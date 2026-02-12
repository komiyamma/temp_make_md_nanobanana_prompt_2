# 第10章：Outboxテーブル設計（運用を見据えた版）🔍🧹

## この章のゴール 🎯✨

Outboxを「ただの箱📦」から、「運用で死なない箱🛡️」へ進化させます。

* 失敗してもリトライできる🔁
* どれが詰まってるか一目で分かる👀
* 複数の配送係（Relay）が動いてもケンカしない👯‍♀️
* 古いデータをちゃんと掃除できる🧹

---

## 1) 運用で起きがちな“困った😇”あるある

## あるある①：未送信が溜まって地獄😱📦📦📦

最初は動くけど、数日〜数週間で「未送信が増え続ける」問題が出ます。

* 送信先が落ちる🌩️
* 一部のメッセージだけ恒久的に失敗する🧱
* Relayが止まって気づかない😴

## あるある②：失敗の原因が分からない🔍💥

「Failedって書いてあるけど、何が起きたの？」状態。

* いつ失敗した？⏰
* 何回目の失敗？🔁
* どんな例外？🧨

## あるある③：Relayを増やしたら二重送信っぽい👯‍♀️📨

複数のRelayが同じ行を取りに行ってしまうと、配送がバッティングします💥
（Outboxは“少なくとも1回”の配送になりやすいので、運用設計が大事です。）

---

## 2) “運用を見据えた”Outboxテーブル：追加カラムの全体像 🧾✨

ミニマム（第9章）の基本カラムに加えて、運用ではだいたい次が欲しくなります👇

## 2.1 状態（Status）とリトライ系 🔁

* **Status**：`Pending / InProgress / Sent / Failed / DeadLetter` など
* **RetryCount**：何回失敗したか
* **NextAttemptAtUtc**：次に試す時刻（バックオフ用⏳）
* **LastAttemptAtUtc**：最後に試した時刻
* **SentAtUtc**：送信が成功した時刻（監査にも便利🕵️‍♀️）

## 2.2 エラー情報（必要最小限で）🧯

* **LastError**：最後のエラー（文字列は長くしすぎ注意⚠️）
* **LastErrorType / LastErrorCode**：分類用（集計しやすい📊）
* **FailedAtUtc**：失敗した時刻（最後に失敗した時刻でもOK）

## 2.3 ロック（複数Relay対策）🔒

* **LockOwner**：この行を掴んだRelayの識別子（例：マシン名＋PID）
* **LockedUntilUtc**：ロックの有効期限（死んだRelayのロックを自然解除🧊→🔥）

---

## 3) Status設計：迷ったらこの状態遷移でOK ✅🗺️

![State Machine](./picture/outbox_cs_study_010_state_machine.png)

まずはシンプルにこの5つが強いです💪

* `Pending`：未送信（取り出し対象）
* `InProgress`：配送中（ロック中）
* `Sent`：送信成功（掃除対象🧹）
* `Failed`：失敗（リトライ対象🔁）
* `DeadLetter`：規定回数超えなどで隔離☠️📦

状態遷移イメージ👇

* `Pending` → `InProgress` → `Sent`
* `Pending` → `InProgress` → `Failed` →（待って）→ `Pending`
* `Failed` →（回数超え）→ `DeadLetter`

---

## 4) リトライ設計の要点：RetryCountとNextAttemptAtUtcが主役 👑🔁

## 4.1 なぜNextAttemptAtUtcが必要？⏳

「失敗したらすぐ再送！」をやると、

* 送信先が落ちてる時に無限パンチ🥊🥊🥊
* DB負荷が急上昇📈
* ログが爆発💣

になりがちです。

そこで、失敗したら次の試行時刻を未来にずらします👇
（いわゆるバックオフ⏳）

例：

* 1回目失敗 → 10秒後
* 2回目失敗 → 30秒後
* 3回目失敗 → 2分後
* …みたいに、だんだん待つ🙂

---

## 5) 複数Relayでも安全にする：ロック戦略 🔒👯‍♀️

