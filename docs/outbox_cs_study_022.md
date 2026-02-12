# 第22章：観測＆テスト＆ミニ演習まとめ（ここで完成！）📈🧪🏁

---

#### 0) 今日のゴール 🎯✨

この章が終わったら、あなたはこうなります👇💕

* Outbox が **詰まってないか**、**壊れてないか** を数字とログで見張れる👀📊
* 「テストがあるから安心！」って言える最低ラインが作れる🧪✅
* **注文作成 → Outbox → Relay → 送信 → 受け手の冪等** を、ミニ演習で最後まで通せる🛒📦🚚📩✅

---

## 1) まず「観測（オブザーバビリティ）」って何？👀🔭

アプリを動かすときは、「今どうなってる？」を見える化しないと、事故が起きても気づけません😱💥
Microsoft の Learn でも、観測は **ログ・メトリック・分散トレース** の3本柱で説明されています。([Microsoft Learn][1])

* **ログ**：何が起きたか（個々の出来事）🧾
* **メトリック**：どれくらい起きてるか（数・割合・分布）📈
* **分散トレース**：1つの処理がどこで時間を使ったか（つながり）🧵

.NET では、だいたいこの3つを次のAPIで扱えます👇（超重要✨）

* ログ：ILogger
* メトリック：Meter（System.Diagnostics.Metrics）
* トレース：ActivitySource / Activity（System.Diagnostics）([Microsoft Learn][1])

---

## 2) Outbox で「まず見るべき」メトリック一覧 📊👀✨

![Observability Dashboard](./picture/outbox_cs_study_022_observability_dashboard.png)

Outbox は **“配送待ちの箱”** なので、最初は「箱の健康診断」からやればOKです🩺📦

### A. 滞留（つまってない？）系 🧱⏳

* **未送信数（Pending件数）**：多いほど詰まり👀
* **最古の未送信の滞留時間**：古いほどヤバい⏰😱
* **送信待ちの増加スピード**：急増は障害の匂い💨

### B. 送信（動いてる？）系 🚚📩

* **送信成功数 / 分** ✅
* **送信失敗数 / 分** ❌
* **失敗率（失敗 / 試行）** 📉

### C. リトライ（苦しんでない？）系 🔁🧯

* **RetryCount の分布**（0が多いのが健康💚）
* **最大 RetryCount**（突出があると毒メッセージ候補☠️）
* **Dead Letter 行き件数**（隔離が増えると要調査🔍）

### D. 冪等（重複が来てる？）系 🧷

* **重複として破棄した件数**（受け手の Inbox 側）📥🚫

  * “最低1回送る”だと重複は起こり得るので、ここも見張ると安心です🙂✅

---

## 3) まずは SQL で「目視できる観測」を作ろう 👀🧾

最初からダッシュボードがなくても大丈夫！
まずは DB を見れば、Outbox の状態が全部わかります💕

#### 未送信数（Pending 件数）📦

```sql
SELECT COUNT(*) AS PendingCount
FROM Outbox
WHERE Status = 'Pending';
```

#### 最古の滞留（何分止まってる？）⏳

（SQL Server 例）

```sql
SELECT TOP 1
  DATEDIFF(SECOND, OccurredAt, SYSUTCDATETIME()) AS OldestPendingAgeSec,
  Id, Type, OccurredAt
FROM Outbox
WHERE Status = 'Pending'
ORDER BY OccurredAt ASC;
```

#### 失敗の上位（LastError で見る）💥

```sql
SELECT TOP 20
  Id, Type, RetryCount, LastError, UpdatedAt
FROM Outbox
WHERE Status = 'Failed'
ORDER BY UpdatedAt DESC;
```

✅ ここまでできたら「Outbox が今どうか」を即答できます👏✨

---

## 4) ログ：最低限ここだけ押さえよう 🧾🧵✨

ログは「後から事件を再現するための証拠」🕵️‍♀️🔍
Outbox では、最低でもこのキーをログに入れると強いです💪

### ログに入れるキー（必須級）✅

* **OutboxId**（超重要👑）
* **MessageType**（何のイベント？）
* **Attempt**（何回目の送信？）
* **Result**（Sent / Failed / DeadLetter）
* **LastError（例外要約）**
* **CorrelationId / TraceId**（つなげる糸🧵）

