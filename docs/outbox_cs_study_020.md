# 第20章：冪等性（実装編）：受け手側の重複排除 ✅🛡️

## 今日のゴール 🎯✨

* 同じメッセージ（同じ `MessageId`）が **2回届いても、処理結果は1回分**にできるようになる ✅
* 「受け手側で重複排除する」ための **DB設計（Inboxテーブル）** と **C#実装** が書けるようになる 🧠💪
* ミニ演習で「2回送ってもポイントが1回しか増えない」を確認する 🎮🧾

---

## 1) まず大事な前提：重複は“普通に起きる” 😅📩📩

Outbox + Relay の世界はだいたい **At-least-once（最低1回は送る）** なので、
**ネットワークの再送**や**タイムアウト後の再試行**で「同じメッセージがもう一回届く」が起こり得るよ〜😇

だから受け手はこう考えるのが基本👇
**「重複が来ても壊れない（= 冪等）」を、受け手が守る** 🤝✨

---

## 2) 冪等性キーはこれ！🔑✨（OutboxId を使うのが定番）

受け手で重複判定するには「これが同じメッセージだよ」って分かるキーが必要だよね？👀
Outboxパターンでは、送信側が持ってる **Outboxの行ID（OutboxId）** を `MessageId` として渡すのが超定番！🪪✨

* `MessageId`（= OutboxId）: **1メッセージに1つの一意なID**
* 受け手は `MessageId` を **“処理済みかどうか”** の判定に使う ✅

---

## 3) 受け手側の重複排除：2つの王道 👑

![Inbox Guard](./picture/outbox_cs_study_020_inbox_guard.png)

## 方法A：処理済みテーブル（Inbox的なもの）📥🧾（おすすめ！）

受け手のDBに「このメッセージは処理したよ」って記録を残す方式！

* Inboxテーブルに `MessageId` を保存しておく
* 同じ `MessageId` が来たら **“もうやったよ”** で処理をスキップ ✅

メリット：

* **重複排除が安定**（分散環境でも強い）💪
* 監査・運用が楽（いつ処理したか見える）👀

---

## 方法B：ユニーク制約で二重登録を弾く 🧱✨（最小構成）

Inboxテーブルや業務テーブルに **ユニーク制約**（Unique Index / Unique Constraint）を付けて、
「二重に入れようとしたらDBが拒否する」方式！

* C#側は `DbUpdateException` を受けて「重複だね」で握る 🤝

メリット：

* 実装がシンプルで強い ✅
* “チェックしてからINSERT”より競合に強い（並列でも安全）⚔️

---

## 4) 今回作るサンプルのシナリオ 🎁💎

**「ポイント付与メッセージ」** を受けて、ユーザーのポイントを増やすよ〜✨
でも重複したらポイント2倍になっちゃう…それは事故😱

なのでこうする👇

* Inboxテーブルで `MessageId` を **一度だけ** 記録
* そのあとポイント付与を実行
* 同じ `MessageId` が来たら **即スキップ** ✅

---

## 5) 最新の土台（2026時点）🧱✨

* `.NET 10` は LTS（長期サポート）で、2028年11月までサポート予定だよ〜📌 ([Microsoft][1])
* `EF Core 10` は .NET 10 向けの LTS で、2028年11月までサポート予定✨（そして EF Core 10 は .NET 10 が必要） ([Microsoft Learn][2])

---

## 6) DB設計：Inbox（処理済み）テーブル 📥🧾

## 6.1 最小カラム案（これでOK）✅

* `Consumer`：この受け手アプリ名（例 `"ReceiverApi"`）
* `MessageId`：冪等性キー（= OutboxId）
* `MessageType`： `"PointsGranted.v1"` みたいな型名
* `ReceivedAt` / `ProcessedAt`：いつ受けた？いつ処理した？⏰

## 6.2 超重要：ユニーク制約 🧱✨

**同じ Consumer に同じ MessageId は1回だけ** にする！

* Unique: `(Consumer, MessageId)`

これがあると、並列で同じメッセージが来てもDBが守ってくれるよ🛡️

---

## 7) 実装：受け手API（Minimal API + EF Core）🧑‍💻✨

## 7.1 プロジェクト作成 & パッケージ追加 📦

```powershell
dotnet new web -n ReceiverApi
cd ReceiverApi

dotnet add package Microsoft.EntityFrameworkCore.SqlServer
dotnet add package Microsoft.EntityFrameworkCore.Design
dotnet tool install --global dotnet-ef
```

---

## 7.2 受け取るメッセージ形式（例）📩

```json
{
  "messageId": "9b4df7bf-25d4-4a1e-9f07-4cc6fbb4a3ad",
  "type": "PointsGranted.v1",
  "payload": {
    "userId": 123,
    "amount": 100
  }
}
```

