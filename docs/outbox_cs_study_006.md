# 第06章：イベントとメッセージの超入門 📩✨

## 今日のゴール 🎯

* 「イベント」と「コマンド（命令）」の違いを、言葉で説明できるようになる🗣️✨
* 「メッセージって何？」を “封筒＋中身” のイメージでつかむ✉️📦
* キュー／Pub/Sub（トピック）で何が変わるか、ざっくり分かる🚚📮

---

## 6-1. まず「メッセージ」って何？✉️💌

![Message Envelope Metaphor](./picture/outbox_cs_study_006_message_envelope_metaphor.png)

**メッセージ**は、ざっくり言うと

> 「別の場所（別プロセス/別サービス）に渡す “情報のかたまり”」
> だよ〜😊✨

ポイントはこれ👇

* メッセージは、**相手のメモリに直接触れない**（別世界に送る）🌍
* だから、**送るための形**（JSONなど）にして、**運ぶ仕組み**（HTTP/キューなど）に乗せる📦➡️🚚

---

## 6-2. 「イベント」と「コマンド（命令）」の違い 🧠⚡

## ✅ 超ざっくり結論

* **コマンド**： 「これやって！」（意図・お願い）🫵📣
* **イベント**： 「これ起きたよ！」（事実・報告）📰✨

この切り分けは、MicrosoftのAzure Architectureガイドでも、
「アクションを期待するなら command、起きた事実を伝えるなら event」って整理されてるよ。([Microsoft Learn][1])

## 例で見るとわかりやすい🍰

* コマンド（命令）🫵

  * `PlaceOrder`（注文して！）🛒
  * `ReserveStock`（在庫確保して！）📦
* イベント（事実）📰

  * `OrderPlaced`（注文が作られた）🎉
  * `StockReserved`（在庫が確保された）✅

## 「宛先が決まってる？」が大きな違い👀

* コマンド：だいたい **宛先がはっきり**（この係にやってほしい）🎯
* イベント：だいたい **宛先は固定しない**（知りたい人が受け取る）📣👂👂👂

---

## 6-3. 図でつかむ：コマンドとイベントの“空気感”🖼️✨

![Command vs Event](./picture/outbox_cs_study_006_cmd_vs_event.png)

```text
（コマンド） 送り手 →「やって！」→ 受け手（たいてい特定の1つ）
（イベント） 送り手 →「起きたよ！」→ 受け手（必要な人たちが複数でもOK）
```

---

## 6-4. 「どう運ぶ？」3つの代表ルート 🚚📡

## ① HTTP（同期っぽくなりやすい）🌐

![Transport Types](./picture/outbox_cs_study_006_transport_types.png)

* 送ってすぐ返事がほしい時に使いがち🙋‍♀️
* ただし、相手が落ちてると困る…😵‍💫

## ② キュー（Queue）📥

![Queue One-to-One](./picture/outbox_cs_study_006_queue_one_to_one.png)

* 「箱に入れておく→誰かが取りに来る」スタイル📦➡️📥
* 重要ポイント：**1つのメッセージは基本“誰か1人”が処理**（負荷分散しやすい）🏃‍♀️🏃‍♂️
* これはAzure Service Busの説明でも「queueはsingle consumer」って整理されてるよ。([Microsoft Learn][2])
* 一般的な説明としても、キューはpoint-to-point（1対1）って語られることが多いよ。([IBM][3])

## ③ Pub/Sub（トピック＋購読）📣📰

![Pub/Sub Megaphone](./picture/outbox_cs_study_006_pubsub_megaphone.png)

* 「掲示板に貼る→見たい人が各自見る」スタイル📌👀
* 重要ポイント：**同じメッセージが“購読者それぞれ”に配られる**（1対多）👂👂👂
* Azure Service Busでも「topics/subscriptionsはone-to-many」って書いてあるよ。([Microsoft Learn][2])

---

## 6-5. メッセージは「封筒（メタデータ）＋中身（Payload）」が基本 ✉️📦

![Envelope and Payload Structure](./picture/outbox_cs_study_006_envelope_payload_structure.png)

## 💡封筒（メタデータ）でよく使うもの

* `messageId`：このメッセージのID🪪
* `type`：何のメッセージ？（例：`OrderPlaced`）🏷️
* `occurredAt` / `requestedAt`：いつ起きた/頼んだ？⏰
* `correlationId`：一連の流れをつなぐ糸🧵（例：注文作成〜通知まで同じID）
* `traceId`：観測（ログ追跡）用のID🔎

## 📦中身（Payload）のイメージ

* 「必要な情報だけ」を入れるのがコツ✨
* 例：注文イベントなら「注文ID・合計金額・顧客ID」くらいからでOK🛒

---

## 6-6. C#で「イベント」「コマンド」を書いてみる ✍️✨

## イベント（起きた事実）📰

```csharp
public sealed record OrderPlaced(
    Guid EventId,
    DateTimeOffset OccurredAt,
    string OrderId,
    string CustomerId,
    decimal TotalAmount
);
```

## コマンド（やって！）🫵

