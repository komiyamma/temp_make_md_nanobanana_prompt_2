# 第19章：Outbox実装（テーブル＋送信ワーカー＋重複対策）🔧💾

---

## 19.1 この章のゴール🎯✨

* Outboxを「最低限の形」で実装できるイメージを持つ💪
* 「DB更新は成功したのに、イベント送信だけ失敗…😱」を防ぐ仕組みが作れる
* 送信ワーカー（Dispatcher）と、重複対策（冪等）の“超重要ポイント”がわかる🔁🛡️

---

## 19.2 Outboxって何を解決するの？🤔📦

![Outbox Solving Dual Write](./picture/saga_cs_study_019_solution_concept.png)

Sagaでは、だいたいこんな流れになります👇

1. 注文をDBに保存する🧾
2. 「注文できたよ！」というイベント（例：`OrderCreated`）をメッセージブローカーに送る📨

ここで怖いのが…😵‍💫

* **DB保存は成功**✅
* **イベント送信だけ失敗**❌（ネットワーク・一時障害・ブローカー不調など）

すると、他サービスがイベントを受け取れず、Sagaが進まない／整合性が崩れる事故になります😱

Outboxパターンはこの問題を、
**「DBの同一トランザクションで “業務データ” と “送信予定メッセージ” を一緒に保存する」**ことで解決します💡
（Outboxは「トランザクション送信トレイ」＝あとで確実に送る箱📦） ([microservices.io][1])

---

## 19.3 最小構成の全体図🧩✨

![Minimum Outbox Architecture](./picture/saga_cs_study_019_min_architecture.png)

登場人物は3つだけ👇

* **① 業務処理**（例：注文作成）🧾
* **② Outboxテーブル**（送るべきメッセージを溜める）💾
* **③ 送信ワーカー**（溜まったメッセージを送って、送信済みにする）🏃‍♀️📮

イメージ👇

* リクエストが来た！
  → 業務データ更新＋Outbox追加（同一トランザクション）✅
* 別のループで
  → Outboxを拾う→送る→送信済みにする✅

これで「DB更新だけ成功して送信が消える事故」がかなり減ります🛡️ ([Microsoft Learn][2])

---

## 19.4 Outboxテーブル設計（最低限＋実戦向け）💾🧾

### 最低限いるカラム✅

* `Id`：Outbox行のID（GUID）
* `Type`：イベント種別（例：`OrderCreated`）
* `PayloadJson`：本体（JSON）
* `OccurredUtc`：イベント発生時刻
* `Status`：`New / Processing / Sent / Failed` など
* `RetryCount`：再送回数
* `NextAttemptUtc`：次に送っていい時刻（バックオフ用）
* `LockedUntilUtc`：ワーカーが掴んだロック期限（多重ワーカー対策）

### SQL Serverの例（シンプル版）🧱

![Outbox Table Schema Visual](./picture/saga_cs_study_019_table_schema.png)

```sql
CREATE TABLE dbo.OutboxMessages (
    Id              uniqueidentifier NOT NULL PRIMARY KEY,
    OccurredUtc     datetime2        NOT NULL,
    Type            nvarchar(200)    NOT NULL,
    PayloadJson     nvarchar(max)    NOT NULL,

    Status          tinyint          NOT NULL, -- 0=New, 1=Processing, 2=Sent, 3=Failed
    RetryCount      int              NOT NULL,
    NextAttemptUtc  datetime2        NULL,

    LockedUntilUtc  datetime2        NULL,
    LockOwner       nvarchar(100)    NULL,

    SentUtc         datetime2        NULL,
    LastError       nvarchar(2000)   NULL
);

-- 取り出しを速くするインデックス（超大事！）
CREATE INDEX IX_Outbox_Pickup
ON dbo.OutboxMessages (Status, NextAttemptUtc, OccurredUtc);
```

💡ポイント

* **取り出し条件に合う複合インデックス**がないと、Outboxが重くなって事故ります😇
* `PayloadJson`はサイズが大きくなりがちなので、必要なら「別テーブル分割」もアリ（上級編）🧠✨

---

## 19.5 書き込み側：業務更新とOutbox追加を「同じトランザクション」で🧾🔒

