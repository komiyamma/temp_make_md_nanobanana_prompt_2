# 第16章：配送係（Relay）の実装：Worker/BackgroundService 🧑‍💻🔧

---

## 1. 今日つくるものの完成イメージ 🗺️📦🚚

**配送係 Relay** は、ずーっと動き続けて👇を繰り返す“小さな常駐アプリ”です✨

1. Outbox テーブルを見に行く 👀
2. 未送信（Pending）を見つけたら、まとめて取り出す 📦📦
3. 送信する（HTTP / キュー / 今は仮の送信でOK）📨
4. 送信できたら「送信済み（Sent）」にする ✅
5. 失敗したら「失敗（Failed）」にしてエラー情報を残す 💥

この章では **Worker / BackgroundService を使って、ずっと動くループを安全に作る**のがゴールです💪😊

---

## 2. Worker と BackgroundService ってなに？🤔💡

![Worker Service Icon](./picture/outbox_cs_study_016_worker_service_icon.png)

* **Worker Service**：
  「バックグラウンドで動くアプリ」を作るための“土台”です🧱✨（ログ・DI・設定なども揃ってて便利）([Microsoft Learn][1])

* **BackgroundService**：
  “ずっと動き続ける処理”を書きやすくしたクラスです🏃‍♀️💨
  中心になるのは **ExecuteAsync** というメソッドで、ここが「アプリが動いてる間ずっと生きる」イメージになります。停止時は CancellationToken（キャンセル）で止めます🛑([Microsoft Learn][2])

✅ ポイント：ExecuteAsync の最初で **await できる状態**にしないと、アプリ全体の起動が詰まることがあるよ（重い初期化をベタ書きしない）([Microsoft Learn][2])

---

## 3. プロジェクト作成（Worker Service）🧰✨

## 3.1 Visual Studio で作る 🪟🧩

* 新規作成 → **Worker Service** を選ぶ
  （「Windows Service としてホストする」系のガイドもこの流れです）([Microsoft Learn][3])

## 3.2 コマンドでも作れる ⌨️🐣

```bash
dotnet new worker -n OutboxRelay
cd OutboxRelay
```

💡 2026-02-03 時点では .NET 10 系が現行の LTS で、ダウンロードページ上の最新 SDK は 10.0.2（2026-01-13 リリース）です。([Microsoft][4])
C# も C# 14 が最新として案内されていて、.NET 10 でサポートされています。([Microsoft Learn][5])

---

## 4. Relay に必要な“最小パーツ”🧩📦

![Relay Components](./picture/outbox_cs_study_016_relay_components.png)

この章の実装は、いったんこの3つに分けるとキレイです✨

1. **RelayWorker**：ずっと動くループ担当 ⏱️
2. **OutboxRepository**：Outbox の取得・更新担当 🗄️
3. **Publisher**：送信担当（今は仮でコンソールでもOK）📨

> 送信先を差し替える本格設計（DIP/DI）は次章で育てるよ🌱（第17章）

---

## 5. コア実装：BackgroundService でポーリングループ ⏱️🔁

![Worker Lifecycle](./picture/outbox_cs_study_016_worker_lifecycle.png)

ここが主役です👑
**一定間隔で未送信を取りに行って、送って、状態更新**します！

## 5.1 Program（DI 登録）🧃

```csharp
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

var builder = Host.CreateApplicationBuilder(args);

// Relay の本体
builder.Services.AddHostedService<OutboxRelayWorker>();

// ここに DB や Repository、Publisher を登録していくイメージ
builder.Services.AddSingleton<IOutboxRepository, InMemoryOutboxRepository>(); // まずは仮
builder.Services.AddSingleton<IMessagePublisher, ConsoleMessagePublisher>(); // まずは仮

builder.Logging.AddConsole();

var host = builder.Build();
await host.RunAsync();
```

💡 「CreateApplicationBuilder」を使うと、設定/ログ/DI をまとめて扱えて便利です（Worker の基本形）([Microsoft Learn][1])

