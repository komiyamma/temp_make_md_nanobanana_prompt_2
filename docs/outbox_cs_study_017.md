# 第17章：送信先アダプタ設計（DIP/DIの練習）🔌🧩

## 今日のゴール 🎯✨

* Relay（配送係🚚）の中から「送信の具体処理（HTTP/キュー/何か）」を追い出して、**差し替え可能**にする🙌
* **DIP（依存関係逆転）**と**DI（依存性注入）**を、Outboxの文脈で“体で覚える”💪🧠
* まずは「偽ブローカー（コンソール出力）」で動かし、次に「HTTP送信」に差し替える🔁🌐

---

## 1) まずDIP/DIを“Outbox流”に翻訳する🗺️💡

![DIP Plugin](./picture/outbox_cs_study_017_dip_plugin.png)

## DIPってなに？（超ざっくり）🧁

* **上位（Relayの流れ）**が、**下位（HTTP送信の詳細）**にベタ依存していると、変更がつらい😵‍💫
* そこで「**送信できる**」という**抽象（インターフェース）**に依存させる✂️
* **詳細（HTTP送信など）は後から差し込む**🔌

> 例：コンセント（抽象）があれば、ドライヤー（実装）も充電器（実装）も差し替えられる⚡🔁

## DIってなに？（超ざっくり）🥤

* 「Relayの中で new HttpEventPublisher()」みたいに作らない🙅‍♀️
* 外（Program.csとか）で「これ使ってね！」って渡す（注入）🧃
* .NETの標準DIコンテナで **コンストラクタ注入** が基本形✨

---

## 2) “ポート（インターフェース）”を切る✂️🧩

Outboxから出ていくものを、まずは最小限の形にそろえよう📦✨
（Outboxテーブルの `Type` と `Payload` が主役！）

```csharp
public sealed record OutboxEnvelope(
    Guid OutboxId,
    string Type,
    string PayloadJson,
    DateTimeOffset OccurredAt
);
```

そして、送信口（ポート）を定義👇

```csharp
public interface IEventPublisher
{
    Task PublishAsync(OutboxEnvelope envelope, CancellationToken ct);
}
```

## ポイント📝💖

* Relayは **IEventPublisherしか知らない**（HTTPのことは忘れる）😌
* `OutboxId` は将来「冪等性（重複対策）」で超重要になるので、今から渡すのがコツ🪪✨（次章で本格的にやるよ）

---

## 3) 実装①：偽ブローカー（コンソール出力）🖥️🎭

![Fake Broker Prop](./picture/outbox_cs_study_017_fake_broker_prop.png)

まずは「送ったことにする」実装で、全体を通すのがいちばん早い🏃‍♀️💨

```csharp
using Microsoft.Extensions.Logging;

public sealed class ConsoleEventPublisher : IEventPublisher
{
    private readonly ILogger<ConsoleEventPublisher> _logger;

    public ConsoleEventPublisher(ILogger<ConsoleEventPublisher> logger)
        => _logger = logger;

    public Task PublishAsync(OutboxEnvelope envelope, CancellationToken ct)
    {
        _logger.LogInformation(
            "📤 PUBLISH (FAKE) outboxId={OutboxId} type={Type} occurredAt={OccurredAt}\n{Payload}",
            envelope.OutboxId, envelope.Type, envelope.OccurredAt, envelope.PayloadJson
        );

        return Task.CompletedTask;
    }
}
```

## これで何が嬉しい？🎉

* 送信先が未確定でも、Relayの設計と流れを先に完成できる✅
* 後からHTTPやキューに切り替えても、Relay本体は触らないで済む🛡️

---

## 4) Relayを“抽象にだけ依存”する形にリファクタ🔧🚚

![Relay Blindfolded](./picture/outbox_cs_study_017_relay_blindfolded.png)

Relay（BackgroundService）は、未送信Outboxを取り出して Publish して、送信済みにする…という流れだったはず👀
ここでは「Publishの詳細」を `IEventPublisher` に丸投げするよ🎁

