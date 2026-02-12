# 第16章：リトライ戦略（いつ再試行？いつ補償？いつ止める？）⏳🧯

## この章のゴール🎯✨

* 「失敗したから、とりあえずリトライ！」を卒業する😇🍼
* 失敗を **分類** して、**Retry / Compensate / Halt** を決められるようになる🧠📋
* Sagaでありがちな **リトライ地獄**（無限ループ・二重実行・障害拡大）を避けられる🛑🔥
* C#で「方針どおり」に動くリトライを実装できるようになる🧑‍💻✨

---

# 1) まず結論：リトライは“万能薬”じゃない💊🙅‍♀️

リトライは便利だけど、使い方を間違えると…👇

* 障害中の相手をさらに殴り続けて **障害を悪化** させる😵‍💫💥
* すでに成功してたのに、もう一回やって **二重課金** みたいな事故になる😱💳
* Saga全体が前に進めず、永遠にリトライして **誰も助けられない** 状態になる🌀🧟‍♂️

だから、Sagaではこう考えるのが基本だよ👇😊
**「リトライして良い失敗」だけリトライする** ✅
**「補償すべき失敗」は補償する** 🧾🔁
**「止めて人間に渡すべき失敗」は止める** 🛑👩‍💼

---

# 2) 失敗を“3種類”に分けよう📦🔍

最初にここを分けるだけで、判断がめっちゃラクになるよ😊✨

| 失敗の種類                     | 例                                      | 基本アクション                  |
| ------------------------- | -------------------------------------- | ------------------------ |
| ① 一時的なインフラ失敗（Transient）⚡  | ネットワーク瞬断、タイムアウト、相手が一瞬落ちてた、HTTP 503/504 | **Retry** が効くことが多い🔁     |
| ② 恒久的な失敗（Permanent）🧱     | 入力ミス、権限なし、在庫ゼロ確定、仕様違反                  | **Retryしても無駄** → 早めに判断🧠 |
| ③ 結果が不明（Unknown outcome）❓ | タイムアウトしたけど相手側で処理されたか不明、レスポンス消えた        | **“再実行して安全？”** を最優先🔑🛡️ |

> リトライの前提として「冪等性」や「冪等キー」が超重要だったよね（第9〜10章）🔑✨
> これが弱いと、リトライは“事故製造機”になりがち😱

---

# 3) 判断フロー（これだけ覚えればOK）🧭✅

### リトライ判断の意思決定 🧭✅
```mermaid
flowchart TD
    Start([エラー発生]) --> Q_Safe{リトライして安全?<br/>(冪等 / 照会可能)}
    Q_Safe -- "NO (危険)" --> Halt[停止 / 人間介入 🛑]
    Q_Safe -- "YES" --> Q_Type{エラーの種類は?}
    
    Q_Type -- "一時的 / インフラ" --> Q_Limit{上限超えた?}
    Q_Type -- "恒久的 / 業務" --> Comp[補償へ 🧾]
    Q_Type -- "不明 (Timeoutなど)" --> Q_Safe
    
    Q_Limit -- "NO" --> Retry[リトライ実行 🔁]
    Q_Limit -- "YES" --> Comp
```

---

* **安全（冪等）**：同じ要求をもう一回やっても結果が同じになる😊

  * 例：`POST /reserve-inventory` でも **冪等キー** で「同じ予約」扱いにできるならOK
* **危険（非冪等）**：やるたび結果が増える😱

  * 例：冪等キーなしの「課金実行」「ポイント付与」

👉 **非冪等なら**：まず冪等化（冪等キー / 状態チェック / “すでに処理済み？”照会）を考える🔍✨

---

## ステップB：失敗はTransient？Permanent？Unknown？🧠

* **Transientっぽい**：タイムアウト、503、接続エラー、429（混雑）など → リトライ候補🔁
* **Permanentっぽい**：仕様違反、在庫ゼロ確定、支払い拒否確定 → 補償 or 失敗確定🧾
* **Unknown**：タイムアウト等で「成功したか不明」 → **同じ操作の再実行は慎重に**❗

---

## ステップC：リトライ予算（Retry Budget）を超えた？💰⏳

Sagaは“いつか成功するまで”粘ると運用崩壊しがち🫠

* 回数上限（例：最大3〜5回）🔁
* 時間上限（例：合計30秒〜数分）⏱️
* 全体の締め切り（Saga全体のタイムアウト）⛔

超えたら👇

* **Compensate（補償）** へ🧾🔁
* もしくは **Halt（停止して人間へ）** 🛑👩‍💼

---

# 4) “いつ補償？いつ止める？”の基準🧾🛑

## 補償（Compensate）に行く条件🧾🔁

* そのステップが **永久失敗**（例：在庫ゼロ確定）だった😇
* **上限までリトライしてもダメ** だった😵
* Sagaが途中まで成功していて、これ以上進めない（例：決済成功→在庫確保失敗）💳➡️📦❌
* 相手システムに迷惑をかけそう（混雑・障害中）で、これ以上のRetryが危険⚠️

## 停止（Halt）に行く条件🛑👩‍💼