---

## 5.2 RelayWorker 本体 🧑‍💻🔧

![Cancellation Token](./picture/outbox_cs_study_016_cancellation_token.png)

**ポイントは3つ**だよ👇

* 停止要求（キャンセル）をちゃんと見て止まる 🛑
* ループは「待つ」ことで CPU を燃やさない🔥→❌
* 例外を握りつぶさずログに残す🧾

```csharp
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

public sealed class OutboxRelayWorker : BackgroundService
{
    private readonly ILogger<OutboxRelayWorker> _logger;
    private readonly IOutboxRepository _repo;
    private readonly IMessagePublisher _publisher;

    public OutboxRelayWorker(
        ILogger<OutboxRelayWorker> logger,
        IOutboxRepository repo,
        IMessagePublisher publisher)
    {
        _logger = logger;
        _repo = repo;
        _publisher = publisher;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        // ここで“すぐ await”できる形にするのが大事✨
        // （重い初期化をここでブロックしない）:contentReference[oaicite:7]{index=7}

        _logger.LogInformation("Relay started 🚚");

        // ポーリング間隔（最初は短めで動作確認しやすく）
        var interval = TimeSpan.FromSeconds(2);
        using var timer = new PeriodicTimer(interval);

        try
        {
            while (await timer.WaitForNextTickAsync(stoppingToken))
            {
                await ProcessOnceAsync(stoppingToken);
            }
        }
        catch (OperationCanceledException)
        {
            // 正常停止ルート（Ctrl+C やサービス停止）
            _logger.LogInformation("Relay stopping 🛑");
        }
        catch (Exception ex)
        {
            // 落ちた理由は必ずログに！
            _logger.LogError(ex, "Relay crashed 💥");
            throw; // 監視/再起動に気付かせるため、基本は再throw推奨
        }
        finally
        {
            _logger.LogInformation("Relay stopped ✅");
        }
    }

    private async Task ProcessOnceAsync(CancellationToken ct)
    {
        // 1回で扱う件数（バッチサイズ）
        const int batchSize = 20;

        var messages = await _repo.DequeuePendingAsync(batchSize, ct);

        if (messages.Count == 0)
        {
            _logger.LogDebug("No pending messages 😴");
            return;
        }

        _logger.LogInformation("Picked {Count} messages 📦", messages.Count);

        foreach (var msg in messages)
        {
            ct.ThrowIfCancellationRequested();

            try
            {
                await _publisher.PublishAsync(msg, ct);
                await _repo.MarkSentAsync(msg.Id, ct);

                _logger.LogInformation("Sent ✅ OutboxId={Id}", msg.Id);
            }
            catch (Exception ex)
            {
                await _repo.MarkFailedAsync(msg.Id, ex.Message, ct);
                _logger.LogWarning(ex, "Failed ❌ OutboxId={Id}", msg.Id);
            }
        }
    }
}
```

✅ 「ExecuteAsync はサービスの生存期間そのもの」って考えると理解しやすいよ〜！([Microsoft Learn][2])

---

## 6. 仮実装：Repository と Publisher（まず動かす用）🏃‍♀️💨

「章16は常駐処理の作り方が主役」なので、まずは **DBなしでも動く**仮実装を置いちゃいます😊
（DB版は 7 で“必須の考え方”だけ押さえるよ📌）

## 6.1 Outbox メッセージモデル 🧾

```csharp
public sealed record OutboxMessage(
    Guid Id,
    string Type,
    string Payload,
    DateTimeOffset OccurredAtUtc);
```

## 6.2 送信（今はコンソール）🖥️📨

```csharp
public interface IMessagePublisher
{
    Task PublishAsync(OutboxMessage message, CancellationToken ct);
}

public sealed class ConsoleMessagePublisher : IMessagePublisher
{
    public Task PublishAsync(OutboxMessage message, CancellationToken ct)
    {
        Console.WriteLine($"📨 PUBLISH Type={message.Type} Id={message.Id} Payload={message.Payload}");
        return Task.CompletedTask;
    }
}
```

