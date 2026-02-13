# 第15章：配送係（Relay）の設計：まずはポーリングでOK ⏱️🚚

## この章のゴール 🎯✨

* Relay（配送係）が **Outboxテーブルから「未送信」を取り出して送る流れ**をイメージできるようになる📦➡️📩
* **二重送信・取りこぼし・詰まり（スタック）**を、設計でどう避けるか分かる🧯
* まずは **ポーリング（定期見回り）**で、シンプルに作れるようになる⏰🙂

---

## 1) Relayって何者？👀🚚

![Relay Role](./picture/outbox_cs_study_015_relay_role.png)

Relayは、ざっくり言うと…

* Outboxテーブルを見に行く👀
* 「未送信の行」を見つける🔎
* 外に送る（HTTP、キュー、イベント基盤など）📩
* 送れたら「送信済」にする✅

ポイントは、Relayは **業務処理（注文作成など）とは別プロセス**でもOKってこと✨
業務側は「Outboxに積む」までで役目終了、Relayが「配送」を担当します🍱🚚

---

## 2) ポーリングって何？⏰🐾

![Polling Clock](./picture/outbox_cs_study_015_polling_clock.png)

ポーリングは「一定間隔で見回りする」方式です👮‍♀️✨

* 例：**1秒ごと / 5秒ごと / 10秒ごと**にOutboxをチェック
* 未送信があればまとめて処理（バッチ）📦📦📦
* なければ寝る（待つ）💤

最初はこれで十分強いです💪🙂
（後でイベント駆動にしたくなっても、まず動くものを作るのが勝ち！🏁）

---

## 3) Relayの「最小責務」セット ✅📦

Relayの責務は、最低限これだけでOKです🙂✨

1. **未送信を取る**（Pendingだけ）🔎
2. **二重に取られないようにする**（Claimする）✋
3. **送る**📩
4. **結果を書く**（Sent / Failed）📝

この「2」が超重要です⚠️
ここが弱いと、Relayを2つ動かした瞬間に二重送信が起きます👯💥

---

## 4) ポーリングRelayの基本フロー 🗺️🚚

![Relay Polling](./picture/outbox_cs_study_015_relay_polling.png)

まずは王道の流れを図でつかみましょう👇

1. **Claim（担当者決め）**✋

* Pendingを「Processing」に変える
* ついでに「誰が担当？」情報（LockIdなど）を書く

2. **送信する**📩

* DBの外に送る（失敗することもある😵‍💫）

3. **完了を書く**✅

* 成功：Sent
* 失敗：Failed（＋エラー情報、リトライ回数など）

---

## 5) 二重送信を防ぐコツ：Claim（取り分け）設計 ✋📦

## 5-1) なぜClaimが必要？😱

![Double Claim Accident](./picture/outbox_cs_study_015_double_claim_accident.png)

Relayが2つ同時に動くと…

* Relay A「このPendingいいね！」
* Relay B「私もそれ見つけた！」
* 2人が同じメッセージを送る👯📩📩

これを避けるのがClaimです🧷✨
「この行は私が担当ね！」を、DBで先に確定させます✅

---

## 5-2) Claimの代表パターン（初心者向け）🧠✨

![Claim Lock](./picture/outbox_cs_study_015_claim_lock_visual.png)

おすすめはこの形👇

* ステータス：`Pending → Processing → Sent/Failed`
* Processingにした行だけを、そのRelayが送る🚚

さらに実運用では、**LockedUntil（期限）**を付けるのが強いです⏳
クラッシュしても「期限切れなら回収してOK」にできます🧹✨

---

## 5-3) SQL Server系の考え方（キュー実装で定番）🧱

SQL Serverには「ロック競合を避けつつ、キューっぽく読む」ためのヒントが用意されています。
たとえば **`READPAST`** は「他トランザクションにロックされてる行は読み飛ばす」挙動で、**ワークキュー実装で主に使う**と明記されています。([Microsoft Learn][1])
また **`UPDLOCK`** は「読み取り時に更新ロックを取って、トランザクション終了まで保持」します。([Microsoft Learn][1])

> つまり「取り分け中の行に他が触れにくい」状態を作りやすい、ってことです🙂🛡️

※ただし、ヒントは強力なので「まずは概念理解」が最優先でOKです🙆‍♀️✨（SQL最適化は後で磨けます）

---

## 5-4) PostgreSQL系なら SKIP LOCKED が超有名 🐘🔒

PostgreSQLは `FOR UPDATE SKIP LOCKED` がまさに「キューっぽいテーブルに複数コンシューマでアクセスするときのロック競合回避に使える」と説明されています。([PostgreSQL][2])

> 「ロックできない行は飛ばす」＝複数Relayでの取り合いに強い💪✨

---

## 6) 1回に何件取る？（バッチサイズ）📦📦📦

![Batch Processing](./picture/outbox_cs_study_015_batch_processing.png)

## 6-1) バッチサイズの目安（最初のおすすめ）🙂✨

最初はシンプルに👇

* バッチサイズ：**50〜200件**くらい
* ポーリング間隔：**1〜5秒**くらい

理由：

* 小さすぎるとDB往復が多すぎる🏃‍♀️💦
* 大きすぎると1回の処理が重くなって遅延が増える🐢💤

> まずは「小さめ〜中くらい」で始めて、メトリクス見て調整が安全です📈✨

---

## 6-2) “未送信ゼロ”のときどうする？😴

ずっと高速ループするとCPUがムダに燃えます🔥
なので「なければ待つ」が基本💤