---

## 7.3 エンティティ：InboxMessage & ポイント用テーブル 🎁

```csharp
// Inbox（処理済み管理）
public sealed class InboxMessage
{
    public long Id { get; set; }

    public required string Consumer { get; set; }      // "ReceiverApi" など
    public required Guid MessageId { get; set; }       // OutboxId
    public required string MessageType { get; set; }   // "PointsGranted.v1"
    public required string PayloadJson { get; set; }   // 生JSON（監査・デバッグ用）
    public DateTimeOffset ReceivedAt { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset? ProcessedAt { get; set; }
}

// ポイント残高（1ユーザー1行）
public sealed class UserPoints
{
    public int UserId { get; set; }
    public long Balance { get; set; }
}

// ポイント付与履歴（監査用）
public sealed class PointGrant
{
    public long Id { get; set; }
    public int UserId { get; set; }
    public long Amount { get; set; }
    public Guid MessageId { get; set; }               // ここにも入れて二重安全🛡️
    public DateTimeOffset GrantedAt { get; set; } = DateTimeOffset.UtcNow;
}
```

---

## 7.4 DbContext：ユニーク制約を付ける 🧱✨

```csharp
using Microsoft.EntityFrameworkCore;

public sealed class ReceiverDbContext : DbContext
{
    public ReceiverDbContext(DbContextOptions<ReceiverDbContext> options) : base(options) {}

    public DbSet<InboxMessage> InboxMessages => Set<InboxMessage>();
    public DbSet<UserPoints> UserPoints => Set<UserPoints>();
    public DbSet<PointGrant> PointGrants => Set<PointGrant>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<UserPoints>()
            .HasKey(x => x.UserId);

        // Inboxの重複排除キー ✅
        modelBuilder.Entity<InboxMessage>()
            .HasIndex(x => new { x.Consumer, x.MessageId })
            .IsUnique();

        // 念のため：付与履歴も MessageId で重複防止 ✅
        modelBuilder.Entity<PointGrant>()
            .HasIndex(x => x.MessageId)
            .IsUnique();
    }
}
```

---

## 7.5 Program.cs：受け手の重複排除ロジック（本丸）👑

ポイント付与の処理は **「トランザクションの中で」** こう流すよ👇

1. Inboxに「処理開始」を入れる（ユニーク制約で重複を弾ける）
2. 付与処理をする
3. Inboxの `ProcessedAt` を埋めてコミット ✅

```csharp
using System.Text.Json;
using Microsoft.Data.SqlClient;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<ReceiverDbContext>(opt =>
{
    // 例：SQL Server LocalDB（接続文字列は appsettings.json に置いてもOK）
    opt.UseSqlServer(builder.Configuration.GetConnectionString("Default"));
});

var app = builder.Build();

const string ConsumerName = "ReceiverApi";

app.MapPost("/messages/points-granted", async (PointsMessage message, ReceiverDbContext db) =>
{
    // 監査用に payload を生JSONで保存したい時用（なくてもOK）
    var payloadJson = JsonSerializer.Serialize(message.Payload);

    await using var tx = await db.Database.BeginTransactionAsync();

    // ✅ 1) Inboxに「このMessageIdを処理する！」を登録（重複ならここで止まる）
    var inbox = new InboxMessage
    {
        Consumer = ConsumerName,
        MessageId = message.MessageId,
        MessageType = message.Type,
        PayloadJson = payloadJson
    };

    db.InboxMessages.Add(inbox);

    try
    {
        await db.SaveChangesAsync(); // ここでユニーク違反なら「重複」🎯
    }
    catch (DbUpdateException ex) when (IsUniqueViolation(ex))
    {
        await tx.RollbackAsync();
        return Results.Ok(new { status = "duplicate_ignored", messageId = message.MessageId });
    }

    // ✅ 2) ここから先は「初回だけ」通る
    var userPoints = await db.UserPoints.FindAsync(message.Payload.UserId);
    if (userPoints is null)
    {
        userPoints = new UserPoints { UserId = message.Payload.UserId, Balance = 0 };
        db.UserPoints.Add(userPoints);
    }

    userPoints.Balance += message.Payload.Amount;

    db.PointGrants.Add(new PointGrant
    {
        UserId = message.Payload.UserId,
        Amount = message.Payload.Amount,
        MessageId = message.MessageId
    });

    // Inboxを「処理完了」にする ✅
    inbox.ProcessedAt = DateTimeOffset.UtcNow;

    await db.SaveChangesAsync();
    await tx.CommitAsync();

    return Results.Ok(new { status = "processed", messageId = message.MessageId });
});

app.Run();

static bool IsUniqueViolation(DbUpdateException ex)
{
    // SQL Server: 2601 (unique index) / 2627 (unique constraint)
    if (ex.InnerException is SqlException sqlEx)
        return sqlEx.Number is 2601 or 2627;

    return false;
}

public sealed record PointsMessage(Guid MessageId, string Type, PointsPayload Payload);
public sealed record PointsPayload(int UserId, long Amount);
```