## 6.3 Outbox（今はメモリ）📦

```csharp
public interface IOutboxRepository
{
    Task<IReadOnlyList<OutboxMessage>> DequeuePendingAsync(int batchSize, CancellationToken ct);
    Task MarkSentAsync(Guid id, CancellationToken ct);
    Task MarkFailedAsync(Guid id, string error, CancellationToken ct);
}

public sealed class InMemoryOutboxRepository : IOutboxRepository
{
    private readonly object _lock = new();
    private readonly Queue<OutboxMessage> _pending = new();

    public InMemoryOutboxRepository()
    {
        // 動作確認用にダミー投入✨
        _pending.Enqueue(new OutboxMessage(Guid.NewGuid(), "OrderCreated.v1", """{"orderId":123}""", DateTimeOffset.UtcNow));
        _pending.Enqueue(new OutboxMessage(Guid.NewGuid(), "OrderCreated.v1", """{"orderId":124}""", DateTimeOffset.UtcNow));
    }

    public Task<IReadOnlyList<OutboxMessage>> DequeuePendingAsync(int batchSize, CancellationToken ct)
    {
        var list = new List<OutboxMessage>(batchSize);
        lock (_lock)
        {
            while (list.Count < batchSize && _pending.Count > 0)
                list.Add(_pending.Dequeue());
        }
        return Task.FromResult<IReadOnlyList<OutboxMessage>>(list);
    }

    public Task MarkSentAsync(Guid id, CancellationToken ct) => Task.CompletedTask;
    public Task MarkFailedAsync(Guid id, string error, CancellationToken ct) => Task.CompletedTask;
}
```

ここまでで「動く Relay の骨格」が完成🎉
次は DB で動かすときの“超重要ポイント”に行くよ〜！🔑✨

---

## 7. DB 版にするときの最重要ポイント：取り出しは“取り合い”になる 🥊📦

DB の Outbox を複数の Relay が見に行くと、こういう事故が起きます👇😱

* Relay A が「未送信」を読む 👀
* Relay B も同じ行を「未送信」で読む 👀
* **同じメッセージを2回送る**（重複送信）👯📨📨

だから DB 版では、未送信を読むだけじゃなくて、**「自分が担当するよ！」って確保（Claim）する**仕組みが必要です🔒✨

よくある方法（初心者向けの順）👇

1. **二重起動しない運用**（まずはこれ）🧯
2. **同一マシンでの二重起動を防ぐ**（Mutex）🧷
3. **DBで行を確保する**（Status を InProgress にする等）🧱

この章では 2 を“すぐ使える形”で入れちゃおう😊

---

## 8. 二重起動が起きると何が困る？どう防ぐ？👯❌

## 8.1 困ること 😵‍💫

* **二重送信**（同じ通知が2回飛ぶ）📨📨
* **処理順の崩れ**（同時に触ると順番がグチャグチャ）🌀
* **DB負荷が増える**（無駄にポーリングが倍）🔥

## 8.2 同一 PC 内だけでも止めたい！→ Global Mutex 🧷🪟

![Mutex Guard](./picture/outbox_cs_study_016_mutex_guard.png)

Program の最初にこれを入れると、**同じアプリを2回起動した瞬間に止められます**👍

```csharp
using System.Threading;

const string mutexName = @"Global\OutboxRelaySingleton";
using var mutex = new Mutex(initiallyOwned: true, name: mutexName, out bool createdNew);

if (!createdNew)
{
    Console.WriteLine("⚠️ すでに起動中なので終了します（多重起動防止）");
    return;
}
```

💡 これは「同じ PC の中だけ」の対策です！
サーバーが2台以上になったら DB 側の Claim が必要になるよ（ここは後半の章で強化していこうね）🌱✨

---

## 9. Windows サービスとして動かしたいとき 🚀🪟

