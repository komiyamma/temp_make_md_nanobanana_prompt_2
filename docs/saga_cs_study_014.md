# 第14章：メッセージの落とし穴（順序・重複・遅延）🕳️😵‍💫

![Reordering numbers 1, 3, 2 -> 1, 2, 3.](./picture/saga_cs_study_014_message_ordering.png)


## この章のゴール🎯✨

* メッセージは **「思った順で届かない」** し、**「同じのが2回届く」** し、**「遅れて届く」** ものだと腹落ちする😇📨
* Sagaで事故が起きるポイント（＝状態がズレる瞬間）を説明できる🧠⚙️
* 対策を **「無視 / 保留 / リトライ / 補償」** に分けて決められる✅🔁

---

## 14.1 まず現実：メッセージングは“ズレる”前提📨🌪️

分散システムのメッセージは、ざっくり言うと **「郵便」** みたいなもの📮
ちゃんと届く努力はしてくれるけど、現実にはこういうことが起きるよ👇

* **重複**：同じメッセージが2回以上届く🔁
* **順序入れ替え**：A→Bのはずが、B→Aで届く🔀
* **遅延・一部欠落っぽく見える**：しばらく来ない…⏳（あとで来るかも）

特に「少なくとも1回届ける」系のキューだと、**重複や順序の乱れが普通に起きる**。

![saga_cs_study_014_mail_chaos.png](./picture/saga_cs_study_014_mail_chaos.png)たとえば SQS の Standard Queue は、複数回届くことや、順序が前後することがあると明記されてるよ📌 ([AWS ドキュメント][1])

### メッセージの「ズレ」のイメージ 📮🌪️
```mermaid
graph LR
    subgraph Normal [理想]
        I1[1] --> I2[2] --> I3[3]
    end
    subgraph Real [現実]
        R1[1] --> R3[3]
        R3 --> R2[2]
        R2 --> R1_dup[1 (重複)]
    end
```

---

## 14.2 3大落とし穴（Saga視点で見る）🧩😵‍💫

### (1) 重複：同じイベントが2回届く🔁😱

**例：** `PaymentAuthorized` が2回来る
→ 何も考えず処理すると「二重出荷」「二重予約」「二重補償」になりがち💥

![saga_cs_study_014_double_steak.png](./picture/saga_cs_study_014_double_steak.png)

**なぜ起きる？**

* 送信側が「送れたか不明」で再送する
* ネットワークやACKの行き違いで再送される
  こういう“疑い”をなくす仕組みとして、Azure Service Bus には **Duplicate detection（重複検知）** があって、`MessageId` を一定期間記録して同じIDを落とせるよ🧠🧹 ([Microsoft Learn][2])

ただし重要ポイント👇

* ブローカーの重複対策があっても、**受信側は冪等に作る**のが基本（Sagaは特に！）💪🔑

---

### (2) 順序：A→B のはずが B→A で来る🔀😵

**例：** `InventoryReserved` が `PaymentAuthorized` より先に届く
→ Sagaの状態機械が「え？まだ決済できてないよ？」ってなる😵‍💫

![saga_cs_study_014_shoes_before_socks.png](./picture/saga_cs_study_014_shoes_before_socks.png)

**順序が欲しいなら“束ねるキー”が必要**🧷

* Azure Service Bus は **Sessions** を使うと、関連メッセージをFIFOで扱える（同じセッション内で順序処理）📌 ([Microsoft Learn][3])
* Kafka は **同一パーティション内**では順序が保証される（だからキーで同じパーティションに寄せる）📌 ([Confluent][4])
* RabbitMQ のキューはFIFOの性質を持つけど、**複数コンシューマだと round-robin 配送**になりやすく、結果として“処理順”が崩れやすい（並列処理の副作用）🌀 ([rabbitmq.com][5])

**結論（超だいじ）💡**

* 「全体で完全な順序」はだいたい無理🙅‍♀️
* 「注文ごと（OrderIdごと）なら順序がほしい」みたいに **粒度を落として順序を作る**✅

---

### (3) 遅延：遅れて届く / 来ないように見える⏳😵

**例：** 決済が成功してるのに、イベントが30秒遅れで来る
→ 先にタイムアウト処理でキャンセル補償が走ってしまい、あとから成功イベントが来て地獄👻

これはSagaでよくある「時間のズレ」問題🕰️

* ネットワーク、混雑、再試行、バックログで遅延は普通に起きる
* ブローカー側にも “遅延” の仕組みがあり、Service Bus は **Scheduled delivery（遅延配信）** や **DLQ（デッドレター）** を持ってるよ📦🪦 ([Microsoft Learn][6])

---

## 14.3 じゃあどう守る？対策カタログ🛡️📚

Sagaの受信側（イベント/コマンドのハンドラ）で、次の4択に分類できると強いよ💪✨

![saga_cs_study_014_defense_sorting.png](./picture/saga_cs_study_014_defense_sorting.png)

### ✅ A. 無視（Ignore）

* **重複**で、すでに処理済みなら無視🔁🚫
* **古いイベント**で、もう状態が先に進んでるなら無視🕰️🚫