---

## 7.6 接続文字列（appsettings.json）🧾

```json
{
  "ConnectionStrings": {
    "Default": "Server=(localdb)\\MSSQLLocalDB;Database=OutboxReceiver;Trusted_Connection=True;MultipleActiveResultSets=true"
  }
}
```

---

## 7.7 マイグレーション作成＆DB作成 🧰

```powershell
dotnet ef migrations add Init
dotnet ef database update
dotnet run
```

---

## 8) ミニ演習：同じメッセージを2回送っても1回しか増えない ✅🎯

## 8.1 PowerShellで2回送ってみる 📮📮

同じ `messageId` を使うのがポイントだよ〜✨

```powershell
$body = @{
  messageId = "9b4df7bf-25d4-4a1e-9f07-4cc6fbb4a3ad"
  type = "PointsGranted.v1"
  payload = @{
    userId = 123
    amount = 100
  }
} | ConvertTo-Json -Depth 5

## 1回目（processed になるはず）
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/messages/points-granted" `
  -ContentType "application/json" -Body $body

## 2回目（duplicate_ignored になるはず）
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/messages/points-granted" `
  -ContentType "application/json" -Body $body
```

期待する結果👇

* 1回目：`processed` ✅
* 2回目：`duplicate_ignored` ✅

---

## 8.2 DBを見て確認 👀🧾

SSMS（SQL Server Management Studio）や好きなDBビューアで見てもOK！

```sql
SELECT * FROM InboxMessages ORDER BY Id DESC;
SELECT * FROM UserPoints WHERE UserId = 123;
SELECT * FROM PointGrants ORDER BY Id DESC;
```

チェックポイント ✅

* `InboxMessages` は **1行だけ**（同じMessageIdは増えない）
* `UserPoints.Balance` は **+100だけ**
* `PointGrants` も **1行だけ**

---

## 9) よくある落とし穴集 🕳️😱（ここ超大事！）

## 落とし穴1：`SELECTしてからINSERT` で判定する（レースに弱い）🏃‍♀️💥

「処理済みか確認して、未処理ならINSERT」ってやると、
並列で同時に来たときに **両方とも未処理に見えて二重処理** が起きることがあるよ😵‍💫

➡️ **ユニーク制約＋例外ハンドリング** が強い 🧱✨

---

## 落とし穴2：Inbox登録と業務処理を別トランザクションにする 🧨

* Inboxだけ先にコミット
* 業務処理で失敗
  みたいになると「Inboxには入ってるのに処理は終わってない」状態に…😱

➡️ **Inbox登録〜業務処理〜完了まで1トランザクション** が基本 ✅

---

## 落とし穴3：Consumer（受け手名）を入れずに MessageId だけでユニークにする 🤔

同じDBを複数の受け手が共有してると、別の受け手まで巻き添えで弾いちゃうことがあるよ〜😵

➡️ `(Consumer, MessageId)` の複合ユニークが安心 ✅

---

## 10) AI活用メモ（そのまま貼って使える）🤖📝✨

## 雛形生成プロンプト例

* 「EF Core で `(Consumer, MessageId)` にユニークインデックスを張る DbContext を作って」
* 「DbUpdateException のユニーク制約違反を SQL Server で判定するサンプルを書いて（2601/2627）」
* 「同じ MessageId を2回POSTしてもポイントが1回しか増えない統合テスト案を出して」

## 人間が必ず見るチェック 🔍✅

* トランザクション範囲は **Inbox登録〜業務処理〜完了** まで含んでる？
* ユニーク制約が **DBに本当に作られてる**？（マイグレーション確認）
* 重複時に「例外を握りつぶしてOKにする」条件が **ユニーク違反だけ** になってる？

---

## 11) まとめ：この章で覚える合言葉 🧠💡

* **重複は来るもの** 😇📩
* **冪等性キー（MessageId = OutboxId）で受け手が守る** 🔑
* **Inbox（処理済み）+ ユニーク制約 + トランザクション** が鉄板 🧱🔒✅
* **同じメッセージ2回でも、結果は1回** 🎯✨

[1]: https://dotnet.microsoft.com/ja-jp/platform/support/policy?utm_source=chatgpt.com "公式の .NET サポート ポリシー | .NET"
[2]: https://learn.microsoft.com/en-us/ef/core/what-is-new/ef-core-10.0/whatsnew?utm_source=chatgpt.com "What's New in EF Core 10"
