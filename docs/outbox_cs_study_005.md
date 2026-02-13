# 第05章：トランザクション超入門（“全部成功 or 全部失敗”）🔒🍙

## 今日のゴール 🎯✨

* **Commit（確定）** と **Rollback（取り消し）** の感覚をつかむ😺
* 「**同じトランザクションに入れる**」がどういう意味か、体で覚える💪
* Outboxで一番大事な「**DB更新とOutbox追加を“同時に確定”**」の土台を作る🏗️📦

---

## 1) トランザクションってなに？🍙🔒

トランザクションは、ひとことで言うと👇

> **複数のDB操作を “ひとまとまり” にして、**
> **全部できたら確定（Commit）／途中で失敗したら全部なかったこと（Rollback）** にする仕組み✨

たとえば「注文を作る」って処理は、実はDBの中で色々やりたいよね？🛒

* Orders に注文行を追加する🧾
* OutboxMessages に「注文が作られたよ」メッセージを追加する📦📩

この2つ、**片方だけ成功**すると事故ります😱
だから、**“2つまとめて成功 or 2つまとめて失敗”**にしたい → それがトランザクション🔒🍙

---

## 2) Commit / Rollback をゲームで覚える🎮✨

![Commit vs Rollback Game](./picture/outbox_cs_study_005_commit_rollback_game.png)

* **Commit（コミット）** = セーブ完了💾✅
* **Rollback（ロールバック）** = セーブせずに終了、なかったことにする🔙💥

「最後までノーミスならセーブ」
「途中でバグったらロードして戻す」
この感覚がそのままDB版になったイメージだよ〜😺✨

---

## 3) 「同じトランザクションに入れる」ってどういうこと？🧠🔗

![Transaction Scope](./picture/outbox_cs_study_005_tx_scope.png)
![Same Bento Box](./picture/outbox_cs_study_005_same_bento_box.png)

これ、言い換えるとこう👇

> **同じ“お弁当箱”の中に入れる🍙**
> → ふたを閉める（Commit）まで、外には確定として見せない
> → こぼしたら箱ごと捨てる（Rollback）

Outboxでは特に👇が重要💡

* **業務テーブル（例：Orders）**
* **Outboxテーブル（例：OutboxMessages）**

この2つを **同じトランザクション** に入れることで、
「注文だけ入ったのに通知が残ってない😭」みたいなズレが起きにくくなるよ🛡️📦

---

## 4) 先に知っておくと安心：EF Core の “デフォルト安全” 🧯✨

![EF Core Safety Net](./picture/outbox_cs_study_005_ef_core_safety.png)

実は EF Core は、基本こう動くよ👇

* **`SaveChanges()` 1回の中の変更は、トランザクションでまとめて処理される**
* だから **途中で失敗したら、全部ロールバックされてDBは無傷** 🧡

つまり、普通は「`SaveChanges()` 1回で済むなら」それだけでも安全寄り👍
（※ただし、Outboxでは「複数回SaveChanges」や「生SQL混在」なども出てくるから、手動トランザクションを覚える価値が大きいよ！）([Microsoft Learn][1])

---

## 5) 手を動かそう：Orders と Outbox を “同時に確定” する🏃‍♀️💨📦

ここではミニ構成で👇をやるよ✨

* Orders に追加🧾
* OutboxMessages に追加📦
* **同じトランザクションで Commit 🔒✅**

（この教材のコードは、今の主流の .NET 10 / C# 14 を想定してるよ）([Microsoft][2])

## 5-1) NuGet（パッケージ）📦

最低限これ👇

* `Microsoft.EntityFrameworkCore`
* `Microsoft.EntityFrameworkCore.SqlServer`

---

## 5-2) モデル＆DbContext を用意 🧩✨

```csharp
using System.Text.Json;
using Microsoft.EntityFrameworkCore;

public sealed class AppDbContext : DbContext
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OutboxMessage> OutboxMessages => Set<OutboxMessage>();

    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }
}

public sealed class Order
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string CustomerEmail { get; set; } = "";
    public decimal Amount { get; set; }
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
}

public sealed class OutboxMessage
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string Type { get; set; } = "";
    public string Payload { get; set; } = "";
    public DateTimeOffset OccurredAt { get; set; } = DateTimeOffset.UtcNow;

    public static OutboxMessage Create(string type, string payloadJson) =>
        new OutboxMessage { Type = type, Payload = payloadJson, OccurredAt = DateTimeOffset.UtcNow };
}
```

---

## 5-3) “同じトランザクション” で2つ書いて Commit 🔒🍙✅

![Code Structure Visual](./picture/outbox_cs_study_005_code_structure_visual.png)

```csharp
using Microsoft.EntityFrameworkCore;

// 例：SQL Server LocalDB（Windowsで手軽に使いやすい構成）
var connectionString =
    "Server=(localdb)\\MSSQLLocalDB;Database=OutboxChapter5Demo;Trusted_Connection=True;TrustServerCertificate=True;";

var options = new DbContextOptionsBuilder<AppDbContext>()
    .UseSqlServer(connectionString)
    .Options;

await using var db = new AppDbContext(options);

// 章5では “動かして体感” が目的なので、サクッと作る（本番は Migration 推奨）
await db.Database.EnsureCreatedAsync();

await using var tx = await db.Database.BeginTransactionAsync(); // ← ここが「お弁当箱🍙」

try
{
    // ① 業務データ（注文）を追加🧾
    var order = new Order
    {
        CustomerEmail = "alice@example.com",
        Amount = 1200m
    };
    db.Orders.Add(order);

    // ② Outbox に「起きた事実」を積む📦
    var payload = JsonSerializer.Serialize(new
    {
        orderId = order.Id,
        order.CustomerEmail,
        order.Amount
    });

    db.OutboxMessages.Add(OutboxMessage.Create(
        type: "OrderCreated.v1",
        payloadJson: payload
    ));

    // ③ まとめて保存（ここで Orders + OutboxMessages が一緒にDBへ）🧠✨
    await db.SaveChangesAsync();

    // ④ 最後に確定！✅
    await tx.CommitAsync();

    Console.WriteLine("✅ Commit 完了！ Orders と OutboxMessages が同時に確定したよ🎉");
}
catch (Exception ex)
{
    // 途中で失敗したら全部なかったことにする💥
    await tx.RollbackAsync();
    Console.WriteLine($"💥 Rollback！ 理由: {ex.Message}");
}
```