例：「注文を作る」＋「OrderCreatedを送る予定をOutboxに積む」🎁

### Entity（EF Core想定）🧸

```csharp
public sealed class Order
{
    public Guid Id { get; set; }
    public string CustomerId { get; set; } = "";
    public decimal Total { get; set; }
    public DateTime CreatedUtc { get; set; }
}

public sealed class OutboxMessage
{
    public Guid Id { get; set; }
    public DateTime OccurredUtc { get; set; }
    public string Type { get; set; } = "";
    public string PayloadJson { get; set; } = "";

    public byte Status { get; set; }           // 0=New,1=Processing,2=Sent,3=Failed
    public int RetryCount { get; set; }
    public DateTime? NextAttemptUtc { get; set; }

    public DateTime? LockedUntilUtc { get; set; }
    public string? LockOwner { get; set; }

    public DateTime? SentUtc { get; set; }
    public string? LastError { get; set; }
}
```

### 追加のしかた（超わかりやすい手動版）🧩

![Transaction Code Flow](./picture/saga_cs_study_019_tx_flow.png)

```csharp
public async Task<Guid> CreateOrderAsync(string customerId, decimal total, CancellationToken ct)
{
    var orderId = Guid.NewGuid();

    await using var tx = await _db.Database.BeginTransactionAsync(ct);

    var order = new Order
    {
        Id = orderId,
        CustomerId = customerId,
        Total = total,
        CreatedUtc = DateTime.UtcNow
    };
    _db.Orders.Add(order);

    var evt = new
    {
        OrderId = orderId,
        CustomerId = customerId,
        Total = total,
        OccurredUtc = DateTime.UtcNow
    };

    _db.OutboxMessages.Add(new OutboxMessage
    {
        Id = Guid.NewGuid(),
        OccurredUtc = evt.OccurredUtc,
        Type = "OrderCreated",
        PayloadJson = System.Text.Json.JsonSerializer.Serialize(evt),
        Status = 0,
        RetryCount = 0,
        NextAttemptUtc = DateTime.UtcNow
    });

    await _db.SaveChangesAsync(ct);
    await tx.CommitAsync(ct);

    return orderId;
}
```

✨これで

* 注文だけ保存される
* Outboxだけ保存される
  みたいな“片方だけ成功”が起きにくくなります✅

---

## 19.6 送信ワーカー（Outbox Dispatcher）🏃‍♀️📮

### 送信ワーカー（Dispatcher）のサイクル 🏃‍♀️📮

![Dispatcher Cycle Diagram](./picture/saga_cs_study_019_dispatcher_cycle.png)
```mermaid
loop 定期スキャン
    Worker[Dispatcher] -- "1: 掴む (Update Status=1)" --> DB[(Outbox Table)]
    Worker -- "2: 送信する" --> Bus[Message Bus]
    Bus -- "成功" --> Worker
    Worker -- "3: 送信済み (Update Status=2)" --> DB
end
```

送信ワーカーは「定期的にOutboxを拾って送る人」です🧑‍✈️✨
ASP.NET CoreのHosted Service（`BackgroundService`）で作れます。 ([Microsoft Learn][3])

### 大事な流れ（超重要）🧠🛡️

1. **送る対象を“掴む（Claim）”**
2. 掴んだ分だけ送る📨
3. 成功したら`Sent`、失敗したら`Failed + RetryCount++ + NextAttemptUtc更新`

この **①掴む** が雑だと、

* 複数ワーカーが同じ行を送る（二重送信）😱
  が起きます。

---

### 19.6.1 “掴む”を安全にやるSQL（SQL Server例）🔒

「まだ送ってないやつ」を、**原子的にProcessingへ変更して**、その行を返すのが強いです💪

```sql
DECLARE @now datetime2 = SYSUTCDATETIME();
DECLARE @lockOwner nvarchar(100) = @p0;   -- ワーカー識別子
DECLARE @lockUntil datetime2 = DATEADD(SECOND, 30, @now);

;WITH cte AS (
    SELECT TOP (20) *
    FROM dbo.OutboxMessages WITH (READPAST, UPDLOCK, ROWLOCK)
    WHERE Status = 0
      AND (NextAttemptUtc IS NULL OR NextAttemptUtc <= @now)
      AND (LockedUntilUtc IS NULL OR LockedUntilUtc < @now)
    ORDER BY OccurredUtc
)
UPDATE cte
SET Status = 1,
    LockedUntilUtc = @lockUntil,
    LockOwner = @lockOwner
OUTPUT inserted.*;
```