```csharp
public sealed record PlaceOrder(
    Guid CommandId,
    DateTimeOffset RequestedAt,
    string CustomerId,
    IReadOnlyList<LineItem> Items
);

public sealed record LineItem(string ProductId, int Quantity);
```

### ✨命名のちょいコツ（初心者向け）

* コマンド：動詞っぽい（`PlaceOrder` / `ReserveStock`）🏃‍♀️
* イベント：過去形っぽい（`OrderPlaced` / `StockReserved`）📅

---

## 6-7. ミニ演習：イベントをJSONにして「メッセージっぽさ」を体験しよ🧪💕

![JSON Message Flying](./picture/outbox_cs_study_006_json_message_fly.png)

## やること ✅

1. `OrderPlaced` を作る
2. JSONにして表示する
3. “別世界に渡す形になった！”を感じる✨

```csharp
using System.Text.Json;

public sealed record OrderPlaced(
    Guid EventId,
    DateTimeOffset OccurredAt,
    string OrderId,
    string CustomerId,
    decimal TotalAmount
);

var ev = new OrderPlaced(
    EventId: Guid.NewGuid(),
    OccurredAt: DateTimeOffset.UtcNow,
    OrderId: "ORD-20260203-0001",
    CustomerId: "CUST-0007",
    TotalAmount: 3980m
);

var json = JsonSerializer.Serialize(ev, new JsonSerializerOptions
{
    WriteIndented = true,
    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
});

Console.WriteLine(json);
```

出力がそれっぽくなったら成功〜！🎉✨
（このJSONが、キューやHTTPに乗って飛んでいくイメージだよ📦➡️🚚）

---

## 6-8. Outboxとどうつながるの？📦🔗

Outboxではだいたいこうなるよ👇

* **業務DBの更新**と同時に、**「イベント（または送るべきメッセージ）」をDBに記録**する📝
* あとから配送係（Relay/Worker）が拾って、外に送る🚚📩

つまり第6章の理解は、
**「Outboxに何を積むの？」＝イベント/メッセージの正体**
につながっていくよ✨

---

## 6-9. ありがち勘違いQ&A 🙋‍♀️💭

## Q1. 「イベント＝通知」って思っていい？📣

半分OK！🙂
でも本質は「通知」より **“事実の記録（何が起きたか）”** が中心だよ📰✨

## Q2. コマンドもキューで送っていい？📥

いいよ〜！🙆‍♀️
「同期/非同期」は運び方の話で、**コマンド/イベントは意味の話**だよ🧠✨
（Azureのガイドでも、非同期メッセージングの文脈でcommand/eventを整理してるよ。([Microsoft Learn][1])）

## Q3. イベントって“絶対1回だけ届く”の？🥺

残念、現実はだいたい **「最低1回（重複あり得る）」** が多いよ😵‍💫
だから後の章で「冪等性（2回来ても1回分）」が大事になるの🧷✨

---

## 6-10. 豆知識：今どきの“イベントの名札”📛✨

![CloudEvents Badge](./picture/outbox_cs_study_006_cloudevents_badge.png)

イベントって、システムごとに形がバラバラだとしんどい…😭
そこで **CloudEvents** みたいに「イベントに共通のメタデータを持たせよう」っていう仕様もあるよ✉️✨
（CNCFのプロジェクトとして整理されてるよ。）([CNCF][4])

---

## 6-11. ちいさな確認テスト ✅🌸

* 「注文して！」は **コマンド** / 「注文が作られた」は **イベント** 🫵📰
* キューは基本 **1つのメッセージを誰か1人が処理** 📥([Microsoft Learn][2])
* Pub/Subは **同じメッセージが購読者それぞれに配られる** 📣([Microsoft Learn][2])
* メッセージは **封筒（メタデータ）＋中身（Payload）** ✉️📦

---

## 参考：2026時点の開発の“旬”メモ🗓️✨

* 現行の.NETは **.NET 10（LTS）** がリリース済みで、サポートも長めだよ。([Microsoft][5])
* C#も **C# 14** の情報が公開されてるよ。([Microsoft Learn][6])
* ツール面だと、.NET 10と一緒に **Visual Studio 2026** なども案内されてるよ。([Microsoft for Developers][7])

（この章では“意味の理解”が主役なので、ここは軽く眺めるだけでOKだよ😊✨）

[1]: https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/messaging?utm_source=chatgpt.com "Asynchronous messaging options - Azure Architecture ..."
[2]: https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-queues-topics-subscriptions?utm_source=chatgpt.com "Azure Service Bus Queues, Topics, and Subscriptions"
[3]: https://www.ibm.com/think/topics/message-queues?utm_source=chatgpt.com "What Is a Message Queue? | IBM"
[4]: https://www.cncf.io/projects/cloudevents/?utm_source=chatgpt.com "CloudEvents | CNCF"
[5]: https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core?utm_source=chatgpt.com "NET and .NET Core official support policy"
[6]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14?utm_source=chatgpt.com "What's new in C# 14"
[7]: https://devblogs.microsoft.com/dotnet/announcing-dotnet-10/?utm_source=chatgpt.com "Announcing .NET 10"