### 例：構造化ログ（ILogger）🧾

```csharp
logger.LogInformation(
    "Outbox send attempt. OutboxId={OutboxId} Type={Type} Attempt={Attempt}",
    outboxId, messageType, attempt);

try
{
    await publisher.PublishAsync(message);
    logger.LogInformation(
        "Outbox sent. OutboxId={OutboxId} Type={Type}",
        outboxId, messageType);
}
catch (Exception ex)
{
    logger.LogError(ex,
        "Outbox send failed. OutboxId={OutboxId} Type={Type} Attempt={Attempt}",
        outboxId, messageType, attempt);
    throw;
}
```

💡ポイント：文章で書くより「キー＝値」で残すのが超大事です🧡
（後で検索しやすいし、AIに要約させる時も強い🤖✨）

---

## 5) メトリック：.NET + OpenTelemetry で最短ルート 📈✨

OpenTelemetry は「ログ・メトリック・トレース」をまとめて扱う標準で、.NET でも公式に紹介されています。([Microsoft Learn][1])
さらに、主要な NuGet パッケージ（Console / OTLP / Prometheus など）も整理されてます。([Microsoft Learn][1])

### 最小の考え方（初心者版）🍼

* Relay がループするたびに

  1. 未送信数を数える
  2. 失敗/成功をカウントする
  3. 送信時間を測る
     …これだけで “運用できるOutbox” になります📦💕

### 例：Outbox用メーター（超ミニ）📈

```csharp
using System.Diagnostics.Metrics;

public static class OutboxMetrics
{
    private static readonly Meter Meter = new("OutboxApp.Outbox", "1.0.0");

    public static readonly Counter<long> PublishAttempt =
        Meter.CreateCounter<long>("outbox.publish.attempt");

    public static readonly Counter<long> PublishSuccess =
        Meter.CreateCounter<long>("outbox.publish.success");

    public static readonly Counter<long> PublishFailure =
        Meter.CreateCounter<long>("outbox.publish.failure");

    public static readonly Histogram<double> PublishDurationMs =
        Meter.CreateHistogram<double>("outbox.publish.duration_ms");

    private static long _pendingCount;
    private static double _oldestPendingAgeSec;

    public static readonly ObservableGauge<long> PendingCount =
        Meter.CreateObservableGauge<long>("outbox.pending.count", () => _pendingCount);

    public static readonly ObservableGauge<double> OldestPendingAgeSec =
        Meter.CreateObservableGauge<double>("outbox.pending.oldest_age_sec", () => _oldestPendingAgeSec);

    public static void SetBacklog(long pendingCount, double oldestAgeSec)
    {
        _pendingCount = pendingCount;
        _oldestPendingAgeSec = oldestAgeSec;
    }
}
```

Relay の中でこう呼ぶだけ👇

```csharp
OutboxMetrics.SetBacklog(pendingCount, oldestAgeSec);

var tags = new KeyValuePair<string, object?>("type", messageType);
OutboxMetrics.PublishAttempt.Add(1, tags);

var sw = Stopwatch.StartNew();
try
{
    await publisher.PublishAsync(message);
    OutboxMetrics.PublishSuccess.Add(1, tags);
}
catch
{
    OutboxMetrics.PublishFailure.Add(1, tags);
    throw;
}
finally
{
    OutboxMetrics.PublishDurationMs.Record(sw.Elapsed.TotalMilliseconds, tags);
}
```

---

## 6) トレース：1つの注文が「どこで止まったか」を追う 🧵🕵️‍♀️

分散トレースは「この注文、どこで時間食ってる？」を一本の糸で追える仕組みです🧵
.NET では ActivitySource / Activity を使って記録できます。([Microsoft Learn][1])

### まずは “点” でOK（3点打てば十分）📌📌📌

* 注文作成（DB + Outbox）🛒
* Relay が取り出した📦
* 送信した📩

