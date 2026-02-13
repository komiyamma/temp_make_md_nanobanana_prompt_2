# 第09章：Outboxテーブル設計（ミニマム版）📦🧱

## この章のゴール 🎯✨

Outboxパターンの「箱」になる **Outboxテーブル**を、まずは **最小構成（4項目）**で作れるようになることです😊
この箱に「あとで送る通知」を安全に積めると、**DB更新と通知送信のズレ**が起きにくくなります📮🛡️（この考え方自体がTransactional Outboxの中心です）([Microsoft Learn][1])

---

## 1) ミニマム設計：まずはこの4つだけ！✅📦

![Minimum Outbox Table](./picture/outbox_cs_study_009_minimum_table.png)

最初はこれでOKです👇✨

* **Id**：Outboxレコードの一意ID 🪪
* **Type**：メッセージ種類（何の通知？）🏷️
* **Payload**：中身（JSON文字列）🧾
* **OccurredAt**：いつ起きた？（UTC推奨）⏰🌍

> 「未送信/送信済」みたいな状態管理は、第10章で“運用目線”として強化します🧹🔍
> 第9章は **“積める箱を作る”**がゴールです😊📦

---

## 2) カラム設計のコツ（初心者向け）🧠💡

## 2.1 Id（主キー）🪪✨

![GUID Concept](./picture/outbox_cs_study_009_guid_concept.png)

**おすすめ：GUID（uniqueidentifier）**

* アプリ側でIDを作れて便利😊
* 後で「このOutboxを送った？」の照合にも使いやすい（冪等性のキーにもなりがち）🔁🧷

💡ポイント：Idは **絶対に重複しない**が正義です👑

---

## 2.2 Type（種類）🏷️📌

**例：**

* `OrderCreated`
* `UserRegistered`
* `PaymentFailed`

💡コツ：Typeは「何が起きたか」が分かる短い名前にすると、後でログや調査がラクです🔍✨
（バージョン管理は第14章で扱うので、この章では気にしすぎなくてOK🙆‍♀️）

---

## 2.3 Payload（中身）🧾📏

![Payload JSON](./picture/outbox_cs_study_009_payload_json.png)

最初は **JSON文字列をそのまま保存**でOKです😊
SQL Serverなら、JSONは **nvarchar(max)** などの文字列に入れるのが一般的です([Microsoft Learn][2])

💡コツ（大事）：

* **必要最小限**だけ入れる👼
* 個人情報（住所・カード・生のメール本文など）を詰め込みすぎない🙈💦
* 迷ったら「参照IDだけ送る」も強い（例：`OrderId`だけ）🔗✨

✅おまけ：SQL Serverでは `ISJSON()` で「ちゃんとJSONか」をチェック制約にできます🧱([Microsoft Learn][3])

---

## 2.4 OccurredAt（発生時刻）⏰🌍

![UTC Time](./picture/outbox_cs_study_009_utc_time.png)

**おすすめ：UTC（世界標準）**

* サーバーや環境が増えたときに事故りにくい😇
* 並べ替え（古い順に配送）がやりやすい📬➡️📬

SQL Serverなら `SYSUTCDATETIME()` をデフォルトにできます✨（後で便利）

---

## 3) SQL Serverの最小DDL例（コピペOK）🧩🗄️

```sql
CREATE TABLE dbo.OutboxMessages (
    Id         uniqueidentifier NOT NULL,
    Type       nvarchar(200)     NOT NULL,
    Payload    nvarchar(max)     NOT NULL,
    OccurredAt datetime2(7)      NOT NULL CONSTRAINT DF_OutboxMessages_OccurredAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_OutboxMessages PRIMARY KEY (Id)
);

-- お好み：PayloadがJSONであることを保証したいなら（SQL Server）
ALTER TABLE dbo.OutboxMessages
ADD CONSTRAINT CK_OutboxMessages_Payload_IsJson CHECK (ISJSON(Payload) = 1);
```

📝メモ：

* `nvarchar(max)` は最大2GBまでのJSONを保持できます（ただし巨大Payloadはおすすめしません😅）([Microsoft Learn][2])
* JSONチェック制約を入れると「壊れたJSON」が混ざりにくくなって安心です🛡️([Microsoft Learn][3])

---

## 4) EF Core用：C#モデル（最小）🧑‍💻✨

![EF Core Mapping](./picture/outbox_cs_study_009_ef_core_mapping.png)