* **結果不明が解消できない**（照会もできない、ログも足りない）❓😱
* 補償も失敗し続ける（補償ループ）🌀
* データが壊れてる、想定外の例外、バグ臭い🧨🐛
* “ここから先は人間の判断が必要”な業務（高額取引など）💰🧑‍⚖️

---

# 5) バックオフは「指数 + ゆらぎ」が基本✨🎢

リトライ間隔を一定にすると、みんなが同時に突撃して地獄になる（リトライ嵐）😵‍💫🌪️
だからよく使うのが👇

* **指数バックオフ**：`200ms → 400ms → 800ms → ...` ⏳
* **ジッター（ゆらぎ）**：ちょっとランダムにずらす🎲
* **429 / 503 のときは相手の指示（Retry-After）を尊重** 🙏📩

---

# 6) 方針表テンプレ（Retry / Compensate / Halt）📋✨

まずは“表”にすると、設計が一気に安定するよ😊🌸

| ステップ              | 失敗例         |     Retry？ |         Compensate？ |        Halt？ |
| ----------------- | ----------- | ---------: | ------------------: | -----------: |
| 決済（Payment）💳     | タイムアウトで結果不明 | △（照会できるなら） | △（照会で成功なら次へ、失敗なら補償） | ○（照会不能が続くなら） |
| 在庫確保（Inventory）📦 | 503/接続失敗    |          ○ |        △（上限超えたら補償へ） |            △ |
| 配送手配（Shipping）🚚  | 仕様エラー（住所不正） |          ✖ |        ○（決済済なら返金など） |    △（例外的ケース） |

ポイントはこれ👇😊

* **“結果不明”は特別扱い**（照会して確定させる）🔍❗
* **リトライ上限超えたら次の手**（補償 or 停止）⛔

---

# 7) C#実装①：HTTP呼び出し側に“標準回復”を入れる🧑‍💻🛡️

HTTPは一時的な失敗が起きやすいので、.NETでは回復性（Resilience）を組み込みやすくなってるよ😊
`Microsoft.Extensions.Http.Resilience` は Pollyベースで、リトライやタイムアウト等をまとめて扱える（標準ハンドラあり）📦✨ ([nuget.org][1])

> ちなみに昔よく見た `Microsoft.Extensions.Http.Polly` は非推奨扱いになってるよ⚠️（新しい方を使おう） ([Microsoft Learn][2])

```csharp
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var builder = Host.CreateApplicationBuilder(args);

// 例：Payment API を叩く HttpClient に回復性ハンドラを追加
builder.Services
    .AddHttpClient<PaymentClient>(client =>
    {
        client.BaseAddress = new Uri("https://payment.example/");
        client.Timeout = TimeSpan.FromSeconds(10); // これは“最後の砦”として短め推奨⏱️
    })
    .AddStandardResilienceHandler(); // 標準の回復性（リトライ等）🛡️✨

var app = builder.Build();
await app.RunAsync();

public sealed class PaymentClient
{
    private readonly HttpClient _http;
    public PaymentClient(HttpClient http) => _http = http;

    public Task<HttpResponseMessage> ChargeAsync(HttpRequestMessage req, CancellationToken ct)
        => _http.SendAsync(req, ct);
}
```

標準ハンドラの中には、全体タイムアウト・リトライ・レート制限・サーキットブレーカー等の“パイプライン”が含まれる設計になってるよ📦🧱 ([nuget.org][3])
（中身をカスタムしたくなったら `AddResilienceHandler` で自分の戦略を組む感じ😊）

---

# 8) C#実装②：Saga側で「Retry予算 → 補償 → 停止」を制御する🎛️🧾🛑

HTTPクライアント側だけだと、Sagaとしての意思決定（補償/停止）ができないよね😇
だからSagaのオーケストレータ側では、こんな責務を持つのがコツ👇

* 何回失敗した？🔁
* どの種類の失敗？⚡🧱❓
* 予算超えた？💰
* 補償に行く？止める？🧾🛑

Polly系の “パイプライン” 構築は `AddResiliencePipeline` みたいに組めるよ（順序が大事）🧱✨ ([Microsoft Learn][4])

## 例：Sagaステップ実行ヘルパー（考え方が伝わる最小形）😊

