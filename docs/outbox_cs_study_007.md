# 第07章：Outboxパターンの全体像（登場人物紹介）🗺️👥

## 今日のゴール 🎯✨

この章の終わりに、あなたがこう言えたら勝ちです👇

* 「Outboxって、**“発送待ち箱”**をDBに作るやつだよね📦」
* 「**同じトランザクションで**“業務テーブル更新”と“Outboxに積む”をやるんだよね🔒」
* 「送るのは後で。送る係（Relay）が配達するんだよね🚚📩」

---

## 7.1 Outboxパターンって、ざっくり何？🐣📦

![Outbox Definition Box](./picture/outbox_cs_study_007_outbox_definition_box.png)

Outboxパターンはひとことで言うと…

> **「DB更新」と「外部への通知（メッセージ送信）」がズレないように、
> まず“送る内容”をDBのOutboxテーブルに保存して、後から確実に配達する仕組み」**🛡️

この考え方は、分散システムで“確実にイベントを届けたい”ときの定番として整理されています。([Microsoft Learn][1])

---

## 7.2 登場人物（この章の主役たち）👥✨

![Outbox Cast Characters](./picture/outbox_cs_study_007_cast_characters.png)

## ① 業務テーブル（例：Orders）🧾🛒

ふつうのアプリが持つ「本命のデータ」だよ〜

* 注文、会員、支払い、在庫…みたいなやつ！

## ② Outboxテーブル（発送待ち箱）📦📮

「**あとで送る用の封筒**」を入れておく箱。
ここに入るのは、だいたいこんな情報👇

* OutboxId（箱の整理番号）🪪
* Type（何の通知？）🏷️
* Payload（中身：JSONなど）🧠
* OccurredAt（いつ起きた？）⏰
* Status（未送信/送信済/失敗…）✅⚠️

## ③ Relay（配送係 / 配達ロボ）🚚🤖

Outboxを定期的に見に行って、未送信を配達する係。
実装としては **Worker / BackgroundService** がすごく相性いいよ〜🧑‍💻
（Hosted Serviceでバックグラウンド処理を書くのが定番、って公式でも説明されてるよ）([Microsoft Learn][2])

## ④ 送信先（外の世界）🌍📩

* メッセージブローカー（キュー/トピック）📬
* HTTP API 呼び出し🌐
* メール送信サービス✉️
  …などなど。「アプリの外」だから失敗しやすい子たち😅

---

## 7.3 全体の流れ（ストーリーで覚える）📚✨

![Outbox Overview](./picture/outbox_cs_study_007_outbox_overview.png)

## ✅ ステップ0：事件は「業務処理」から起きる

例）「注文が作られた！」🛒✨

## ✅ ステップ1：同じトランザクションで “2つ” 書く 🔒🍙

![Step 1 Dual Write](./picture/outbox_cs_study_007_step1_dual_write.png)

* Orders に注文を保存🧾
* Outbox に「注文作成イベント」を積む📦

ここがOutboxの**心臓**だよ🫀
「片方だけ成功」が起きにくくなるのがポイント！

## ✅ ステップ2：Relayが後でOutboxを見に行く 👀⏱️

未送信（Pending）を探して…

## ✅ ステップ3：外へ配達する 🚚📩

送信できたら…

## ✅ ステップ4：Outboxを“送信済”にする ✅

（失敗したら、失敗として記録してリトライへ…は後の章で！🧯）

---

## 7.4 文字で見る「超ミニ図解」🖼️➡️🧠

![Relay Process Loop](./picture/outbox_cs_study_007_relay_process_loop.png)

```text
(同じDBトランザクション)
[OrdersにINSERT/UPDATE]  +  [OutboxにINSERT(Pending)]  ✅

(後で別プロセス/別スレッド)
RelayがOutbox(Pending)を取得 → 外部へ送信 → OutboxをSentに更新 ✅
```

---

## 7.5 最小のテーブル案（雰囲気つかむ用）🧱📦

![Table Schema Visual](./picture/outbox_cs_study_007_table_schema_visual.png)

※あとで「設計章」でガッツリやるけど、今は“雰囲気”だけ！

```sql
CREATE TABLE OutboxMessages (
    Id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
    Type NVARCHAR(200) NOT NULL,
    Payload NVARCHAR(MAX) NOT NULL,
    OccurredAt DATETIME2 NOT NULL,
    Status INT NOT NULL,          -- 0:Pending, 1:Sent, 2:Failed など
    SentAt DATETIME2 NULL,
    Error NVARCHAR(MAX) NULL
);

CREATE INDEX IX_OutboxMessages_Status_OccurredAt
ON OutboxMessages (Status, OccurredAt);
```

---

## 7.6 「同じトランザクションで2つ書く」って、C#だとどんな感じ？🔒✍️

## 例：注文作成＋Outbox積み（概念サンプル）🛒📦

（EF Core 10は .NET 10 とセットで動くよ、って公式に書かれてるよ）([Microsoft Learn][3])
（.NET 10 は 2025-11-11 リリースのLTSだよ）([Microsoft][4])