Worker は **Windows Service として動かす**のも王道です✨
そのときは拡張パッケージを入れて、ホストに「Windows Service モード」を教えます。([Microsoft Learn][6])

## 9.1 パッケージ追加 📦

```bash
dotnet package add Microsoft.Extensions.Hosting.WindowsServices
```

## 9.2 ホスト側に設定を追加 🧩

（Host.CreateDefaultBuilder を使う書き方の例がよく載っています）

```csharp
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;

IHost host = Host.CreateDefaultBuilder(args)
    .ConfigureServices(services =>
    {
        services.AddHostedService<OutboxRelayWorker>();
    })
    .UseWindowsService(options =>
    {
        options.ServiceName = "OutboxRelay";
    })
    .Build();

await host.RunAsync();
```

✅ 「Worker Service を Windows Service としてホストする」流れ自体は公式ドキュメントにもまとまってます。([Microsoft Learn][6])

---

## 10. 動作確認（デバッグ超かんたん）🧪🎮

## 10.1 まずはコンソールで実行 ▶️

![Console Log View](./picture/outbox_cs_study_016_console_log_view.png)

* Visual Studio の実行（▶）
* もしくは👇

```bash
dotnet run
```

ログにこんな感じが出たらOK✨

* Relay started 🚚
* Picked 2 messages 📦
* Sent ✅ OutboxId=...

## 10.2 止め方 🛑

* コンソールなら Ctrl + C
* サービスなら停止操作（Stop）

キャンセルを受けて、キレイに止まるのが理想です😊([Microsoft Learn][2])

---

## 11. Copilot / Codex に頼むときの“良い指示”例 🤖📝✨

「丸投げ」より、こう頼むと強いよ👇

* 「BackgroundService で PeriodicTimer を使って2秒ごとに処理する Worker を作って。停止は CancellationToken で正しく止めて」
* 「例外はログに出して、OperationCanceledException は正常停止として扱って」
* 「バッチサイズ、待機間隔は定数にして調整しやすくして」

そして最後はここだけ人間がチェック✅

* ループがキャンセルで止まる？🛑
* 待機がちゃんと await されてる？（CPU燃やしてない？）🔥❌
* 例外が握りつぶされてない？💥
* 二重起動の危険は把握できてる？👯

---

## 12. この章のまとめ 🧡📌

* Relay は **ずっと動く配送係**🚚
* Worker / BackgroundService で **安全な常駐ループ**が作れる⏱️🔁([Microsoft Learn][2])
* 停止は CancellationToken を使って **ちゃんと止まる**ようにする🛑([Microsoft Learn][7])
* 二重起動は **重複送信**につながるので、まずは Mutex で守る🧷
* Windows Service 化も王道（運用しやすい）🪟✨([Microsoft Learn][6])

[1]: https://learn.microsoft.com/en-us/dotnet/core/extensions/workers?utm_source=chatgpt.com "Worker Services - .NET"
[2]: https://learn.microsoft.com/en-us/aspnet/core/fundamentals/host/hosted-services?view=aspnetcore-10.0&utm_source=chatgpt.com "Background tasks with hosted services in ASP.NET Core"
[3]: https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/windows-service?view=aspnetcore-10.0&utm_source=chatgpt.com "Host ASP.NET Core in a Windows Service"
[4]: https://dotnet.microsoft.com/en-US/download/dotnet/10.0?utm_source=chatgpt.com "Download .NET 10.0 (Linux, macOS, and Windows) | .NET"
[5]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14?utm_source=chatgpt.com "What's new in C# 14"
[6]: https://learn.microsoft.com/en-us/dotnet/core/extensions/windows-service?utm_source=chatgpt.com "Create Windows Service using BackgroundService - .NET"
[7]: https://learn.microsoft.com/ja-jp/dotnet/api/microsoft.extensions.hosting.backgroundservice.executeasync?view=net-8.0&utm_source=chatgpt.com "BackgroundService.ExecuteAsync(CancellationToken) ..."
