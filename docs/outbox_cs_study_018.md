# 第18章：到達保証の話（Outboxはだいたい“At-least-once”）📬🔁

## この章でわかること 🎯✨

* 「最低1回は送る」ってどういう意味か（そして、なぜ重複するのか）😅
* 「送れたかどうか、実は曖昧」問題の正体 🤷‍♀️
* Outboxを採用したときに、**どこで重複が生まれるか**を絵で説明できるようになる 🖼️
* 次章の「冪等性」が、なぜ“必須科目”になるのかが腑に落ちる 🧠💡

---

## 1. 配達保証の3兄弟 📦👨‍👩‍👧‍👦

![Delivery Types](./picture/outbox_cs_study_018_delivery_types.png)

メッセージ配達の世界には、ざっくり3つの「保証レベル」があるよ〜😊✨

## 1) At-most-once（最大1回）🎯

* **重複は起きない**（嬉しい）🙆‍♀️
* でも **落ちたら終わり**（配達されない可能性がある）😇

## 2) At-least-once（最低1回）📬

* **落とさない**方向に寄せる（嬉しい）🛡️
* ただし **重複は起こり得る**（現実）👯

## 3) Exactly-once（ちょうど1回）🏆

* 夢のように見えるけど、**エンドツーエンドで本当にやるのは難しい**💦
* だいたいは「システムとアプリが協力して、結果的に“そう見せる”」方向に落ち着くよ〜🧩

RabbitMQの公式ドキュメントでも、**ack（受領確認）を使うと at-least-once になり、使わないと at-most-once になる**という整理が書かれてるよ。([rabbitmq.com][1])

---

## 2. Outboxが狙う保証はどれ？🎯📦

Outboxの基本ゴールは、超シンプルに言うとこれ👇

* ✅ **業務DBの更新がコミットされたなら、その通知も“いつか必ず”外に出る**
* ❌ でも、**“1回だけ”を完全保証する仕組みではない**

つまり Outbox は、だいたい **at-least-once** の世界観で設計されることが多いよ〜📬🔁

「DB更新とメッセージ送信を同時に原子的にやりたいけど、DBとブローカーをまたぐ分散トランザクション（2PC）は現実的じゃない」…って背景が、Transactional Outboxの前提としてよく語られるポイントだよ。([microservices.io][2])

---

## 3. 「最低1回」は、なぜ重複するの？👯💥

![At Least Once](./picture/outbox_cs_study_018_at_least_once.png)
![Ack Lost Bridge](./picture/outbox_cs_study_018_ack_lost_bridge.png)

ここが超大事〜！！！😺✨
重複が起きる理由は、だいたい **“失敗したように見える”** からだよ。

## 典型パターン：送れたのに、送れてないように見える 🤯

イメージ図いくね👇

```text
Relay（配送係）             ブローカー/送信先
   |   send(msg)  -------------------->  |  (実は受け取って保存した)
   |                                     |
   |   (ACK待ち)                         |
   |   ・・・ネットワークが途切れる・・・ |
   |  Timeout!（失敗だと思う）           |
   |                                     |
   |   retry send(msg) ----------------> |  (同じmsgがまた届く)
```

* ブローカー側は受け取ってる ✅
* Relay側はACKが返らなくて「失敗した」と判断 ❌
* だから再送して **重複** 👯

これ、めちゃ普通に起こるよ〜😅

---

## 4. 「送れたかどうか」は意外と曖昧 🤷‍♀️🌀

![Schrodinger's ACK](./picture/outbox_cs_study_018_schrodingers_ack.png)

送信処理って、結果がだいたい3種類あるのね👇

## A. 成功が確定 ✅

* ACKも返ってきた
* 送信先が「受け取った」と言ってる

## B. 失敗が確定 ❌

* 認証エラー、リクエスト不正、宛先不存在…など
* 直してからじゃないと永遠に成功しないタイプ 😇

## C. **不明（グレー）🤷‍♀️** ← ここが主役

* タイムアウト
* 接続が切れた
* 返事が来る前にプロセスが落ちた
* 送信先が受け取ったかどうか、こちらからは確定できない

そして **at-least-once** を取りに行く設計は、
この「不明」を **“成功してたかもしれないけど、とにかく再送する”** に倒すのが基本なんだ〜📬🔁

---

## 5. Outboxで重複が生まれる“穴”はここ 🕳️👀

![Crash Runner](./picture/outbox_cs_study_018_crash_runner.png)

Outboxはざっくり二段階だよね👇

1. 業務テーブル更新＋Outbox行追加（同一トランザクション）🔒
2. RelayがOutboxを読んで外へ送信し、Outboxを送信済みにする 🚚📩

この **2)** が、どうしても「穴」になるよ〜😅

