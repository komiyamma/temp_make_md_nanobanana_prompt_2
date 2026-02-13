# 第21章：リトライ設計＋デッドレター（失敗と仲良くなる）🛠️🧯

## この章でできるようになること 🎯✨

* 「失敗には種類がある！」を言えるようになる（**一時失敗** vs **恒久失敗**）🌩️🧱
* リトライの設計パラメータ（回数・間隔・バックオフ・ジッター）を決められる ⏳🎲
* Outboxの配送係（Relay）が失敗したときの「正しい振る舞い」を実装イメージできる 🚚💥
* “毒メッセージ”を隔離する **デッドレター**（Dead Letter）運用がわかる ☠️📦
* 隔離されたら「何を見る？どう直す？」の手順が作れる 🔍🧑‍🔧

---

## 1. 失敗の2種類を見分けよう 👀💡（超重要）

![Failure Types](./picture/outbox_cs_study_021_failure_types.png)

### ✅ 一時失敗（Transient）🌩️

「しばらくしたら直るかも」系

* ネットワークの一時不調 📶💦
* 相手サービスが一瞬だけ重い（タイムアウト）⏱️😵
* 一時的な 429 / 503 みたいな “混んでるよ” 🧑‍🤝‍🧑🚧

👉 **基本はリトライ対象**（ただし“やみくも”はNG）🙅‍♀️

### ❌ 恒久失敗（Permanent）🧱

「待っても直らない」系

* 送るデータが壊れてる（JSONが壊れてる、必須項目が欠けてる）🧾💥
* 相手が “そのIDは存在しない” と言っている 🆔❓
* 認証・権限が間違ってる（設定ミス）🔑🚫

👉 **リトライしてもムダ**になりがち → **隔離（デッドレター）候補**☠️📦

---

## 2. リトライは「設計」しないと事故る 😱🧨

![Retry Backoff](./picture/outbox_cs_study_021_retry_backoff.png)
![Thundering Herd](./picture/outbox_cs_study_021_thundering_herd.png)

### リトライで起きがちな事故 💥

* 失敗するたびに即リトライ → 相手をさらに殴る → もっと落ちる 🥊🌀
* たくさんのRelayが同時にリトライ → **群れ（Thundering Herd）**で爆発 🐑🐑🐑💣
* “永遠にリトライ” → Outboxが詰まって運用崩壊 📦📦📦😵

### だから「指数バックオフ＋ジッター」が定番 🧠✨

* **指数バックオフ（Exponential backoff）**：失敗するほど待ち時間を増やす ⏳➡️⏳⏳➡️⏳⏳⏳
* **ジッター（Jitter）**：待ち時間にランダム要素を混ぜて“同時突撃”を防ぐ 🎲🛑

バックオフ＋上限（キャップ）を設けるのが一般的だよ〜、という話がまとまってるよ 📚✨  ([Amazon Web Services, Inc.][1])

---

## 3. リトライ設計で決める5つのこと 🧩📝

### (1) 最大リトライ回数 🔁

例：**5回** とか **10回**

* 少なすぎ：一時障害を拾えない 😢
* 多すぎ：ずっと詰まる 😵

### (2) 初期待ち時間（ベース）⏱️

例：1秒 / 2秒 / 5秒 など

### (3) バックオフの増え方 📈

例：倍々（2^n）

* 1s → 2s → 4s → 8s → 16s …

### (4) 最大待ち時間（キャップ）🧢

例：最大 1分 / 5分
指数はすぐ大きくなるので「上限」が大事！ ([Amazon Web Services, Inc.][1])

### (5) ジッターの入れ方 🎲

![Jitter Dice](./picture/outbox_cs_study_021_jitter_dice.png)

例：±20% ぶんランダム、または 0〜X 秒を足す
「群れ」を避けたいならジッター推奨だよ〜、というガイドもあるよ 🐑🛑 ([Microsoft Learn][2])

---

## 4. デッドレター（Dead Letter）ってなに？☠️📦

![Dead Letter Box](./picture/outbox_cs_study_021_dlq_box.png)

### ざっくり言うと…

**「もう自動処理はムリっぽいメッセージを隔離して、あとで人間が見る箱」**🧑‍🔧🔍

実際のメッセージング基盤でも同じ考え方があるよ👇

* Microsoft の **Azure Service Bus**：処理できないメッセージをDLQに保持して、取り出して検査・修正・再送ができる ✨ ([Microsoft Learn][3])
* **RabbitMQ**：条件で“dead-lettered”になったメッセージを交換機へ再発行する仕組み（DLX）📮➡️📦 ([RabbitMQ][4])
* Amazon の **SQS**：処理失敗したメッセージをDLQへ移して原因調査に役立てる 📦🔍 ([AWSドキュメント][5])

