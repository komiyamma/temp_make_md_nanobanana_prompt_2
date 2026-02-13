# 第12章：書き込み側の実装（C# + DB更新＋Outbox追加）✍️🔒

## 今日のゴール 🎯✨

* ✅ **Orders（業務テーブル）に保存**しつつ
* ✅ **Outbox（OutboxMessages）にも同時に積む**
* ✅ しかも **同一トランザクション**で「どっちも成功 or どっちも失敗」にする 👑

※本章のコードは **.NET 10 / C# 14 / EF Core 10** を想定（2025年11月リリースのLTS世代）で書くよ 🧡
([Microsoft Learn][6])

---

## 1. まず全体像（超重要）🗺️📦

![Atomic Commit](./picture/outbox_cs_study_012_atomic_commit.png)

やりたいことはこれだけ！👇

1. 注文を作る 🛒
2. 「注文作ったよ」イベントを Outbox に積む 📦
3. 1つのトランザクションでコミットする 🔒✨

イメージ図（頭に入れてからコードへ）🧠💡

* **BEGIN TX**

  * INSERT Orders
  * INSERT OutboxMessages
* **COMMIT**
* （途中で例外なら **ROLLBACK**）🧯

---

## 2. 今回のミニモデル（Orders と OutboxMessages）🧩✨

## Orders（業務テーブル）🛒

* Id（Guid）
* CustomerId（Guid）
* TotalAmount（decimal）
* CreatedAt（DateTimeOffset）

## OutboxMessages（Outboxテーブル）📦

* Id（Guid） … **OutboxId（後で冪等性キーにも使える予定）**
* Type（string） … 例：`OrderCreated.v1`
* Payload（string） … JSON
* OccurredAt（DateTimeOffset）

※運用版で Status / RetryCount / LastError を足すのは後の章でOK（第10章寄り）🙂

---

## 3. エンティティと DbContext を用意する 🧱🧑‍💻

## 3.1 Entity（C#）✨

```csharp
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

public sealed class Order
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid CustomerId { get; set; }

    [Column(TypeName = "decimal(18,2)")]
    public decimal TotalAmount { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;
}

public sealed class OutboxMessage
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    [MaxLength(200)]
    public string Type { get; set; } = default!;

    public string Payload { get; set; } = default!;

    public DateTimeOffset OccurredAt { get; set; } = DateTimeOffset.UtcNow;
}
```

## 3.2 DbContext（EF Core 10）🗃️

```csharp
using Microsoft.EntityFrameworkCore;

public sealed class AppDbContext : DbContext
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OutboxMessage> OutboxMessages => Set<OutboxMessage>();

    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Order>()
            .HasIndex(x => x.CreatedAt);

        modelBuilder.Entity<OutboxMessage>()
            .HasIndex(x => x.OccurredAt);

        base.OnModelCreating(modelBuilder);
    }
}
```

---

## 4. 「同一トランザクション」実装の核心 👑🔒

![Transaction Scope Visual](./picture/outbox_cs_study_012_transaction_scope_visual.png)

## 4.1 重要ポイント（ここ試験に出るやつ）📌😺

* **Orders 保存**と**Outbox 追加**が「別々のトランザクション」だとズレる 😱
* だから **“同じトランザクションの中で” 2つとも書く** ✨

---

## 5. ユースケース実装：注文作成 + Outbox 追加 🛒📦

ここでは「アプリ層のサービス（UseCase）」として実装するよ（第11章の責務分離の続き）🍱✨

## 5.1 送るイベント（Payload用のDTO）📩

![Payload Serialization](./picture/outbox_cs_study_012_payload_serialization.png)

```csharp
public sealed record OrderCreatedEventV1(
    Guid OutboxId,
    Guid OrderId,
    Guid CustomerId,
    decimal TotalAmount,
    DateTimeOffset OccurredAt
);
```

## 5.2 UseCase（同一トランザクションでまとめて書く）🔒✨

✅ まずは “基本の形” 👇