```csharp
public async Task<Guid> CreateOrderAsync(CreateOrderCommand cmd, CancellationToken ct)
{
    var orderId = Guid.NewGuid();
    var outboxId = Guid.NewGuid();

    await using var tx = await _db.Database.BeginTransactionAsync(ct);

    // ① 業務テーブル更新（本命）
    _db.Orders.Add(new Order
    {
        Id = orderId,
        CustomerId = cmd.CustomerId,
        TotalPrice = cmd.TotalPrice,
        CreatedAt = DateTimeOffset.UtcNow
    });

    // ② Outboxに「送る内容」を積む（発送待ち箱）
    _db.OutboxMessages.Add(new OutboxMessage
    {
        Id = outboxId,
        Type = "OrderCreated.v1",
        Payload = System.Text.Json.JsonSerializer.Serialize(new
        {
            OrderId = orderId,
            cmd.CustomerId,
            cmd.TotalPrice
        }),
        OccurredAt = DateTimeOffset.UtcNow,
        Status = OutboxStatus.Pending
    });

    await _db.SaveChangesAsync(ct);

    await tx.CommitAsync(ct);

    return orderId;
}
```

ここでの大事ポイントはこれ👇✨

* **Orders と Outbox を “同じ tx” で確定してる**🔒
* だから「注文は保存できたけど通知は消えた😱」が起きにくい！

---

## 7.7 Relay（配送係）の“頭の中”🧠🚚

Relayはだいたいこんなことをぐるぐるしてます👇

1. Pendingを一定件数だけ取る📦
2. 送る📩（HTTP/キューなど）
3. 成功したら Sent にする✅
4. 失敗したら Failed にして理由を残す⚠️（→次でリトライ）

Hosted Service / BackgroundService でバックグラウンド処理を書くのが王道だよ〜([Microsoft Learn][2])
それを **Windows Serviceとして動かす**やり方も公式でまとまってるよ🪟([Microsoft Learn][5])

---

## 7.8 よくある勘違い（ここで潰しとこ！）🧨😺

## ❌ 勘違い1：「Outboxはメッセージを直接“送る仕組み”でしょ？」

![Misunderstanding Direct Send](./picture/outbox_cs_study_007_misunderstanding_direct_send.png)

👉 ちがうよ〜！
Outboxは **“送るための記録を残す箱”**📦
送るのはRelay（配送係）🚚

## ❌ 勘違い2：「業務DBとは別DBにOutboxを置いてもいい？」

👉 初心者のうちは **同じDB** が安心！
「同じトランザクション」が効かなくなると、ズレ防止の力が弱まっちゃう😭

## ❌ 勘違い3：「Relayは1台だけ動く前提でいいよね？」

👉 うっかり二重起動👯すると、同じPendingを2回触ることがあるよ〜
（このへんは後の章で“重複・冪等性”につながるよ🧷）

---

## 7.9 ミニ演習（5分）⏱️🧪

## 演習A：Outboxが“発送待ち箱”っぽいのを確認📦👀

1. 注文作成を1回実行🛒
2. DBで OutboxMessages を見てみる👀
3. Pending が増えてたらOK✅

## 演習B：外部送信が落ちても“記録が残る”のを想像💭🧯

* Relayの送信部分だけ例外を投げる（throw）ようにしてみて、
  Outboxに Failed と Error が残るイメージを持とう⚠️
  （実装は後の章で丁寧にやるよ）

---

## 7.10 Copilot / Codex に頼むときの“良い聞き方”🤖💡

そのままコピペで使えるやつ置いとくね👇✨

* 「EF Coreで OutboxMessages テーブル用の Entity と DbContext 設定例を書いて」🧩
* 「BackgroundServiceで“5秒ごとにPendingを10件取得して送る”雛形を書いて」⏱️🚚
* 「SQL Serverで Pendingを取り出すクエリ例（ロック競合が少ないやつ）を提案して」🔍
* 「送信成功したOutboxをSentに更新する処理の例外パターンを列挙して」🧯

※ただし、**トランザクション範囲**と**二重起動対策**は人間が最終チェックね👀✅

---

## まとめ（この章で覚える合言葉）🔑✨

* Outbox＝**発送待ち箱**📦
* 同じトランザクションで **業務更新＋Outbox積み**🔒
* 送るのは後で、**Relay（配送係）** がやる🚚📩
* ここから先で「テーブル設計」「Relay実装」「冪等性」「リトライ」に育てていくよ🌱

[1]: https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-outbox-cosmos?utm_source=chatgpt.com "Transactional Outbox pattern with Azure Cosmos DB"
[2]: https://learn.microsoft.com/en-us/aspnet/core/fundamentals/host/hosted-services?view=aspnetcore-10.0&utm_source=chatgpt.com "Background tasks with hosted services in ASP.NET Core"
[3]: https://learn.microsoft.com/en-us/ef/core/what-is-new/ef-core-10.0/whatsnew?utm_source=chatgpt.com "What's New in EF Core 10"
[4]: https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core?utm_source=chatgpt.com "NET and .NET Core official support policy"
[5]: https://learn.microsoft.com/en-us/dotnet/core/extensions/windows-service?utm_source=chatgpt.com "Create Windows Service using BackgroundService - .NET"
