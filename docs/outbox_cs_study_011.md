# 第11章：書き込み側の設計（責務分離の形）🧠🧩

## 今日のゴール 🎯✨

この章では、Outboxを使うときの「書き込み側（＝DBに保存する側）」を、**ごちゃ混ぜにしない設計**にします😊🍱
とくにここが大事👇

* ✅ **業務処理（注文を作る等）** と ✅ **Outboxに積む** を混ぜない（SoC：関心の分離）🍱
* ✅ 「イベント（送るネタ）」を **どこで作るか** を迷わない📌
* ✅ 次章（実装）で **同一トランザクション** をきれいに書ける形にする🔒✨

---

## 11-1. まず「書き込み側」で起きがちな事故 😱💥

## ❌ アンチパターン：全部を1か所でやっちゃう

* 注文をDBへ保存📝
* ついでにメッセージ送信（HTTP/Queue）📩
* 失敗したらリトライ…🔁

これ、**Dual Writeの地雷**がそのまま残ります💣😵‍💫
（Outboxは「送信」じゃなくて「積む」までを、DB更新と同じ成功/失敗にするのが目的！）

Outboxの基本の考え方（DB更新とイベントを確実に揃える）は「Transactional Outbox」として定番です。([Microsoft Learn][1])

---

## 11-2. 書き込み側の登場人物（役割の分け方）👥🗺️

![SoC Layers](./picture/outbox_cs_study_011_soc_layers.png)

書き込み側を、ざっくり **3つの箱** に分けます📦📦📦

## ① ユースケース（アプリ層）🧭

* 「注文作成しよう！」の**進行役**🎬
* 何をいつ呼ぶかを決める（オーケストラの指揮者🎻）

## ② ドメイン（業務ルール）🏰

* 「注文とは何か」「そのルールは何か」を守る🛡️
* できれば **インフラ（DB/Queue）を知らない**🙈

## ③ インフラ（DBなど）🛠️

* DBへ保存する人🧑‍🔧
* Outboxテーブルへ保存する人🧑‍🔧

---

## 11-3. SoC（関心の分離）の“3つの約束”🍱✨

## 約束①：ドメインは「送信」を知らない 🙈📩

ドメインは「メッセージ送るぞ！」って考えないでOK🙆‍♀️
ドメインは **事実（起きたこと）** を表現するだけに寄せると、設計が超ラクになります😊

## 約束②：ユースケースは「積む」まで。送信しない 📦🚫

ユースケースは Outbox に **レコードを積む** ところまで。
**送信は配送係（Relay）** に任せる🚚（これは後の章！）

## 約束③：インフラは「保存の実務」。判断しない 🧾

* 保存する ✅
* 取り出す ✅
  でも「どんなOutboxを作るべき？」みたいな判断は、アプリ側に寄せるのが初心者向けで安全です😊👍

---

## 11-4. “イベントを作る場所”を決めよう 📌✨（迷いポイントを解消！）

Outboxで送るネタ（イベント/メッセージ）を **どこで作るか** は悩みがち🌀
結論、初心者はこの順でOKです👇

## パターンA（初心者おすすめ）🌱：アプリ層（ユースケース）で作る

* いちばん分かりやすい😊
* 設計の学習コストが低い📉
* 「Outboxに積む」責務が1か所に集まって見通しが良い👀✨

> この教材の序盤は **Aで進める** のが安全です💖

## パターンB（中級）🌿：ドメインイベントを発生 → アプリ層でOutboxへ変換

* ドメインが「起きた事実」をイベントとして持つ🧠
* アプリ層が「外へ出す用（Integration Event）」に変換して Outbox へ📦

## パターンC（上級）🌳：保存処理のフックで自動収集（Interceptor等）

* 便利だけど魔法っぽくなりやすい🪄
* 初心者がハマる率が上がるので後回し推奨🙅‍♀️

---

## 11-5. 初心者向け・最小の責務分離（これだけ覚えて！）🧩✨

ここからは **パターンA** でいきます🌱

## ✅ 最小構成で出てくるクラス（おすすめ命名つき）🧸