```csharp
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

public interface IOutboxRepository
{
    Task<IReadOnlyList<OutboxEnvelope>> GetPendingAsync(int batchSize, CancellationToken ct);
    Task MarkAsSentAsync(Guid outboxId, CancellationToken ct);
    Task MarkAsFailedAsync(Guid outboxId, string error, CancellationToken ct);
}

public sealed class OutboxRelayWorker : BackgroundService
{
    private readonly IOutboxRepository _repo;
    private readonly IEventPublisher _publisher;
    private readonly ILogger<OutboxRelayWorker> _logger;

    public OutboxRelayWorker(
        IOutboxRepository repo,
        IEventPublisher publisher,
        ILogger<OutboxRelayWorker> logger)
    {
        _repo = repo;
        _publisher = publisher;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        const int batchSize = 50;

        while (!stoppingToken.IsCancellationRequested)
        {
            var pending = await _repo.GetPendingAsync(batchSize, stoppingToken);

            foreach (var msg in pending)
            {
                try
                {
                    await _publisher.PublishAsync(msg, stoppingToken);
                    await _repo.MarkAsSentAsync(msg.OutboxId, stoppingToken);

                    _logger.LogInformation("✅ SENT outboxId={OutboxId}", msg.OutboxId);
                }
                catch (Exception ex)
                {
                    await _repo.MarkAsFailedAsync(msg.OutboxId, ex.Message, stoppingToken);
                    _logger.LogWarning(ex, "⚠️ FAILED outboxId={OutboxId}", msg.OutboxId);
                }
            }

            await Task.Delay(TimeSpan.FromSeconds(2), stoppingToken);
        }
    }
}
```

`BackgroundService` は Hosted Service の基本クラスだよ〜という位置づけ🧱✨ ([Microsoft Learn][1])
（前章の Worker/BackgroundService と同じ世界線！）

---

## 5) DIで差し込む（偽ブローカー版）🧃🔌

![DI Injection Robot](./picture/outbox_cs_study_017_di_injection_robot.png)

Program.cs で「IEventPublisher は ConsoleEventPublisher を使うよ」って登録するだけ✨

```csharp
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var builder = Host.CreateApplicationBuilder(args);

builder.Services.AddHostedService<OutboxRelayWorker>();

// Repository（例：DB実装）も登録しておく
// builder.Services.AddSingleton<IOutboxRepository, SqlOutboxRepository>();

// ✅ 送信先は “偽ブローカー”
builder.Services.AddSingleton<IEventPublisher, ConsoleEventPublisher>();

var app = builder.Build();
await app.RunAsync();
```

## ここがDIのキモ🧠✨

* Relayは `IEventPublisher` を欲しがるだけ
* どの実装を入れるかは Program.cs が決める
* 差し替えが「1行変更」で済む💃

---

## 6) 実装②：HTTP送信に差し替える🌐📨

## 6-1) “HttpClientを雑にnewしない”のが大事🙅‍♀️

![HttpClient Factory](./picture/outbox_cs_study_017_http_client_factory.png)

HTTPは `HttpClient` を毎回 new して捨てると、接続枯渇などの罠にハマりがち😱
なので、.NET標準の `IHttpClientFactory` を使うのが定番✨ ([Microsoft Learn][2])

## 6-2) HTTP Publisher を作る🧩

```csharp
using System.Net.Http.Json;

public sealed class HttpEventPublisher : IEventPublisher
{
    private readonly HttpClient _http;

    public HttpEventPublisher(HttpClient http)
        => _http = http;

    public async Task PublishAsync(OutboxEnvelope envelope, CancellationToken ct)
    {
        // 送信先の契約（とりあえず最小）
        var request = new
        {
            id = envelope.OutboxId,
            type = envelope.Type,
            occurredAt = envelope.OccurredAt,
            payload = envelope.PayloadJson
        };

        var res = await _http.PostAsJsonAsync("/events", request, ct);
        res.EnsureSuccessStatusCode();
    }
}
```

## 6-3) DI登録：AddHttpClientで“差し替え完成”🔁✨

```csharp
builder.Services.AddHttpClient<IEventPublisher, HttpEventPublisher>(client =>
{
    client.BaseAddress = new Uri("https://localhost:5001");
    client.Timeout = TimeSpan.FromSeconds(10);
});
```

`AddHttpClient` は `IHttpClientFactory` を登録して、型指定クライアントなどを作れる仕組みだよ〜という位置づけ🧰✨ ([Microsoft Learn][3])

---

## 7) ローカルで受け口（Receiver）を作って動作確認🧪🏁

「送れたかどうか」が分かると気持ちいいので、最小の受信APIを作ろう📩✨
（Minimal APIでOK！）

```csharp
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapPost("/events", (object body) =>
{
    Console.WriteLine("📥 RECEIVED: " + body);
    return Results.Ok(new { ok = true });
});

app.Run();
```

## 確認のコツ🔍

* Relay側のログに ✅ SENT が出る
* Receiver側に 📥 RECEIVED が出る
* Outboxが “送信済み” になって減っていく📉✨

---

## 8) “差し替えがラク”ってこういうこと💃🔁

![Program Switch](./picture/outbox_cs_study_017_program_switch.png)

## パターンA：開発中は偽ブローカー、本番はHTTP

* 開発：ログで追える🕵️‍♀️
* 本番：HTTP/キューに変える📦➡️🌐