```csharp
using System.Text.Json;
using Microsoft.EntityFrameworkCore;

public sealed class CreateOrderUseCase
{
    private readonly AppDbContext _db;

    public CreateOrderUseCase(AppDbContext db)
    {
        _db = db;
    }

    public async Task<Guid> ExecuteAsync(Guid customerId, decimal totalAmount, bool simulateCrash = false, CancellationToken ct = default)
    {
        // ✅ SQL Server などで “一時的な失敗” を吸収したいときの定番（後半で説明）
        var strategy = _db.Database.CreateExecutionStrategy();

        return await strategy.ExecuteAsync(async () =>
        {
            await using var tx = await _db.Database.BeginTransactionAsync(ct);

            var order = new Order
            {
                CustomerId = customerId,
                TotalAmount = totalAmount,
                CreatedAt = DateTimeOffset.UtcNow
            };

            var outbox = new OutboxMessage
            {
                Id = Guid.NewGuid(),
                Type = "OrderCreated.v1",
                OccurredAt = DateTimeOffset.UtcNow,
                Payload = "" // 後で入れる
            };

            var evt = new OrderCreatedEventV1(
                OutboxId: outbox.Id,
                OrderId: order.Id,
                CustomerId: order.CustomerId,
                TotalAmount: order.TotalAmount,
                OccurredAt: outbox.OccurredAt
            );

            outbox.Payload = JsonSerializer.Serialize(evt);

            _db.Orders.Add(order);
            _db.OutboxMessages.Add(outbox);

            await _db.SaveChangesAsync(ct);

            // 🔥 わざと落として「ちゃんとロールバックされる？」を観察する用
            if (simulateCrash)
            {
                throw new InvalidOperationException("Simulated crash right after SaveChanges 😈💥");
            }

            await tx.CommitAsync(ct);

            return order.Id;
        });
    }
}
```

### ここが嬉しいポイント 🧡

* `BeginTransactionAsync()` の中で **2つ追加**して
* `SaveChangesAsync()` で **まとめてDBに反映**して
* `CommitAsync()` で **確定**する 🔒✨

EF Core 10 は .NET 10 とセットのLTS世代で、公式も .NET 10 前提になってるよ 📚
([Microsoft Learn][7])

---

## 6. “途中で落ちたらどうなる？” をちゃんと理解する 🧯👀

## ケースA：SaveChanges 前に落ちた 😴💥

![Crash Before Commit](./picture/outbox_cs_study_012_crash_before_commit.png)

* まだDBに何も書かれてない
* ✅ Orders も Outbox も **0件**（何も残らない）

## ケースB：SaveChanges 後、Commit 前に落ちた 😈💥

* いったんINSERTは走ったように見えても、**トランザクション未コミット**
* ✅ Dispose/例外で **ROLLBACK**
* 結果：Orders も Outbox も **残らない**（＝ズレない！）🎉

## ケースC：Commit 後に落ちた 🧨

![Crash After Commit](./picture/outbox_cs_study_012_crash_after_commit.png)

* ✅ Orders と Outbox は **両方残る**
* これは OK（次章以降で Relay が拾って送る）🚚📩

---

## 7. DBを覗いて確認しよう 👀🧾

## 7.1 まず “成功パターン” ✅✨

* `simulateCrash = false` で実行
* Orders と OutboxMessages が **同じ回数**増えてたら勝ち 🏆

## 7.2 次に “クラッシュ注入” 😈💥

![Simulate Crash Switch](./picture/outbox_cs_study_012_simulate_crash_switch.png)

* `simulateCrash = true` で実行
* ✅ Orders も OutboxMessages も **増えてない**（ロールバック確認）🎯

---

## 8. 最小のAPIにつなぐ（呼べるようにする）📮🛒

![API Integration](./picture/outbox_cs_study_012_api_integration.png)

Minimal API 例（コントローラでもOK）🙂

```csharp
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<AppDbContext>(options =>
{
    // 例：SQL Server LocalDB（接続文字列は各自の環境に合わせてOK）
    options.UseSqlServer(builder.Configuration.GetConnectionString("Default"));
});

builder.Services.AddScoped<CreateOrderUseCase>();

var app = builder.Build();

app.MapPost("/orders", async (CreateOrderRequest req, CreateOrderUseCase useCase, CancellationToken ct) =>
{
    var orderId = await useCase.ExecuteAsync(req.CustomerId, req.TotalAmount, req.SimulateCrash, ct);
    return Results.Ok(new { OrderId = orderId });
});

app.Run();

public sealed record CreateOrderRequest(Guid CustomerId, decimal TotalAmount, bool SimulateCrash);
```