## 5.1 “DBを真実のソース”にしてロックする 🏛️

Outboxは「DBに書けたら勝ち」パターンなので、配送の取り合いもDB側で制御するのが定番です。

考え方はこう👇

1. `Pending`（かつ `NextAttemptAtUtc <= now`）を探す🔍
2. その行を **InProgress + LockOwner + LockedUntilUtc** に更新する✍️
3. 更新に成功した人だけが送信していい📨✅
4. 期限（LockedUntilUtc）を過ぎたロックは、別Relayが回収できる🚑

※複数インスタンスが共存する設計は、実装例でも「状態テーブルでロックする」方針が紹介されています。([DEV Community][1])

---

## 6) インデックス設計：Outboxの性能はここで決まる🏃‍♀️💨

## 6.1 Relayがよく打つクエリはだいたいこれ👀

* 条件：`Status = Pending`
* 条件：`NextAttemptAtUtc <= now`
* 並び：`OccurredAtUtc`（古い順に配送したい）
* 件数：`TOP (N)`（バッチサイズ）

なので、インデックスもこのクエリに合わせます🎯
「並び順に合うインデックスを貼ると、ソートが減って速い」みたいな話はスケール実例でも強調されています。([milanjovanovic.tech][2])

## 6.2 SQL Server向け：まずはこの1本が王道👑（例）

```sql
-- 取り出し（Pending + 期限到来）を速くする
CREATE INDEX IX_Outbox_Pending_Next_Occurred
ON dbo.OutboxMessages (Status, NextAttemptAtUtc, OccurredAtUtc)
INCLUDE (Type, Payload);
```

ポイント✨

* **Status, NextAttemptAtUtc, OccurredAtUtc** をキーにして
  → 「条件＋並び」に合わせる🎯
* 取り出しで必要な列（Type/Payload）を `INCLUDE` に入れて
  → 余計な行アクセスを減らす🚀（入れすぎ注意⚠️）

## 6.3 “掃除🧹”用のインデックスも忘れずに

Sentを定期削除するなら、これがあると強い👇

```sql
CREATE INDEX IX_Outbox_SentAt
ON dbo.OutboxMessages (Status, SentAtUtc);
```

---

## 7) 保持期間と掃除：Outboxは放置すると太ります🐷📦

## 7.1 まず決める：どれくらい残す？🗓️

おすすめの考え方👇

* `Sent`：短め（例：7〜30日）で削除🧹
* `DeadLetter`：長め（例：30〜180日）で残す（調査用🔍）
* 監査要件があるなら別ストレージへ退避📚

“Outbox系のテーブルはクリーンアップが重要”という話は、実装・運用の議論でもよく出ます。([GitHub][3])

## 7.2 掃除ジョブは「アプリのついで」より「専用」が安心🧹🕰️

複数インスタンス環境だと、各インスタンスが掃除し始めて競合💥しやすいので

* **DBジョブ / スケジューラで1本だけ**
  がシンプルで事故りにくいです🙂‍↕️([GitHub][3])

---

## 8) “後で地獄”にならない設計のコツ🔥→🛡️

## コツ①：文字列は無限に保存しない✋🧨

`LastError` にスタックトレース丸ごと入れると、行がデカくなって検索も遅くなります😇

おすすめ👇

* `LastErrorCode`（短い分類）＋`LastError`（要約、上限あり）
* 詳細はログ（相関IDで追えるように）🧵

## コツ②：状態は“増やしすぎない”🌱

初心者フェーズでは、状態は少ないほど正義👼
増やすのは「必要が見えてから」でOKです。

## コツ③：時刻は基本UTCで統一🌍🕰️

集計・監視・障害対応が楽になります。

---

## 9) 参考：OutboxMessagesのサンプルDDL（SQL Server）🧾✨