```csharp
using System.Diagnostics;

public static class OutboxTracing
{
    public static readonly ActivitySource ActivitySource = new("OutboxApp");
}

// 注文作成側
using var act = OutboxTracing.ActivitySource.StartActivity("orders.create");
act?.SetTag("order.id", orderId);
act?.SetTag("outbox.id", outboxId);
```

💡発展：送信時に「traceparent」をヘッダに載せると、受け手まで糸がつながって最高です🧵✨
（ここは“できたら強い”枠🙂）

---

## 7) 自動インストルメンテーション（コードいじらず観測）🤖⚡

「とりあえず HTTP / DB の観測を早く入れたい！」なら、OpenTelemetry の **.NET 自動計測（zero-code / automatic instrumentation）** という選択肢もあります。([OpenTelemetry][2])
ただし Outbox 固有メトリック（未送信数とか）は **自前で追加**が必要になりやすいです📦🫶

---

## 8) テスト戦略：Outboxは “3段階” で固める 🧪🧱✨

### ① 単体テスト（Unit）🧪

狙い：**ロジックの正しさ**を高速に確認🏃‍♀️💨

* Outbox レコード生成が正しい（Type / Payload / Version）
* Payload の JSON が期待通り（余計な情報が入ってない）
* 状態遷移が正しい（Pending → Sent / Failed）
* RetryCount の増え方が正しい

例（雰囲気）👇

```csharp
[Fact]
public void CreateOutboxRecord_ShouldContainMinimalPayload()
{
    var record = OutboxRecord.CreateOrderCreated(orderId: 123, customerId: 55);

    record.Type.Should().Be("OrderCreated.v1");
    record.Payload.Should().Contain("\"orderId\":123");
    record.Payload.Should().NotContain("password");
}
```

### ② 統合テスト（Integration）🔒🧪

狙い：**同一トランザクションで2つ書けてる**ことの証明👑

チェックすること👇

* Orders に1件入ったら、Outbox にも1件入ってる ✅
* 途中で例外が起きたら **両方とも入ってない**（ロールバック）✅

例（イメージ）👇

```csharp
[Fact]
public async Task CreateOrder_ShouldInsert_Order_And_Outbox_InSameTransaction()
{
    await using var db = await TestDb.CreateAsync(); // LocalDBでもSQLiteでもOK（教材ではどっちでも！）
    var service = new OrderService(db);

    var orderId = await service.CreateOrderAsync(...);

    (await db.Orders.CountAsync(o => o.Id == orderId)).Should().Be(1);
    (await db.Outbox.CountAsync(x => x.Type == "OrderCreated.v1")).Should().Be(1);
}

[Fact]
public async Task CreateOrder_WhenFail_ShouldRollbackBoth()
{
    await using var db = await TestDb.CreateAsync();
    var service = new OrderService(db);

    await Assert.ThrowsAsync<Exception>(() => service.CreateOrderAsync(failAfterOutbox: true));

    (await db.Orders.CountAsync()).Should().Be(0);
    (await db.Outbox.CountAsync()).Should().Be(0);
}
```

### ③ 失敗注入テスト（Fault Injection）🎭🧯

狙い：**送信失敗 → リトライ → 成功** の一連を安全に再現！

* publisher を「最初の2回だけ失敗する偽物」にする
* Relay を1件処理させて、RetryCount とステータスを検証する
* さらに「恒久失敗」も作って Dead Letter へ☠️➡️📦

---

## 9) 最終ミニ演習：全部つなげて “完成” させよう 🛒📦🚚📩✅

ここからは、**手順どおりにやれば必ず通る**流れにします🙆‍♀️💕

### 構成（最小）🧩

* 注文作成アプリ（Orders + Outbox に書く）🛒🧾
* Relay（未送信をポーリングして送る）🚚
* 受け手（Inboxで重複排除して処理）📥✅

送信先は「偽ブローカー（コンソール出力）」でOKです🖥️✨
（本物のキューは後で差し替えられる設計にしてあるから安心🔌）

---

### ステップ1：注文を1件作る 🛒

期待結果👇

* Orders に1件 ✅
* Outbox に Pending が1件 ✅
* ログに OutboxId が出る ✅

確認 SQL 👇

```sql
SELECT TOP 5 * FROM Outbox ORDER BY OccurredAt DESC;
```

---