```csharp
using System.Net;
using Polly;
using Polly.Retry;

public enum StepDecision { Retry, Compensate, Halt }

public static class SagaRetry
{
    // ざっくり例：HTTPでよくある「一時的」判定
    public static bool IsTransient(HttpStatusCode statusCode)
        => statusCode == HttpStatusCode.TooManyRequests    // 429
        || statusCode == HttpStatusCode.RequestTimeout     // 408
        || (int)statusCode >= 500;                         // 5xx

    public static StepDecision Decide(
        int attempt,
        int maxAttempts,
        bool idempotent,
        bool unknownOutcome,
        bool transient)
    {
        // ① 結果不明 & 非冪等 → まず止める寄り（照会などの別ルート推奨）❗
        if (unknownOutcome && !idempotent)
            return StepDecision.Halt;

        // ② 一時的なら、上限までリトライ🔁
        if (transient && attempt < maxAttempts)
            return StepDecision.Retry;

        // ③ それ以外（永久っぽい / 上限超え）→ 補償へ🧾
        return StepDecision.Compensate;
    }

    public static ResiliencePipeline CreateRetryPipeline(int maxAttempts)
    {
        // Polly v8系のリトライ戦略（最小例）🔁
        return new ResiliencePipelineBuilder()
            .AddRetry(new RetryStrategyOptions
            {
                MaxRetryAttempts = maxAttempts - 1, // “初回 + リトライ回数”の考え方に注意👀
                Delay = TimeSpan.FromMilliseconds(200),
                BackoffType = DelayBackoffType.Exponential,
                UseJitter = true,
                ShouldHandle = new PredicateBuilder()
                    .Handle<TimeoutException>()
                    .Handle<HttpRequestException>()
            })
            .Build();
    }
}
```

ここで大事なのは👇😊

* **「何でも例外ならリトライ」じゃなくて、先に分類してから決める** 🧠
* **非冪等 & 結果不明は危険**（照会で確定させる／止める）🔑❗
* **リトライは上限付き**（上限超えたら補償 or 停止）⛔🧾🛑

---

# 9) よくある事故パターン集（超重要）😱📚

## ① “リトライしたら二重課金した”💳💥

* 原因：非冪等操作をそのままリトライ
* 対策：**冪等キー**、**処理済み照会**、**決済IDの一意制約** など🔑🛡️

## ② “タイムアウト＝失敗”と決めつけて補償したら、実は成功してた😵‍💫

* 原因：結果不明を失敗扱いにした
* 対策：**結果照会API** を用意して「成功/失敗」を確定させる🔍✅

## ③ “障害中に全員がリトライして相手が死んだ”🌪️💀

* 原因：一定間隔リトライ、ジッターなし
* 対策：**指数バックオフ + ジッター**、必要なら遮断（サーキット）🧯🎲

---

# 10) ミニ演習（紙でもOK）📝😊

## 演習①：失敗を分類しよう📦

次を「Transient / Permanent / Unknown」に分類してみてね👇

* (A) `HttpRequestException` が出た
* (B) 住所が必須なのに空だった
* (C) 決済APIがタイムアウトした（成功したか不明）
* (D) 在庫0が返ってきた

## 演習②：方針表を完成させよう📋✨

「注文→決済→在庫→配送」それぞれに対して👇

* リトライ上限は？🔁
* 上限超えたら補償？停止？🧾🛑
* “結果不明”のときはどう確定させる？🔍

---

# 11) AI活用（レビューが強い！）🤖✨

コピペで使える感じにしておくね😊💕

* 「このSagaの各ステップについて、Transient/Permanent/Unknown を分類して、Retry/Compensate/Halt の表を作って」📋🤖
* 「非冪等操作が紛れてないかチェックして。二重実行になりそうな箇所を指摘して」🔑👀🤖
* 「“結果不明”が起きた時の照会フロー（成功確定→次へ / 失敗確定→補償 / 確定不能→停止）を書いて」🔍🧾🛑🤖
* 「リトライ嵐になりそうな設定（間隔・回数・同時実行）を指摘して、改善案を出して」🌪️🧯🤖

---

# 12) 2026年の“いま”押さえておきたい補足📌✨

* .NETは **.NET 10 が最新のLTS**で、2026/01/13時点の最新パッチは **10.0.2** だよ📅✨ ([Microsoft][5])
* 回復性（Resilience）は Pollyベースで、`Microsoft.Extensions.Resilience` / `Microsoft.Extensions.Http.Resilience` が推奨ルートになってるよ🛡️📦 ([Microsoft Learn][2])
* Polly自体も継続的に更新されていて、NuGet上では **Polly 8.6.5** が確認できるよ🔁📚 ([nuget.org][6])

---

## ✅ この章のまとめ（超短く）🌸

* リトライは「一時的な失敗」にだけ効く🔁
* “結果不明”と“非冪等”は特に危険（照会・冪等キー・停止をセットで）❗🔑
* Sagaは **Retry予算 → 補償 → 停止** の順で、運用できる形にする🧾🛑✨

[1]: https://www.nuget.org/packages/Microsoft.Extensions.Http.Resilience/ "
        NuGet Gallery
        \| Microsoft.Extensions.Http.Resilience 10.2.0
    "
[2]: https://learn.microsoft.com/en-us/dotnet/core/resilience/ "Introduction to resilient app development - .NET | Microsoft Learn"
[3]: https://www.nuget.org/packages/Microsoft.Extensions.Http.Resilience/?utm_source=chatgpt.com "Microsoft.Extensions.Http.Resilience 10.2.0 - NuGet"
[4]: https://learn.microsoft.com/ja-jp/dotnet/core/resilience/ "回復性のあるアプリ開発の概要 - .NET | Microsoft Learn"
[5]: https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core ".NET and .NET Core official support policy | .NET"
[6]: https://www.nuget.org/packages/polly/ "
        NuGet Gallery
        \| Polly 8.6.5
    "