* `CreateOrderUseCase`（ユースケース）🎬

  * 注文を作る
  * Outboxメッセージを作る
  * **保存する（次章で同一トランザクション）**
* `Order`（ドメイン）🛒

  * 注文のルールを守る
* `IOrderRepository`（保存窓口）🗃️
* `IOutboxRepository`（Outbox保存窓口）📦
* `IUnitOfWork`（まとめて確定する係）🔒（次章で活躍！）

---

## 11-6. 依存方向のルール（超やさしく）➡️💞

矢印は「依存（知ってる）」の方向ね😊

* アプリ層 → ドメイン を知ってOK ✅
* インフラ → アプリ層/ドメイン を知ってOK ✅
* ドメイン → インフラ は **知らない** 🚫

これが守れると、後で差し替えが楽になります🔁✨（DIは後の章で！）

---

## 11-7. Outboxに積むデータは「OutboxMessage」という1語にする 🧾📦

書き込み側では、Outboxの1行を **1つの型** として扱うとスッキリします😊✨
（テーブル設計は前の章でやった“ミニマム版”を想定）

```csharp
public sealed record OutboxMessage(
    Guid Id,
    string Type,
    string Payload,
    DateTimeOffset OccurredAt
);
```

* `Type`：イベント名（例：`OrderCreated_v1`）🏷️
* `Payload`：JSON（中身は次章以降でしっかり！）🧾
* `OccurredAt`：起きた日時⏰

---

## 11-8. 「イベント生成」を1か所に寄せる（Factoryでスッキリ）🏭✨

ユースケースがOutboxを作るとき、ベタ書きが増えると読みにくい😵
だから「OutboxMessageを作る責務」も分けちゃうのがオススメです😊

```csharp
public static class OutboxMessageFactory
{
    public static OutboxMessage OrderCreated(Guid orderId, DateTimeOffset now)
    {
        var payload = $$"""
        {"orderId":"{{orderId}}"}
        """;

        return new OutboxMessage(
            Id: Guid.NewGuid(),
            Type: "OrderCreated_v1",
            Payload: payload,
            OccurredAt: now
        );
    }
}
```

ポイント🎀

* **Payloadは最小**（まずはIDだけでOK）🔗
* こうしておくと、後でPayloadが育っても影響が小さい🌱➡️🌳

---

## 11-9. ユースケースの形（“混ぜない”基本フォーム）🧩🧠

「注文を作る」と「Outboxを積む」を、**順序は近く**、でも **責務は別** にします🍱✨

```csharp
public sealed class CreateOrderUseCase
{
    private readonly IOrderRepository _orders;
    private readonly IOutboxRepository _outbox;
    private readonly IUnitOfWork _uow;
    private readonly IClock _clock;

    public CreateOrderUseCase(
        IOrderRepository orders,
        IOutboxRepository outbox,
        IUnitOfWork uow,
        IClock clock)
    {
        _orders = orders;
        _outbox = outbox;
        _uow = uow;
        _clock = clock;
    }

    public async Task<Guid> HandleAsync(CreateOrderCommand cmd, CancellationToken ct)
    {
        var order = Order.Create(cmd.CustomerId, cmd.Items);   // 🏰ドメイン
        await _orders.AddAsync(order, ct);                    // 🗃️保存（準備）

        var now = _clock.Now;
        var msg = OutboxMessageFactory.OrderCreated(order.Id, now); // 📦Outbox生成
        await _outbox.AddAsync(msg, ct);                             // 📦保存（準備）

        await _uow.CommitAsync(ct); // 🔒 次章で「同一トランザクション」の中心になる！
        return order.Id;
    }
}
```

ここでの気持ちいいポイント😍✨

* `Order.Create` は業務ルールだけ🏰
* Outbox生成は `OutboxMessageFactory` に寄せてスッキリ🏭
* 保存はRepositoryへ🗃️📦
* 最後に `CommitAsync` 🔒

---

## 11-10. EF Core を使うときの “地味に大事” 注意点 🧯🧵

次章でトランザクションを扱うときに効いてくる小ネタ✨

## ✅ `DbContext` は同時並行で使わない（超大事）🚫🧵