Program.cs のこの1行だけ変わるのが理想👇

* 偽ブローカー：
  `AddSingleton<IEventPublisher, ConsoleEventPublisher>();`
* HTTP：
  `AddHttpClient<IEventPublisher, HttpEventPublisher>(...);`

---

## 9) ミニテスト：RelayがPublishを呼ぶことを確認🧪✅

![Recording Spy](./picture/outbox_cs_study_017_recording_spy.png)

モックが苦手でも大丈夫🙆‍♀️
“記録するだけのPublisher”を作れば簡単！

```csharp
public sealed class RecordingPublisher : IEventPublisher
{
    public List<OutboxEnvelope> Sent { get; } = new();

    public Task PublishAsync(OutboxEnvelope envelope, CancellationToken ct)
    {
        Sent.Add(envelope);
        return Task.CompletedTask;
    }
}
```

テスト（イメージ）：

```csharp
// 擬似Repoが1件返す → RelayがPublishしてSentに入る、みたいな確認をする
// ※ここはプロジェクト構成によって書き方が変わるので「発想」が大事✨
```

## ここでの学び🎓

* 「HTTPが絡むテスト」は難しい → だからまず **ポートで切る**✂️
* Relayは “送信した” という事実だけをテストできる🧠✨

---

## 10) Copilot/Codexに頼むときの“ちょうどいい指示”🤖📝

## インターフェース生成を頼む💡

* 「OutboxEnvelope record と IEventPublisher を作って。OutboxId/Type/PayloadJson/OccurredAt を含めて」

## HTTP版の下書きを頼む🌐

* 「IEventPublisher の Http 実装を作って。HttpClient をコンストラクタ注入して、/events にPOSTして」

## でも人間が必ず見る場所👀🔥

* `EnsureSuccessStatusCode()` の扱い（失敗＝リトライ対象？毒メッセージ？）
* タイムアウトや例外時に「OutboxをFailedにする」方針
* Payloadの作り方（入れすぎない！）

---

## 11) つまずきポイントあるある😵‍💫🧯

## 「RelayがHTTPの詳細を知っちゃってる」問題

* `HttpClient` を Relay に直接注入しない🙅‍♀️
* Relayは `IEventPublisher` だけを握る🤝

## 「HttpClient を毎回 new してる」問題

* `IHttpClientFactory` / `AddHttpClient` を使う✨ ([Microsoft Learn][2])

## 「送れたのに受け側が処理してないかも…」問題

* それが **At-least-once** の入口📬🔁（次章でガッツリ！）

---

## 12) ミニ演習（手を動かすパート）✍️🏃‍♀️

1. `IEventPublisher` と `OutboxEnvelope` を作る🧩
2. `ConsoleEventPublisher` を登録して、Relayが動くのをログで見る🖥️✨
3. `HttpEventPublisher` を作って、受信API（Minimal）に投げる🌐📨
4. Program.cs の登録を切り替えて「差し替えできた！」を体験する🔁🎉
5. RecordingPublisher を使って「Publishが呼ばれてる」ことをテスト発想で確認🧪✅

---

## 参考：この章で使っている“2026時点の土台”🧱✨

* .NET 10 は 2025-11-11 にリリースされ、2026-01-13 時点の最新パッチとして 10.0.2 が案内されているよ📦🆙 ([Microsoft for Developers][4])
* C# 14 は Visual Studio 2026 / .NET 10 SDK で試せる機能として整理されているよ🧠✨ ([Microsoft Learn][5])
* Visual Studio 2026 のリリースノートも公開されているよ🛠️📝 ([Microsoft Learn][6])

[1]: https://learn.microsoft.com/ja-jp/dotnet/api/microsoft.extensions.hosting.backgroundservice?view=net-10.0&utm_source=chatgpt.com "BackgroundService Class (Microsoft.Extensions.Hosting)"
[2]: https://learn.microsoft.com/en-us/dotnet/core/extensions/httpclient-factory?utm_source=chatgpt.com "Use the IHttpClientFactory - .NET"
[3]: https://learn.microsoft.com/en-us/dotnet/api/microsoft.extensions.dependencyinjection.httpclientfactoryservicecollectionextensions.addhttpclient?view=net-10.0-pp&utm_source=chatgpt.com "HttpClientFactoryServiceCollecti..."
[4]: https://devblogs.microsoft.com/dotnet/announcing-dotnet-10/?utm_source=chatgpt.com "Announcing .NET 10"
[5]: https://learn.microsoft.com/ja-jp/dotnet/csharp/whats-new/csharp-14?utm_source=chatgpt.com "C# 14 の新機能"
[6]: https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-notes?utm_source=chatgpt.com "Visual Studio 2026 Release Notes"