✅ これが「同じトランザクションに入れる」の最小形だよ〜！📦🍙

---

## 6) Rollback を “体感” する実ufmer3 👀💥

![Rollback Experience](./picture/outbox_cs_study_005_rollback_experience.png)

「ほんとに戻るの？」を体験しよ✨
わざと `SaveChangesAsync()` の後に例外を投げてみるよ👇

```csharp
await using var tx = await db.Database.BeginTransactionAsync();

try
{
    // ①②③は同じ（Orders と OutboxMessages を追加して SaveChanges）
    // ...

    await db.SaveChangesAsync();

    // わざと落とす💥（たとえば通知処理で例外が出た想定）
    throw new InvalidOperationException("わざと落としたよ😇");

    // await tx.CommitAsync(); ← ここまで到達しない
}
catch
{
    await tx.RollbackAsync();
}

// 別コンテキストで確認（トラッキングの影響を避ける）👀
await using var db2 = new AppDbContext(options);
var ordersCount = await db2.Orders.CountAsync();
var outboxCount = await db2.OutboxMessages.CountAsync();

Console.WriteLine($"Orders: {ordersCount}, Outbox: {outboxCount} （両方0なら成功✨）");
```

ポイント💡

* `SaveChangesAsync()` まで行ってても、**Commit してないなら確定じゃない**
* Rollback すれば、**Orders も Outbox も一緒に消える**🧹✨

---

## 7) TransactionScope っていつ使うの？🧠🔭

![Async Flow Option](./picture/outbox_cs_study_005_tx_scope_option.png)

EF Core の `BeginTransaction()` は **「そのDbContext/接続の範囲」**で分かりやすい👍
でも、たとえば👇みたいに **複数の技術をまたぐ**ときに `TransactionScope` が出てくることがあるよ🧩

* ADO.NET の生SQL + EF Core を同じ取引に入れたい
* 複数のDB操作を「周囲の大きなスコープ」でまとめたい

ただし注意⚠️

* `async/await` するなら、**AsyncFlowOption を Enabled**にしないと “トランザクションが流れない” 事故が起きがち😱([Microsoft Learn][1])

ミニ例👇

```csharp
using System.Transactions;

using var scope = new TransactionScope(
    TransactionScopeOption.Required,
    new TransactionOptions { IsolationLevel = IsolationLevel.ReadCommitted },
    TransactionScopeAsyncFlowOption.Enabled // ← asyncで大事！
);

// ここでDB操作（EF Core / ADO.NET など）をまとめる

scope.Complete(); // ← Commit 相当
```

---

## 8) トランザクション “やらかし集” 😵‍💫🧨

## やらかし①：トランザクションが長すぎる 🐢💤

![Long Transaction Turtle](./picture/outbox_cs_study_005_long_tx_turtle.png)

* 例：トランザクション開始 → ユーザー入力待ち → commit
* その間、DBのロックが長引いて、他の処理が詰まる😱
  ✅ 対策：**DBに触る直前に開始して、サッと確定**🏃‍♀️💨

## やらかし②：外部通信（HTTP/Queue/メール）をトランザクション内でやる 📡💥

* 外部は遅い＆失敗しやすい → ロックが長引く → 地獄👹
  ✅ 対策：**DB内で完結（Orders + Outbox）までをトランザクション**
  → 外部送信は「後で」（これがOutboxの気持ちよさ）📦➡️📩

## やらかし③：SaveChangesを2回に分けて、片方だけ成功 😭

* 1回目：Orders 保存 ✅
* 2回目：Outbox 保存 💥
  → “注文だけある”事故
  ✅ 対策：**同じトランザクションでまとめる**🔒🍙

---

## 9) まとめ 🧡✨

* トランザクションは **「全部成功 or 全部失敗」**の安全装置🔒
* Outboxで一番大事なのは **「業務更新 + Outbox追加」を同じ取引で確定**📦🍙
* EF Core は `SaveChanges` 1回なら基本安全だけど、Outboxでは明示トランザクションが強い味方💪([Microsoft Learn][1])
* `TransactionScope` を使うなら `TransactionScopeAsyncFlowOption.Enabled` を忘れない😇([Microsoft Learn][3])

---

## チェック問題（ゆるめ）📝😺

1. Commit しなかったトランザクションは、どうなる？🔒
2. Outboxで「同じトランザクションに入れる」2つのものは何？📦
3. トランザクション中にHTTP送信しちゃダメ寄りなのはなぜ？📡💥

（答えは次章以降の実装で、どんどん体に入ってくるよ〜！✨）

[1]: https://learn.microsoft.com/en-us/ef/core/saving/transactions "Transactions - EF Core | Microsoft Learn"
[2]: https://dotnet.microsoft.com/en-us/download/dotnet "Browse all .NET versions to download | .NET"
[3]: https://learn.microsoft.com/en-us/dotnet/api/system.transactions.transactionscopeasyncflowoption?view=net-10.0 "TransactionScopeAsyncFlowOption Enum (System.Transactions) | Microsoft Learn"