💡これの嬉しいところ

* **二重で掴みにくい**（ロック＋ステータス更新が一体）✅
* 送信対象をまとめて（バッチで）取れる✅

---

### 19.6.2 C#ワーカー例（めちゃ素直版）🧸

```csharp
public sealed class OutboxDispatcher : BackgroundService
{
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly ILogger<OutboxDispatcher> _logger;

    public OutboxDispatcher(IServiceScopeFactory scopeFactory, ILogger<OutboxDispatcher> logger)
    {
        _scopeFactory = scopeFactory;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        // ざっくり：1秒ごとに回す（本番は負荷見ながら調整）
        using var timer = new PeriodicTimer(TimeSpan.FromSeconds(1));

        while (await timer.WaitForNextTickAsync(stoppingToken))
        {
            try
            {
                await using var scope = _scopeFactory.CreateAsyncScope();
                var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                var publisher = scope.ServiceProvider.GetRequiredService<IMessagePublisher>();

                var lockOwner = Environment.MachineName + ":" + Guid.NewGuid().ToString("N");

                var claimed = await db.ClaimOutboxAsync(lockOwner, stoppingToken);
                if (claimed.Count == 0) continue;

                foreach (var msg in claimed)
                {
                    await ProcessOneAsync(db, publisher, msg, stoppingToken);
                }
            }
            catch (OperationCanceledException) { }
            catch (Exception ex)
            {
                _logger.LogError(ex, "OutboxDispatcher loop failed");
            }
        }
    }

    private static async Task ProcessOneAsync(
        AppDbContext db,
        IMessagePublisher publisher,
        OutboxMessage msg,
        CancellationToken ct)
    {
        try
        {
            await publisher.PublishAsync(msg.Type, msg.PayloadJson, ct);

            msg.Status = 2; // Sent
            msg.SentUtc = DateTime.UtcNow;
            msg.LockedUntilUtc = null;
            msg.LockOwner = null;
            msg.LastError = null;

            await db.SaveChangesAsync(ct);
        }
        catch (Exception ex)
        {
            msg.Status = 0; // New に戻して再送対象へ（または Failed）
            msg.RetryCount += 1;

            // ざっくり指数バックオフ（例）
            var delaySeconds = Math.Min(300, (int)Math.Pow(2, msg.RetryCount));
            msg.NextAttemptUtc = DateTime.UtcNow.AddSeconds(delaySeconds);

            msg.LockedUntilUtc = null;
            msg.LockOwner = null;
            msg.LastError = ex.Message.Length > 1800 ? ex.Message[..1800] : ex.Message;

            await db.SaveChangesAsync(ct);
        }
    }
}
```

✅ここでの超大事ポイント

* **送信成功→Sentにするのは、送信後**
* 失敗時は **`NextAttemptUtc` を未来にして、すぐ連打しない**（ブローカーに優しく🥹）
* 例外で落ちても **Outboxに残ってるから復旧できる**📦✨

---

## 19.7 重複対策：Outboxだけでは「二重送信」はゼロにならない😇🔁

Outboxは「送信漏れ」を減らす仕組みで、配送は基本 **at-least-once**（最低1回は届く）になりがちです。
だから現実はこう👇

* 送信は成功したけど、`Sent`更新前にプロセス落ちた💥
  → 次回また送る → 二重送信の可能性😇

つまり…
**最終的に守るのは受信側の冪等（Inbox）** です🛡️ ([microservices.io][1])

---

### Inboxの超定番パターン（受信側）📥✨

![Inbox Pattern Logic](./picture/saga_cs_study_019_inbox_pattern.png)

* 受信した`MessageId`（またはOutboxのId）を **Inboxテーブルに保存**
* **同じIDが来たら無視**（二重処理しない）

SQLのイメージ👇

```sql
CREATE TABLE dbo.InboxProcessed (
    MessageId uniqueidentifier NOT NULL PRIMARY KEY,
    ProcessedUtc datetime2 NOT NULL
);
```