👉 Outboxでも発想は同じ！
「失敗を握りつぶさず、でもシステム全体を止めない」ための仕組みだよ 🛡️😊

---

## 5. Outboxでの「リトライ＆デッドレター」設計 🍱📦

### 5.1 Outboxテーブルに持たせたい列（実用ミニマム）🧱

* `Status`：Pending / Processing / Sent / Failed / DeadLettered など 🚦
* `RetryCount`：何回失敗した？ 🔢
* `NextAttemptAt`：次はいつ再挑戦する？ ⏰
* `LastError`：最後のエラー（短めでOK）💬
* `LastAttemptAt`：最後に試した時刻 🕒
* `DeadLetterReason`：隔離した理由（分類）🏷️

「後から運用で助かる列」ほど最初に入れとくと楽だよ〜 🧹✨

---

## 6. Relayの基本アルゴリズム 🚚💨（これが“正しい動き”）

![Relay Logic Flow](./picture/outbox_cs_study_021_relay_logic_flow.png)

### ステップ0：対象を取る 🔍

* `Status = Pending or Failed`
* `NextAttemptAt <= now`
  のものをバッチで取る 📦📦📦

### ステップ1：送る ✉️

* 送信（HTTP/Queueなど）を試す 💪

### ステップ2：成功したら ✅

* `Status = Sent`
* `SentAt = now`（任意）
* `LastError = null`

### ステップ3：失敗したら 💥

まず「一時失敗？恒久失敗？」を分類 👇

#### ✅ 一時失敗っぽい → リトライへ 🔁

* `RetryCount++`
* `Status = Failed`（または RetryPending）
* `NextAttemptAt = now + delay`

  * delay は **指数バックオフ＋ジッター＋キャップ** ⏳🎲🧢

#### ❌ 恒久失敗っぽい → デッドレターへ ☠️

* `Status = DeadLettered`
* `DeadLetteredAt = now`
* `DeadLetterReason = "invalid_payload"` みたいに分類しておく 🏷️

---

## 7. C# 実装例（考え方が伝わる最小形）🧑‍💻✨

### 7.1 バックオフ＋ジッター計算 🎲⏳

ポイント：指数で増やしつつ、上限で止めて、ランダムを足す！
（“バックグラウンド処理は指数バックオフ＋ジッター推奨”というガイドもあるよ） ([Microsoft Learn][2])

```csharp
using System;

public static class RetryDelay
{
    // retryCount: 1,2,3...（失敗回数）
    public static TimeSpan ComputeDelay(
        int retryCount,
        TimeSpan baseDelay,
        TimeSpan maxDelay,
        double jitterRatio = 0.2) // 20%ジッター
    {
        // 指数バックオフ: base * 2^(retryCount-1)
        var exp = TimeSpan.FromMilliseconds(
            baseDelay.TotalMilliseconds * Math.Pow(2, retryCount - 1));

        // キャップ
        var capped = exp < maxDelay ? exp : maxDelay;

        // ジッター（±jitterRatio）
        var rand = Random.Shared.NextDouble(); // 0..1
        var jitter = (rand * 2 - 1) * jitterRatio; // -ratio..+ratio
        var jitteredMs = capped.TotalMilliseconds * (1 + jitter);

        // 0未満防止
        jitteredMs = Math.Max(0, jitteredMs);

        return TimeSpan.FromMilliseconds(jitteredMs);
    }
}
```

---

### 7.2 “一時失敗っぽい例外”を判定する（超ざっくり版）🌩️

※ 本番では送信先ごとにもっと丁寧に（HTTPならStatusCode、QueueならSDK例外など）👍

```csharp
using System;
using System.Net.Http;

public static class FailureClassifier
{
    public static bool IsTransient(Exception ex)
    {
        // タイムアウト系
        if (ex is TimeoutException) return true;

        // HTTP系の一時エラーは状況次第（例: HttpRequestException）
        if (ex is HttpRequestException) return true;

        // それ以外は一旦「恒久かも」扱い（安全側）
        return false;
    }
}
```

---

### 7.3 Outboxレコード更新のイメージ（状態遷移）🚦

ここは **“DB更新”** が主役なので、まずは「どう更新したいか」を形にしよ〜🧾✨

```csharp
public enum OutboxStatus
{
    Pending,
    Processing,
    Sent,
    Failed,
    DeadLettered
}

public sealed class OutboxMessage
{
    public Guid Id { get; set; }
    public OutboxStatus Status { get; set; }
    public int RetryCount { get; set; }
    public DateTimeOffset? NextAttemptAt { get; set; }
    public DateTimeOffset? LastAttemptAt { get; set; }
    public string? LastError { get; set; }
    public string? DeadLetterReason { get; set; }
}
```