* 未送信が0件 → **Delayして待つ**
* いっぱいある → **連続で処理してOK**

---

## 7) 送信の順序って気にする？🔁🙂

結論：**最初は気にしすぎなくてOK**です🙆‍♀️✨

ただし「同じ集約（同じ注文IDなど）」の順序が必要なケースだけ注意⚠️
その場合の初心者向けルール👇

* **グループキー（例：OrderId）ごとに順序を守る**
* それ以外は多少前後してもOKにする（設計で吸収）🙂

順序を厳密にすると難易度が跳ねます🧗‍♀️💦
（必要になったら、あとで “同一キーは直列化” に進むのが王道です✨）

---

## 8) 「送信中に落ちた」問題と LockedUntil 🧯⏳

![LockedUntil Recovery](./picture/outbox_cs_study_015_locked_until_recovery.png)

Relayは落ちます。ネットも落ちます。普通です😇🌩️

そこで **Processingが永遠に残る**のを防ぎます👇

* `LockedUntil` を持つ（例：今から2分後）⏳
* Relayが落ちたら、期限が切れたProcessingは **再回収OK** にする🧹
* 再回収のときは `RetryCount` を増やす🔁

これで「詰まり」が減ります✨

---

## 9) Relay設計テンプレ（超実用）📌✨

最低限この列があると、運用がかなり楽です🙂

* `Status`：Pending / Processing / Sent / Failed
* `LockedUntil`：処理権の期限⏳
* `LockId`：担当Relayの識別子🪪
* `RetryCount`：何回目？🔁
* `LastError`：最後の失敗理由（短めでOK）🧾

---

## 10) 擬似コードで全体像（まだ実装しないけどイメージ）🧑‍💻✨

```csharp
while (!cancellationToken.IsCancellationRequested)
{
    // 1) Claim: Pending を Processing に取り分け（期限つき）
    var messages = ClaimPending(batchSize: 100, lockFor: TimeSpan.FromMinutes(2));

    if (messages.Count == 0)
    {
        await Task.Delay(TimeSpan.FromSeconds(2), cancellationToken);
        continue;
    }

    // 2) Send: DBの外へ送る
    foreach (var msg in messages)
    {
        try
        {
            await SendAsync(msg, cancellationToken);
            MarkSent(msg);
        }
        catch (Exception ex)
        {
            MarkFailedOrRetry(msg, ex);
        }
    }
}
```

この「Claim → Send → Mark」の分離が、ポーリングRelayの芯です🧠✨
（次章でこれをちゃんと `BackgroundService` で形にします🚀）([Microsoft Learn][3])

---

## 11) よくある落とし穴（初心者がハマりやすい）🕳️😵‍💫

## 落とし穴A：Claimせずに「SELECTして送る」😱

* ほぼ確実に二重送信が起きます👯📩

✅対策：**必ずClaim**（Status更新などで担当確定）

---

## 落とし穴B：送信をDBトランザクションの中でやる😵‍💫

* 外部送信が遅いと、DBロックが長くなる🔒💦
* 詰まりやすい

✅対策：**Claimのトランザクションは短く**、送信は外で📩

---

## 落とし穴C：Processingが詰んで永遠に残る🧊

* Relayが落ちると起きがち

✅対策：`LockedUntil` で回収🧹⏳

---

## 12) Copilot / Codexに頼むと良い“質問”例 🤖💡

（そのまま貼ってOK系✨）

* 「Outbox Relay の Claim を、Processing + LockedUntil 方式で設計したい。テーブル設計案を出して」🧾
* 「SQL Serverでワークキューっぽく Pending を複数ワーカーで安全に取るSQL例を3案」🧱([Microsoft Learn][1])
* 「PostgreSQLで SKIP LOCKED を使った取り分けSQL例を説明して」🐘([PostgreSQL][2])
* 「.NETのWorker Service / BackgroundServiceで、ポーリングループの基本形を作って」🧑‍💻([Microsoft Learn][4])

---

## 13) ミニ演習 🎓📝（設計だけでOK）

次の問いに、自分の言葉で答えられたら勝ちです🏆✨

1. Relayが2つ動いたとき、二重送信を防ぐために **何をDBに書いて担当確定する？** ✋
2. Processingが残りっぱなしになるのを防ぐために、**どんな列が欲しい？** ⏳
3. バッチサイズ100、間隔2秒にした理由を一言で説明してみよう🙂📦⏰

---

## 14) この章のまとめ（覚える3つだけ）🧠✨

* ポーリングは「定期見回り」⏰🐾
* Relayの肝は **Claim（取り分け）** ✋📦
* **LockedUntil** があると、落ちても復活しやすい🧹⏳

次章では、この設計を **Worker/BackgroundService** で「動く配送係」にしていきます🚚💨([Microsoft Learn][3])

[1]: https://learn.microsoft.com/en-us/sql/t-sql/queries/hints-transact-sql-table?view=sql-server-ver17 "Table Hints (Transact-SQL) - SQL Server | Microsoft Learn"
[2]: https://www.postgresql.org/docs/current/sql-select.html "PostgreSQL: Documentation: 18: SELECT"
[3]: https://learn.microsoft.com/en-us/dotnet/core/extensions/workers "Worker Services - .NET | Microsoft Learn"
[4]: https://learn.microsoft.com/en-us/dotnet/core/extensions/windows-service?utm_source=chatgpt.com "Create Windows Service using BackgroundService - .NET"