### ✅ B. 保留（Hold / Pending）

* **順不同**で、前提となるステップがまだなら一旦保留📥⏸️

  * 例：決済前に在庫確保イベントが来た → `PendingEvents` に入れる
  * 後で状態が整ったら再評価する

### ✅ C. リトライ（Retry）

* 一時的なエラー（DB一瞬落ちた/外部API一時不調）なら再試行🔁⏳
# * ただし **リトライ無限** は事故るので、回数や期限を決める（第16章につながるよ）🧯

## ✅ D. 補償（Compensate）

* “業務として成立しない” 状態になったら補償へ🧾🔁

  * 例：在庫確保できない → 決済を返金、注文をキャンセル、など

---

## 14.4 最低限の防御ライン（Sagaの必須3点セット）🥷🛡️

### ① 受信冪等（Inbox / ProcessedMessage）🔑📥

「このメッセージID、もう処理した？」を記録して重複を防ぐ✨
Azure Service Bus は `MessageId` ベースの重複検知があるけど、受信側でも同じ発想を持つのが安心だよ🧠 ([Microsoft Learn][2])

**DBでやるなら（超よくある形）👇**

```sql
CREATE TABLE ProcessedMessage (
    MessageId UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
    ProcessedAt DATETIMEOFFSET NOT NULL,
    CorrelationId UNIQUEIDENTIFIER NULL,
    MessageType NVARCHAR(200) NOT NULL
);
-- 重要：PRIMARY KEY（または UNIQUE）で “二重挿入できない” を作る
```

---

### ② 状態機械のガード（期待してない遷移は通さない）⚙️🚧

「今のSaga状態で、このイベントを処理していい？」を必ずチェック✅

* OK → 適用して状態更新
* NG → 保留 or 無視 or DLQ

---

### ③ “順序が必要なら束ねる”（Session / Key / Partition）🧷📌

* Service Bus：**SessionId** を OrderId にする、など（Order単位FIFO）📨 ([Microsoft Learn][3])
* Kafka：同じキーで同じパーティションへ（キー単位で順序）🧵 ([Confluent][4])

---

## 14.5 ミニ演習📝🎲（ズレた到着にどう返す？）

### シナリオ：注文Saga（理想の順）🛒

1. `OrderCreated`
2. `PaymentAuthorized`
3. `InventoryReserved`
4. `ShipmentCreated`

### 事件😱：実際に届いた順

1. `OrderCreated`
2. `InventoryReserved`（先に来た！）
3. `PaymentAuthorized`
4. `PaymentAuthorized`（重複！）

**Q1**：2の `InventoryReserved` を受け取った時、どうする？🧠

* A 無視
* B 保留
* C リトライ
* D 補償

**Q2**：4の重複 `PaymentAuthorized` は？🔁

---

### こたえ✅😊

* **Q1：B 保留**
  決済が前提の設計なら「前提が揃うまで Pending に置く」📥⏸️
* **Q2：無視（＋冪等記録）**
  Inbox（ProcessedMessage）にあれば即return🔁🚫

![saga_cs_study_014_puzzle_piece_pending.png](./picture/saga_cs_study_014_puzzle_piece_pending.png)

---

## 14.6 C#ミニ実装（“ズレ耐性”の骨組み）🧑‍💻✨

ここでは雰囲気を掴む用に、超ミニで書くよ（本番はDB＋トランザクションで強化する感じ）💪