```csharp
public sealed class OutboxMessage
{
    public Guid Id { get; init; }
    public string Type { get; init; } = "";
    public string Payload { get; init; } = "";
    public DateTime OccurredAt { get; init; } // UTC推奨
}
```

## マッピング例（Fluent API）🧩

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

public sealed class OutboxMessageEntityTypeConfiguration : IEntityTypeConfiguration<OutboxMessage>
{
    public void Configure(EntityTypeBuilder<OutboxMessage> b)
    {
        b.ToTable("OutboxMessages", "dbo");

        b.HasKey(x => x.Id);

        b.Property(x => x.Type)
            .HasMaxLength(200)
            .IsRequired();

        b.Property(x => x.Payload)
            .IsRequired();

        b.Property(x => x.OccurredAt)
            .HasColumnType("datetime2(7)")
            .IsRequired();
    }
}
```

✅補足：本日時点の最新系では **.NET 10 / EF Core 10** が「2026の前提」として自然です（LTS）([Microsoft Learn][4])

---

## 5) ミニ演習：Outboxテーブルを作って眺める👀🛠️

## ステップ1：テーブル作成🧱

* 上のDDLを実行（またはEF Core Migrationで作成）✅

## ステップ2：1件だけ手で積む📦

```sql
INSERT INTO dbo.OutboxMessages (Id, Type, Payload)
VALUES (
    NEWID(),
    N'OrderCreated',
    N'{"orderId":"A-1001","total":3980}'
);
```

## ステップ3：並び替えて見てみる👀✨

```sql
SELECT TOP (50) *
FROM dbo.OutboxMessages
ORDER BY OccurredAt DESC;
```

🎉見えたら勝ち！
「通知の材料」が **DBの中に安全に積まれた**状態です📦✨

---

## 6) よくあるミス集（先に潰す）💥🧯

* **Payloadに全部入れちゃう**（巨大JSON）📦💣
  → 後で重くて地獄になりがち😇
* **ローカル時刻で保存して混乱**⏰😵‍💫
  → UTCに寄せると安心🌍
* **Typeがフワッとして後で判別不能**🏷️❓
  → 「何が起きたか」が読める名前に📌
* **Outboxを別DBに置く**🗄️➡️🗄️
  → 同一トランザクションの旨みが消えやすいので注意（Outboxの基本は同じ更新の中で積むこと）([Microsoft Learn][1])

---

## 7) AI（Copilot/Codex）に頼むときのプロンプト例🤖💬

「雛形はAI」「判断は人間」が安全です✅👀
（特に **カラム型・制約・時刻の扱い**は要チェック！）

```text
EF Core 10 / SQL Server 前提で OutboxMessages テーブルを作りたいです。
最小構成で Id(Guid), Type(string 200), Payload(string), OccurredAt(datetime2 UTC default) を含む
Entityクラス、Fluent API設定、Migrationのイメージを出してください。
PayloadはJSON文字列で、可能ならISJSONのチェック制約案もください。
```

---

## 8) 理解チェック（ミニクイズ）📝✨

1. Outboxの「ミニマム4カラム」は何？📦
2. OccurredAtはなぜUTCが便利？🌍
3. Typeは何のためにある？🏷️
4. Payloadを巨大にしすぎると何が困る？📏💦
5. SQL Serverで「PayloadがJSON」を守る仕組みは？🧱

---

## まとめ 🎀

* 第9章は **Outboxの“箱”を最小構成で作る**章です📦✨
* **Id / Type / Payload / OccurredAt** の4つでスタートすればOK✅
* JSONは `nvarchar(max)` に入れて、必要なら `ISJSON()` で守ると安心🛡️([Microsoft Learn][2])
* 次章（第10章）で、StatusやRetryCountなど **運用で困らない強化版**に進みます🔍🧹

[1]: https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-outbox-cosmos?utm_source=chatgpt.com "Transactional Outbox pattern with Azure Cosmos DB"
[2]: https://learn.microsoft.com/en-us/sql/relational-databases/json/store-json-documents-in-sql-tables?view=sql-server-ver17&utm_source=chatgpt.com "Store JSON Documents - SQL Server"
[3]: https://learn.microsoft.com/ja-jp/azure/azure-sql/database/json-features?view=azuresql&utm_source=chatgpt.com "JSON データの操作 - Azure SQL Database & ..."
[4]: https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/overview?utm_source=chatgpt.com "What's new in .NET 10"