## 重複が生まれる王道シナリオ 🥲

* Relayが外部へ送信 ✅
* でも「Outboxを送信済みに更新する」前に落ちる 💥
* 次回起動でまた同じOutboxを拾って再送 👯

これってつまり、
**外部送信** と **Outbox行の状態更新** を“完全に同時”にはできない（外部はDBトランザクションに入らない）からだよね🤝

---

## 6. 「じゃあExactly-onceって無理なの？」への現実的な答え 🧠✨

![Azure Duplicate Detection](./picture/outbox_cs_study_018_azure_duplicate_detection.png)

エンドツーエンド（DB更新＋外部副作用まで含めて）で「ちょうど1回」をやるのは難しい、ってのが基本姿勢だよ〜💦
たとえばKafkaの設計ドキュメントでも、Exactly-onceには「消費位置と出力の協調（必要なら2PC的な話）」が絡む、というニュアンスが説明されてるよ。([kafka.apache.org][3])

ただし！
「特定の範囲では重複排除できる」機能は存在するよ〜🙌

## 例：Azure Service Bus の重複検出 🧽✨

Azure Service Bus は、MessageId の履歴を一定期間保持して、同じIDのメッセージを落とす「重複検出」があるよ。
ドキュメント上も「設定した時間窓の中で exactly once delivery を保証する」と書いてある。([Microsoft Learn][4])

でもね、ここが超ポイント👇

* ブローカー側で落としてくれても、アプリ側の副作用（DB更新や外部API呼び出し）を全部“ちょうど1回”にするには、結局アプリ設計も必要になりがち 😅
* だから「冪等性」はやっぱり重要になるよ〜🧷✨

---

## 7. ミニ実験：重複が“自然に”起きるのを体感しよう 🧪👯

![Flaky Dice Publisher](./picture/outbox_cs_study_018_flaky_dice.png)

本物のブローカーを使わなくても、「ACKが消える」を疑似的に作ると理解が爆速だよ〜🚀

## 7.1 偽のPublisherを作る 🤖📩

```csharp
public interface IEventPublisher
{
    Task PublishAsync(Guid outboxId, string payloadJson, CancellationToken ct);
}

// 「実は送れてるのに、たまにタイムアウトする」やつ😈
public sealed class FlakyPublisher : IEventPublisher
{
    private readonly Random _rng = new();

    public Task PublishAsync(Guid outboxId, string payloadJson, CancellationToken ct)
    {
        Console.WriteLine($"📨 SEND  outboxId={outboxId}");

        // 40%の確率で「ACKが返らなかった」ことにする（=送れたか不明🤷‍♀️）
        if (_rng.NextDouble() < 0.4)
        {
            Console.WriteLine($"⚠️  ACK LOST  outboxId={outboxId}");
            throw new TimeoutException("Ack timeout (simulated)");
        }

        Console.WriteLine($"✅ ACK OK  outboxId={outboxId}");
        return Task.CompletedTask;
    }
}
```

## 7.2 Relay側はどう動くべき？🚚🔁

* タイムアウトしたら「失敗扱い」でリトライ
* すると、同じ outboxId が複数回 SEND されるログが出るよ 👯
* **それが at-least-once のリアル**📬🔁

---

## 8. 実務の合言葉：重複はバグじゃなくて “仕様” 😺📌

Outboxを採用した瞬間、チームの共通認識はこれになるよ👇

* ✅ 「重複は起こる」前提で作る
* ✅ “1回だけに見せる”のは **受け手（または途中）で吸収**する
* ✅ そのための代表選手が **冪等性**🧷✨

---

## 9. 次章につなぐ一言 🧠✨

この章の結論はシンプルだよ〜📌

* Outboxは「落とさない」を取りにいく
* その代償として「重複が起こり得る」
* だから次章のテーマはこうなる👇

👉 **「2回届いても、1回分として扱える」＝冪等性（Idempotency）** ✅🧷

（次章で、OutboxIdを“鍵”にして重複を消す方法をやるよ〜🔑✨）

[1]: https://www.rabbitmq.com/docs/reliability?utm_source=chatgpt.com "Reliability Guide"
[2]: https://microservices.io/patterns/data/transactional-outbox.html?utm_source=chatgpt.com "Pattern: Transactional outbox"
[3]: https://kafka.apache.org/081/design/design/?utm_source=chatgpt.com "Design | Apache Kafka"
[4]: https://learn.microsoft.com/en-us/azure/service-bus-messaging/enable-duplicate-detection?utm_source=chatgpt.com "Enable duplicate message detection - Azure Service Bus"