```csharp
public interface IMessage
{
    Guid MessageId { get; }
    Guid CorrelationId { get; }   // 例: OrderId
    string MessageType { get; }   // 例: "PaymentAuthorized"
    DateTimeOffset OccurredAt { get; }
}

public enum SagaStatus
{
    Created,
    Paid,
    InventoryReserved,
    Shipped,
    Cancelled
}

public sealed class OrderSaga
{
    public Guid OrderId { get; init; }
    public SagaStatus Status { get; private set; } = SagaStatus.Created;

    public bool CanApply(IMessage msg) => (Status, msg.MessageType) switch
    {
        (SagaStatus.Created, "PaymentAuthorized") => true,
        (SagaStatus.Paid, "InventoryReserved") => true,
        (SagaStatus.InventoryReserved, "ShipmentCreated") => true,
        // それ以外は「想定外の順序」なので保留/無視候補
        _ => false
    };

    public void Apply(IMessage msg)
    {
        Status = msg.MessageType switch
        {
            "PaymentAuthorized" => SagaStatus.Paid,
            "InventoryReserved" => SagaStatus.InventoryReserved,
            "ShipmentCreated" => SagaStatus.Shipped,
            _ => Status
        };
    }
}

public sealed class InMemoryInbox
{
    private readonly HashSet<Guid> _processed = new();
    private readonly object _lock = new();

    public bool TryMarkProcessed(Guid messageId)
    {
        lock (_lock)
        {
            if (_processed.Contains(messageId)) return false; // duplicate
            _processed.Add(messageId);
            return true;
        }
    }
}

public sealed class InMemoryPending
{
    private readonly Dictionary<Guid, List<IMessage>> _pending = new();

    public void Add(IMessage msg)
    {
        if (!_pending.TryGetValue(msg.CorrelationId, out var list))
        {
            list = new List<IMessage>();
            _pending[msg.CorrelationId] = list;
        }
        list.Add(msg);
    }

    public IReadOnlyList<IMessage> Drain(Guid correlationId)
    {
        if (!_pending.TryGetValue(correlationId, out var list)) return Array.Empty<IMessage>();
        _pending.Remove(correlationId);
        return list;
    }
}

public sealed class SagaHandler
{
    private readonly InMemoryInbox _inbox = new();
    private readonly InMemoryPending _pending = new();
    private readonly Dictionary<Guid, OrderSaga> _store = new();

    public void Handle(IMessage msg)
    {
        // 1) 重複は即捨て（冪等）
        if (!_inbox.TryMarkProcessed(msg.MessageId)) return;

        // 2) Sagaロード（なければ作る例）
        if (!_store.TryGetValue(msg.CorrelationId, out var saga))
        {
            saga = new OrderSaga { OrderId = msg.CorrelationId };
            _store[msg.CorrelationId] = saga;
        }

        // 3) 順序が合わないなら保留
        if (!saga.CanApply(msg))
        {
            _pending.Add(msg);
            return;
        }

        // 4) 適用して状態更新
        saga.Apply(msg);

        // 5) 状態が進んだら、保留してたやつを再評価（ここが気持ちいい✨）
        foreach (var p in _pending.Drain(msg.CorrelationId))
        {
            if (saga.CanApply(p)) saga.Apply(p);
            else _pending.Add(p); // まだ無理なら戻す（本番は回数/期限でDLQへ）
        }
    }
}
```

ポイントまとめ🎀

* **Inbox** で重複を落とす🔁✅
* **CanApply** で想定外順序をブロック🧱
* **Pending** で“順不同”を吸収📥
* 本番では Pending を無限に抱えないように **期限/回数/DLQ** を設計する（運用へ）🪦📌 ([Microsoft Learn][6])

---

## 14.7 AI活用（Copilot / Codex向け）🤖✨

### ✅ 事故パターン洗い出しプロンプト📝

```text
注文Saga（OrderCreated→PaymentAuthorized→InventoryReserved→ShipmentCreated）で、
メッセージの「重複・順不同・遅延」が起きたときの事故パターンを列挙して。
各パターンに「無視/保留/リトライ/補償」の推奨対応も付けて。
```

### ✅ 状態機械のガード生成プロンプト⚙️

```text
このSagaの状態（Created/Paid/InventoryReserved/Shipped/Cancelled）に対して、
受け取れるイベントと禁止イベントの表（遷移表）を作って。
禁止イベントが来たときの扱い（無視・保留・DLQ）も提案して。
```

### ✅ テスト観点プロンプト🧪

```text
受信側が「冪等」「順不同耐性」「遅延耐性」を持つことを確認するテストケースを作って。
各テストで、入力メッセージ列（順番・重複）と期待されるSaga最終状態を書いて。
```

---

## 14.8 チェックリスト（この章の持ち帰り）✅🎒

* [ ] 受信は **必ず冪等**（Inbox/一意制約など）🔁
* [ ] 状態機械で **想定外遷移を通さない**⚙️🚧
* [ ] 順序が必要なら **キーで束ねる**（Session/Partition）🧷 ([Microsoft Learn][3])
* [ ] 保留は **期限・回数・DLQ** を持つ（永久保留は禁止）🪦 ([Microsoft Learn][6])
* [ ] Standard系キューは「重複・順不同」を前提に設計する📌 ([AWS ドキュメント][1])

---

## ⚠️ 2026年の最新注意メモ（Azure Service Bus）📌🧯

古い Azure Service Bus SDK（`WindowsAzure.ServiceBus` / `Microsoft.Azure.ServiceBus` など）や SBMP プロトコルは **2026-09-30 にサポート終了予定**なので、最新Azure SDKへ寄せる前提で組むのが安全だよ🧰✨ ([Microsoft Learn][2])

[1]: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html "Amazon SQS standard queues - Amazon Simple Queue Service"
[2]: https://learn.microsoft.com/en-us/azure/service-bus-messaging/duplicate-detection "Azure Service Bus duplicate message detection - Azure Service Bus | Microsoft Learn"
[3]: https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-sessions?utm_source=chatgpt.com "Azure Service Bus message sessions"
[4]: https://www.confluent.io/learn/kafka-partition-key/?utm_source=chatgpt.com "Apache Kafka Partition Key: A Comprehensive Guide"
[5]: https://www.rabbitmq.com/docs/queues?utm_source=chatgpt.com "Queues"
[6]: https://learn.microsoft.com/en-us/azure/service-bus-messaging/advanced-features-overview "Azure Service Bus messaging - advanced features - Azure Service Bus | Microsoft Learn"


![saga_cs_study_014_guest_list_check.png](./picture/saga_cs_study_014_guest_list_check.png)