```sql
CREATE TABLE dbo.OutboxMessages
(
    Id               uniqueidentifier NOT NULL PRIMARY KEY,
    Type             nvarchar(200)    NOT NULL,
    Payload          nvarchar(max)    NOT NULL,

    OccurredAtUtc    datetime2        NOT NULL,

    Status           tinyint          NOT NULL, -- 0=Pending,1=InProgress,2=Sent,3=Failed,4=DeadLetter
    RetryCount       int              NOT NULL DEFAULT(0),

    NextAttemptAtUtc datetime2        NULL,
    LastAttemptAtUtc datetime2        NULL,

    SentAtUtc        datetime2        NULL,
    FailedAtUtc      datetime2        NULL,

    LastErrorCode    nvarchar(50)     NULL,
    LastError        nvarchar(1000)   NULL,

    LockOwner        nvarchar(200)    NULL,
    LockedUntilUtc   datetime2        NULL
);
```

---

## 10) 参考：C#のモデル例（EF Core想定）🧑‍💻✨

```csharp
public enum OutboxStatus : byte
{
    Pending = 0,
    InProgress = 1,
    Sent = 2,
    Failed = 3,
    DeadLetter = 4
}

public sealed class OutboxMessage
{
    public Guid Id { get; init; }
    public string Type { get; init; } = "";
    public string Payload { get; init; } = "";

    public DateTimeOffset OccurredAtUtc { get; init; }

    public OutboxStatus Status { get; set; } = OutboxStatus.Pending;
    public int RetryCount { get; set; }

    public DateTimeOffset? NextAttemptAtUtc { get; set; }
    public DateTimeOffset? LastAttemptAtUtc { get; set; }

    public DateTimeOffset? SentAtUtc { get; set; }
    public DateTimeOffset? FailedAtUtc { get; set; }

    public string? LastErrorCode { get; set; }
    public string? LastError { get; set; }

    public string? LockOwner { get; set; }
    public DateTimeOffset? LockedUntilUtc { get; set; }
}
```

---

## 11) ミニ演習 🧪🏁：「取り出しが速いOutbox」を作ってみよう

## 演習1：インデックスを貼って、取り出しを想像する👀⚡

1. `IX_Outbox_Pending_Next_Occurred` を作る
2. 1000件くらい `Pending` を入れる📦
3. 「期限到来のPendingを古い順でTOP 50」みたいなクエリを考える
4. “このインデックスなら速そう！”が言えたら勝ち🏆

## 演習2：失敗→リトライの記録を更新してみる🔁🧯

* 送信失敗を想定して

  * `RetryCount++`
  * `LastAttemptAtUtc = now`
  * `FailedAtUtc = now`
  * `LastError = "timeout"`
  * `NextAttemptAtUtc = now + 30秒`
    みたいに更新してみよう✍️

## 演習3：掃除SQLを書いてみる🧹

* `SentAtUtc < now - 30日` の `Sent` を削除するSQLを書いてみる🙂

---

## 12) この章のチェックリスト✅🧡

* [ ] StatusとRetryCountがある🔁
* [ ] NextAttemptAtUtcでバックオフできる⏳
* [ ] LastErrorが“短く”残る🧯
* [ ] ロック（LockOwner/LockedUntilUtc）で多重Relayに備えた🔒
* [ ] `Pending + 期限到来 + 古い順` に合うインデックスがある🏃‍♀️💨
* [ ] Sentを消す掃除の方針がある🧹

---

## ちょいメモ📌（最新動向の足場）

2026年時点では .NET 10 系の情報が公式に整理されています（言語はC# 14として紹介されることが多いです）。([learn.microsoft.com][4])

[1]: https://dev.to/hootanht/learning-masstransit-transactional-outbox-pattern-g4c?utm_source=chatgpt.com "Learning - MassTransit Transactional Outbox Pattern"
[2]: https://www.milanjovanovic.tech/blog/scaling-the-outbox-pattern?utm_source=chatgpt.com "Scaling the Outbox Pattern (2B+ messages per day)"
[3]: https://github.com/Particular/NServiceBus.Persistence.Sql/issues/333?utm_source=chatgpt.com "Cannot customize outbox clean up features · Issue #333"
[4]: https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/overview?utm_source=chatgpt.com "What's new in .NET 10"