SQL Server を使うなら、最新系として **SQL Server 2025 がGA済み**だよ（2025-11-18）🗄️✨
([TECHCOMMUNITY.MICROSOFT.COM][8])

---

## 9. AI（Copilot / Codex）に雛形を出させるコツ 🤖✨

AIに任せやすいのは「形」！でも **トランザクション境界**は最後に人間が確定するよ ✅👀

## 使える指示例（コピペOK）📋💡

* 「EF Coreで Orders と OutboxMessages を同一トランザクションで保存する UseCase を書いて。例外時はロールバックするコードにして。」
* 「CreateExecutionStrategy を使ったリトライを含めて。BeginTransactionAsync と CommitAsync を明示して。」

## AI出力をチェックする “3点セット” ✅✅✅

* `BeginTransactionAsync()` がある？（または SaveChanges 1回で暗黙TXになってる？）
* Orders と Outbox が **同じトランザクション内**？
* Commit まで行ってる？（例外時は Commit しない？）

---

## 10. ミニ演習 🧪🏃‍♀️

## 演習1：成功パターンを作る ✅

1. `/orders` を呼ぶ（SimulateCrash=false）
2. Orders と OutboxMessages が 1件ずつ増えるのを確認 👀✨

## 演習2：クラッシュ注入 😈💥

1. `/orders` を呼ぶ（SimulateCrash=true）
2. Orders と OutboxMessages が **増えてない**のを確認 🎯

## 演習3：Type を “バージョン付き” にしてみる 🏷️

* `"OrderCreated.v1"` を `"OrderCreated.v1"` のままでもOK
* 余裕があれば `"OrderCreated.v2"` を想像して、将来の変更を意識してみる🙂🧠
  （次章で Payload 設計に入るよ！）

---

## 11. よくあるミス集（先に潰す）💣🧯

* ❌ Orders 保存してから Outbox 保存を別処理にした
  → ✅ **同一トランザクション**に入れる
* ❌ SaveChanges を2回に分けて、トランザクションを張ってない
  → ✅ `BeginTransactionAsync()` で囲む
* ❌ try/catch で握りつぶして Commit しちゃう
  → ✅ 例外時は **Commitしない**（＝ROLLBACK）

---

## まとめ 🎀✨

この章でできたこと👇

* 🛒 Orders と 📦 OutboxMessages を
* 🔒 **同一トランザクションで一緒に書く**
* 😈 クラッシュ注入しても **ズレが発生しない**のを確認できた

次は **Payload（JSONの中身）をどう設計するか**（第13章）で、運用っぽさが一気に上がるよ 🧾📏✨

[1]: https://chatgpt.com/c/6980e20a-6580-83a3-91dc-57f54b4e0848 "トランザクション超入門"
[2]: https://chatgpt.com/c/697af19c-84cc-8320-bcea-5f6a526ccb70 "冪等性とOutbox設計"
[3]: https://chatgpt.com/c/6978e7cd-c504-8321-a4a7-b7c5ab8ec440 "New chat"
[4]: https://chatgpt.com/c/696fcd75-0f54-8324-8b0e-259fce1014db "第23章 Outbox実装"
[5]: https://chatgpt.com/c/6980e64a-cb40-83a8-8567-682441d7f7aa "Outboxパターン概要"
[6]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14?utm_source=chatgpt.com "What's new in C# 14"
[7]: https://learn.microsoft.com/en-us/ef/core/what-is-new/ef-core-10.0/whatsnew?utm_source=chatgpt.com "What's New in EF Core 10"
[8]: https://techcommunity.microsoft.com/blog/sqlserver/sql-server-2025-is-now-generally-available/4470570?utm_source=chatgpt.com "SQL Server 2025 is Now Generally Available"