受信処理（ざっくり）👇

```csharp
public async Task HandleAsync(Guid messageId, string payloadJson, CancellationToken ct)
{
    await using var tx = await _db.Database.BeginTransactionAsync(ct);

    // 先にInboxへ（重複ならここで弾ける）
    _db.InboxProcessed.Add(new InboxProcessed
    {
        MessageId = messageId,
        ProcessedUtc = DateTime.UtcNow
    });

    // ここで業務処理（在庫引当など）
    // ...

    try
    {
        await _db.SaveChangesAsync(ct);
        await tx.CommitAsync(ct);
    }
    catch (DbUpdateException)
    {
        // すでに同じMessageIdがある（=重複到着）なら無視してOK
        await tx.RollbackAsync(ct);
    }
}
```

この “Inboxで受信冪等” が入ると、二重送信が来ても落ち着いていられます😌🛡️

---

## 19.8 失敗の扱い：RetryとPoison（毒メッセージ）☠️🔄

![Poison Message Handling](./picture/saga_cs_study_019_poison_message.png)

送信がずっと失敗するメッセージもあります😵‍💫
例：Payloadが壊れてる／宛先設定ミス／相手が永遠に受け付けない…など

おすすめ設計🧠✨

* `RetryCount` が一定超えたら `Failed`（または `Poison`）へ☠️
* `LastError` を残す📝
* 運用で見つけやすいように「一覧表示できる」状態を作る👀

---

## 19.9 ミニ演習📝✨

### 演習1：Outboxの状態を決めよう📋😊

`New / Processing / Sent / Failed` 以外に必要？
例：`Poison`（手動対応待ち）☠️

### 演習2：取り出しを速くしよう🏎️💨

`IX_Outbox_Pickup` の列順を、取り出し条件に合わせて説明してみよう🔍

### 演習3：障害ごっこ😈

* 送信処理の途中で例外を投げる
* 次のループで再送される
* Inboxで二重処理が防げる
  ここまでを通して確認✅🔁

---

## 19.10 AI活用（Copilot / Codex向け）プロンプト集🤖💡

* 「OutboxMessagesのインデックス設計をレビューして。取り出し条件は `Status` と `NextAttemptUtc` と `OccurredUtc` です📦」
* 「SQL ServerでOutboxを“掴む（Claim）”ために、二重取得が起きにくいSQLを書いて。`UPDATE ... OUTPUT inserted` を使いたい🔒」
* 「送信失敗時のバックオフ設計案を3つ。指数／固定＋ジッター／上限付き指数で比較して🧯」
* 「Inbox（受信冪等）をEF Coreで実装する時の注意点。ユニーク制約と例外処理のコツを教えて🛡️」
* 「Outboxのワーカーが止まってるかを検知する“最低限のヘルスチェック案”を出して👀」

---

## 19.11 まとめ🌟

* Outboxは「DB更新」と「送る予定」を**同じトランザクション**で守る仕組み📦✅ ([microservices.io][1])
* 送信ワーカーは **Claim → 送信 → Sent更新** の順が命🏃‍♀️📮
* 二重送信はゼロにならないので、最後は **受信側Inboxで冪等**が本命🛡️🔁 ([microservices.io][1])
* Hosted Service（`BackgroundService`）で定期処理は作れる🧰 ([Microsoft Learn][3])
* 2026年時点では .NET 10 がLTSとして現役で、サポート面でも安心寄り🧡 ([Microsoft for Developers][4])

[1]: https://microservices.io/patterns/data/transactional-outbox.html?utm_source=chatgpt.com "Pattern: Transactional outbox"
[2]: https://learn.microsoft.com/en-us/dotnet/architecture/microservices/architect-microservice-container-applications/asynchronous-message-based-communication?utm_source=chatgpt.com "Asynchronous message-based communication - .NET"
[3]: https://learn.microsoft.com/en-us/aspnet/core/fundamentals/host/hosted-services?view=aspnetcore-10.0&utm_source=chatgpt.com "Background tasks with hosted services in ASP.NET Core"
[4]: https://devblogs.microsoft.com/dotnet/announcing-dotnet-10/?utm_source=chatgpt.com "Announcing .NET 10"