同じ `DbContext` で並列にクエリ/保存を走らせるのはNGです🙅‍♀️
（awaitをちゃんと待つ、並列処理はDbContextを分ける、など）([Microsoft Learn][2])

---

## 11-11. よくある分離ミス集（チェックリスト）✅🔍

## ❌ ミス1：ユースケースから外部送信しちゃう 📩💥

* HTTPを叩く
* キューにPublishする
  → それ、Outboxの意味が薄れる😵‍💫（配送係へ！🚚）

## ❌ ミス2：ドメインが `IOutboxRepository` を呼び出す 🙈🧨

* ドメインがインフラを知り始めると、芋づる式に設計が崩れがち🌀

## ❌ ミス3：OutboxのType/Payloadが場当たりになる 🧾😵

* せめて **Factoryに寄せる**
* Type命名にルールを作る（例：`OrderCreated_v1`）🏷️

---

## 11-12. ミニ演習：既存の「注文作成」を責務分離してみよう 🛠️🎓✨

## お題📝

今ある `OrderService.Create()` がこうなってるとします👇

* 注文保存
* メール送信
* ログ出力
  ぜんぶ同じメソッド😱

## やること（手順）👣✨

1. メール送信を削除して、代わりに **OutboxMessageを積む** 📦
2. Outbox生成のコードを `OutboxMessageFactory` に移す🏭
3. `CreateOrderUseCase` が「進行役」だけになるように整える🎬

## ゴールの形（合格ライン）🎯

* `CreateOrderUseCase` が **“注文＋Outboxを積む”** までしかやってない✅
* 外部送信ゼロ✅
* ドメインがインフラを知らない✅

---

## 11-13. AI（支援ツール）で早く作るコツ 🤖✨（でも最後は人が守る）

AIに頼むと速いのはここ👇

* 雛形（UseCase/Repository/DTO）生成🧩
* Factoryのテンプレ作成🏭
* チェックリストの洗い出し✅

例：AIへの依頼文（コピペOK）📋✨
（※名前だけ出すね：GitHub / OpenAI / Microsoft ）

```text
C# 14 / .NET 10 の想定で、
Outboxパターンの「書き込み側」だけを責務分離して実装したいです。
CreateOrderUseCase / Order（ドメイン）/ IOrderRepository / IOutboxRepository / IUnitOfWork / OutboxMessageFactory
を用意して、外部送信は一切しない形の雛形コードをください。
```

でも最後に必ず人が見る場所👀🔥

* 「送信してないか？」🚫📩
* 「Outbox生成が散らばってないか？」🧩
* 「依存方向が逆になってないか？」➡️

---

## 11-14. この章のまとめ 🎀✨

* 書き込み側は **“業務処理” と “Outboxに積む” を混ぜない** 🍱✅
* 初心者は **アプリ層（ユースケース）でOutboxMessageを作る** のが最短ルート🌱📌
* `OutboxMessage` と `OutboxMessageFactory` を作ると、設計がスッキリしやすい🏭✨
* 次章では、この形のまま **同一トランザクションで2つ書く** のを実装していくよ🔒👑

---

## 参考（この章の前提として押さえた“最新”の土台）📌✨

* 2026-01-13 時点の .NET 10.0.2 / SDK 10.0.102 と、C# 14.0 の対応関係([Microsoft][3])
* C# 14 は .NET 10 を対象にした最新リリース([Microsoft Learn][4])
* Transactional Outbox の考え方（信頼性あるメッセージングのため）([Microsoft Learn][1])

[1]: https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-outbox-cosmos "Transactional Outbox pattern with Azure Cosmos DB - Azure Architecture Center | Microsoft Learn"
[2]: https://learn.microsoft.com/en-us/dotnet/api/microsoft.entityframeworkcore.infrastructure.databasefacade.begintransactionasync?view=efcore-10.0&utm_source=chatgpt.com "DatabaseFacade.BeginTransactionAsync ..."
[3]: https://dotnet.microsoft.com/en-US/download/dotnet/10.0 "Download .NET 10.0 (Linux, macOS, and Windows) | .NET"
[4]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14 "What's new in C# 14 | Microsoft Learn"