---

## 8. “毒メッセージ”を隔離する基準（初心者ルール）☠️📦✨

### すぐ隔離していいケース ✅

* JSONがパースできない 🧾💥
* 必須項目が欠けてる（Outbox作成側のバグっぽい）🐛
* バリデーションで「これは不正」って確定できる 🚫

### 少し粘ってリトライしていいケース 🔁

* ネットワーク不調 📶
* タイムアウト ⏱️
* 429 / 503 みたいな “混んでる” 🧑‍🤝‍🧑🚧
  （こういう時に指数バックオフ＋ジッターが効くよ！） ([Amazon Web Services, Inc.][1])

---

## 9. 運用のミニ手順：隔離したら何を見る？どう直す？🔍🧑‍🔧

![Manual Fix Bench](./picture/outbox_cs_study_021_manual_fix_bench.png)

### 9.1 まず見るもの（上から順）👀

1. `DeadLetterReason`（分類）🏷️
2. `LastError`（最後のエラー）💬
3. `RetryCount` と `LastAttemptAt`（どれだけ粘った？）🔢🕒
4. `Payload`（中身）🧾
5. 送信先ログ（相関IDやOutboxIdで追跡）🧵

### 9.2 直し方の“型”（よくある3パターン）🛠️

* **データ修正して再送**：Payloadが直せるなら直して再投入 🔧📦
* **コード修正して再送**：変換ロジックやマッピングがバグってた 🐛➡️✅
* **捨てる判断**：そのイベント自体が不要だった（ただし監査的に記録は残す）🗑️📝

Azure Service BusのDLQも「検査して、ユーザーが修正し、再送できる」方向で説明してるよ 🔍✨ ([Microsoft Learn][3])

---

## 10. ミニ演習（やると一気に腹落ちするやつ）🧪🏃‍♀️✨

### 演習A：一時失敗 → リトライで復帰 🔁✅

1. 送信処理で「ランダムに失敗する」ようにする 🎲💥（例：30%で例外）
2. `RetryCount` が増えるのを見る 🔢👀
3. `NextAttemptAt` が未来になっているのを見る ⏰👀
4. そのうち成功して `Sent` になるのを見る ✅🎉

### 演習B：恒久失敗 → デッドレターへ ☠️📦

1. Payloadをわざと壊す（例：必須フィールド欠け）🧾💥
2. Relay側でバリデーションして「これは恒久失敗」と判断する 🚫
3. `DeadLettered` に遷移するのを確認 ☠️➡️📦

### 演習C：デッドレターを“人が救う”🧑‍🔧✨

1. `LastError` を見て原因を特定 🔍
2. データ or コードを修正 🛠️
3. レコードを **再投入**（例：`Status=Pending`, `RetryCount=0`, `NextAttemptAt=now`）♻️📦
4. 受け手側が冪等なら「再投入」も怖くない ✅🛡️（前章につながるやつ！）

---

## 11. もう一段レベルアップ：Pollyなどの“レジリエンス”を使う選択肢 🤝🧰

.NET界隈では、リトライ・サーキットブレーカー等をまとめて **レジリエンス（resilience）** と呼んで、ライブラリで扱うのが定番になってるよ 🧠✨

* **Polly**：Retry / Circuit Breaker / Timeout などを組み合わせられる（.NETのレジリエンス文脈でも頻出） ([nuget.org][6])

Outbox Relayの送信部分（HTTPやQueue送信）に、こういう仕組みを“薄く”入れるのはアリだよ〜🪄

---

## まとめ 🎀📌

* 失敗は **一時** と **恒久** に分ける 🌩️🧱
* 一時失敗は **指数バックオフ＋ジッター＋キャップ** で上品にリトライ ⏳🎲🧢 ([Amazon Web Services, Inc.][1])
* 恒久失敗は **デッドレター** に隔離して、人が救うルートを作る ☠️📦🔍 ([Microsoft Learn][3])
* 「隔離したら何を見る？」の手順まで用意できると、運用がめちゃ強くなる 💪✨

[1]: https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/?utm_source=chatgpt.com "Timeouts, retries and backoff with jitter"
[2]: https://learn.microsoft.com/en-us/azure/well-architected/design-guides/handle-transient-faults?utm_source=chatgpt.com "Recommendations for handling transient faults"
[3]: https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues?utm_source=chatgpt.com "Service Bus dead-letter queues - Azure"
[4]: https://www.rabbitmq.com/docs/dlx?utm_source=chatgpt.com "Dead Letter Exchanges"
[5]: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html?utm_source=chatgpt.com "Using dead-letter queues in Amazon SQS"
[6]: https://www.nuget.org/packages/polly/?utm_source=chatgpt.com "Polly 8.6.5"