### ステップ2：Relay を起動して配送する 🚚📩

期待結果👇

* Pending が減る（0へ）📉
* Sent が増える ✅
* 送信成功カウンタが増える 📈

確認 SQL 👇

```sql
SELECT Status, COUNT(*) FROM Outbox GROUP BY Status;
```

---

### ステップ3：受け手で冪等（2回来ても1回扱い）🧷✅

やること👇

* 同じ OutboxId を **2回** 処理してみる
* Inbox 的テーブル（処理済み）で弾けることを確認📥🚫

期待結果👇

* “処理済み” 判定で2回目はスキップ✅
* 重複破棄カウンタが増える（任意）📈

---

### ステップ4：失敗注入（送信失敗→リトライ→成功）🎭🔁✅

やること👇

* publisher を「最初の2回だけ例外」にする
* Relay を動かす

期待結果👇

* Failed が一時的に増えるが、最終的に Sent になる✅
* RetryCount が 2 以上になってる✅
* ログに Attempt=1,2,3… が出る🧾

---

### ステップ5：毒メッセージ（恒久失敗→隔離）☠️➡️📦

やること👇

* 受け手が絶対処理できない Payload（Version違いなど）を作る
* Relay（または受け手）で恒久失敗扱いにする

期待結果👇

* Dead Letter 相当の隔離に入る✅
* LastError に理由が残る✅
* “未送信が永遠に詰まる” 状態を防げる✅

---

## 10) AI（Copilot/Codex）に頼むならココが安全 🤖✅🧡

AIは便利だけど、Outboxは **境界を間違えると事故る**ので、頼みどころを分けます💡

### AIに頼んで良い（おすすめ）✨

* メトリック名の候補出し（命名）📛
* テストケースの洗い出し（成功/失敗/境界）🧪
* 例外メッセージの整理（ユーザー向け/運用向け）🧾
* SQLの観測クエリの雛形🧮

### 人が最終確定する（絶対）👀👑

* トランザクション範囲（どこからどこまで一括？）🔒
* リトライ回数・バックオフ（やりすぎると地獄⏳）
* 冪等性のキー（何で一意にする？）🪪

---

## 11) 仕上げチェックリスト ✅✅✅（これが通れば合格🎓）

### 観測（見える化）📈

* [ ] Pending件数がすぐ取れる
* [ ] 最古滞留時間がすぐ取れる
* [ ] 失敗率が見える
* [ ] ログに OutboxId / Type / Attempt / LastError が出る

### テスト🧪

* [ ] Unit：Outbox生成が正しい
* [ ] Integration：Orders + Outbox が同一トランザクション
* [ ] Fault：失敗→リトライ→成功 が再現できる
* [ ] 冪等：2回届いても1回扱い

### ミニ演習🏁

* [ ] 注文作成 → Outbox → Relay → 送信 → 受け手冪等 が通った✨

---

## 12) “最新前提”メモ（2026時点）🗓️✨

* **C# 14 は .NET 10 上でサポート**され、**Visual Studio 2026 に .NET 10 SDK が含まれる**と案内されています。([Microsoft Learn][3])
* **.NET 10 は 2025-11-11 リリース**として公開されています。([Microsoft][4])
* Visual Studio 2026 の情報も公開されています。([Microsoft Learn][5])

---

### 🎉 これで Outbox の「実装」だけじゃなく「運用できる形」まで完成！📦🚚📈🧪🏁

[1]: https://learn.microsoft.com/ja-jp/dotnet/core/diagnostics/observability-with-otel "OpenTelemetry を使用した .NET の監視 - .NET | Microsoft Learn"
[2]: https://opentelemetry.io/docs/zero-code/dotnet/?utm_source=chatgpt.com "NET zero-code instrumentation"
[3]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14?utm_source=chatgpt.com "What's new in C# 14"
[4]: https://dotnet.microsoft.com/en-US/download/dotnet/10.0?utm_source=chatgpt.com "Download .NET 10.0 (Linux, macOS, and Windows) | .NET"
[5]: https://learn.microsoft.com/ja-jp/visualstudio/releases/2026/release-notes?utm_source=chatgpt.com "Visual Studio 2026 リリース ノート"
