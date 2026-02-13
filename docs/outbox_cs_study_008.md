# 第08章：いつ使う？いつ使わない？判断のコツ 👀🌱

## 今日のゴール 🎯✨

* 「Outboxを入れるべき状況」 vs 「入れないほうが良い状況」を、**迷わず判断**できるようになる😊
* “便利そうだから全部Outbox”にならないように、**ちょうどいい境界線**を持つ📏✨
* 次章（Outboxテーブル設計）に入る前に、**採用判断の軸**を固める🧠💡

---

## 1) まず結論：Outboxが効くのは「DB更新＋外への副作用」がセットのとき 📦➡️📩

Outbox（Transactional Outbox）はざっくり言うと、

* **DB更新と同じトランザクションで「送るべきメッセージ」をDBに保存**しておき
* **あとから別プロセス（配送係）が送る**

…という形で、「DBは更新されたのに通知は飛んでない😱」みたいなズレを減らす考え方だよ🛡️✨ ([microservices.io][4])

---

## 2) 「使うべき」サイン ✅🌩️（このどれかに当てはまったら候補！）

![Decision Signs ABC](./picture/outbox_cs_study_008_decision_signs_abc.png)

## サインA：DB更新のたびに、外に“何か”をしたい 📤

例：

* メール送信📧
* 別サービスへイベント通知🔔
* キューに投入📬
* 外部APIへPOST🌐

これ、DBと送信先は**別世界**なので、失敗の組み合わせが増えるよね😵‍💫
→ Outboxの得意領域✨ ([microservices.io][4])

---

## サインB：送信が失敗しても「あとで必ず届けたい」 🔁📩

* 一時的なネットワーク不調🌧️
* 送信先の一時停止🛑
* タイムアウト⏳

こういう“よくある事故”に対して、**再試行（リトライ）前提**で設計したいなら相性◎😊

---

## サインC：サービスが分かれてる（境界がある）🧩🌍

* マイクロサービス
* 別チーム/別リポジトリ
* 別DB（または別スキーマ）

「非同期メッセージで整合性を取る」世界では、Outboxがよく採用されるよ📨✨ ([Microsoft Learn][5])

---

## サインD：ビジネス的に“通知漏れ”が致命的 💸😱

* 決済成功通知が消える
* 出荷指示が飛ばない
* 予約確定が相手に届かない

こういうのは「たまに落ちました」で済まないよね…🥶

---

## サインE：“同期API”で繋ぐと遅くなる/詰まる 🐢💥

* 相手が遅いと、自分も遅くなる
* 相手が落ちると、自分も巻き添え

だから「まずDBだけ確定させて、外への通知はあとで」って分離したくなる✂️✨

---

## 3) 「使わない（or 後回しでOK）」サイン 🙅‍♀️🌿

![Signs Not To Use](./picture/outbox_cs_study_008_signs_not_to_use.png)

## サイン1：単一アプリ内で完結してる 🏠

* 同じプロセス内で完結
* 外部に通知しない
* 送信が不要

→ Outboxを入れても、複雑さが増えるだけになりがち😅

---

## サイン2：失敗しても“ユーザーの再操作”で回復できる 🔁🙂

例：

* 画面で「再送」ボタンを押せる
* 多少の遅延が許される通知（例：お知らせ）

こういうのは、まずはシンプルに作ってからでもOK👍

---

## サイン3：結果が重要じゃない（ログ/メトリクス系）📊

* 監視ログ
* 解析用イベント

“取りこぼしゼロ”を目標にするとコストが跳ねるので、最初からOutboxで固めなくてもいい場面が多いよ🙂

---

## サイン4：導入コストが利益に見合わない 🧮💦

Outboxは「安心」を買う代わりに、増えるものがあるよ👇

* Outboxテーブル管理🧱
* 配送係（常駐/スケジュール）🚚
* リトライ・失敗管理🧯
* 監視（滞留数など）👀

「大事なところだけに使う」が上手な使い方になりやすい✨
“なんでもOutbox”は避けようね、って注意喚起もあるよ📣 ([squer.io][6])

---

## 4) 迷ったらこれ！判断フロー（初心者版）🧭✨

![Decision Flow](./picture/outbox_cs_study_008_decision_flow.png)

## Step 1：DB更新のあとに“外への副作用”ある？ 🌐

* ない → Outboxいらない可能性大🙆‍♀️
* ある → Step 2へ👇

## Step 2：その副作用が漏れると“事故”になる？ 😱

* 事故にならない（遅れてもOK/多少落ちてもOK）→ まず簡単に🙂
* 事故になる（お金/契約/在庫/予約）→ Step 3へ👇

## Step 3：相手が落ちても“あとで必ず届けたい”？ 🔁

* はい → Outbox候補📦✨
* いいえ（同期で失敗したら全体失敗でOK）→ 同期リトライ等で済むことも

## Step 4：重複が来ても耐えられる？（後で冪等性を入れる覚悟）🧷

Outboxはだいたい “最低1回は送る（重複あり得る）” を前提にすることが多いよ📬🔁
なので「重複が来ても大丈夫」にできるかが大事🛡️ ([Microsoft Learn][7])

---

## 5) “小さく導入”の境界線 📏🧡（ここ超大事！）

![Small Start Steps](./picture/outbox_cs_study_008_small_start_steps.png)

Outboxは、いきなり全部に入れなくてOK🙌
おすすめの“小さく始める”ラインはこれ👇

## ✅ ライン1：まずは「最重要イベント」だけ 🎯

例：

* 注文確定
* 決済確定
* 予約確定

“漏れたら困る順”に、Outbox適用を増やすのが安全✨

## ✅ ライン2：送信先は最初は「偽ブローカー」でもOK 🖥️

* まずはコンソール出力でもOK（流れ確認）
* そのあと本物のキュー/HTTPへ差し替え🔁

## ✅ ライン3：配送係は .NET の Worker / BackgroundService でOK 🚚

「未送信を取りに行って送る」常駐処理は、.NETのWorker（ホスト＋DI＋ログ）で作りやすいよ🧑‍💻✨ ([Microsoft Learn][8])

（※.NETは現行だと .NET 10 がLTS扱いでサポート表に載ってるよ📌） ([Microsoft][9])

---

## 6) ケースで判断してみよう！📚🧠

![Case Study Quiz](./picture/outbox_cs_study_008_case_study_quiz.png)

## ケース①：注文確定 → 確認メール📧

* メール漏れはクレームになりやすい😢
* メールサーバは落ちることがある🌧️
  ✅ Outbox候補（あとで確実に送る）

## ケース②：注文確定 → 画面に「注文番号」を出す🧾

* これはDBの結果を返すだけ
  🙅‍♀️ Outbox不要（同期でOK）

## ケース③：決済成功 → 在庫引当（別サービス）📦

* 漏れると売れない/二重引当など事故が怖い😱
  ✅ Outbox候補（イベント通知の信頼性が欲しい）

## ケース④：ユーザー登録 → “歓迎のおすすめ通知”🔔

* 遅れてもOK
* 失敗しても致命的じゃない🙂
  △ 最初はOutboxなしでもOK（後で必要なら追加）

## ケース⑤：検索インデックス更新🔎

* 多少遅れてもOKなことが多い
* ただし「絶対に漏れたら困る要件」なら話は別
  △ 要件次第（最初はシンプル寄りが多い）

---

## 7) ミニ演習 ✍️✨（答えもセット）

## 演習1：次のうち、Outbox「推奨」なのはどれ？（○/△/×）

1. 注文確定→配送指示（別サービス）
2. 注文確定→画面に注文番号表示
3. パスワード変更→監査ログ保存（DB内のみ）
4. 予約確定→外部パートナーへ通知（HTTP）
5. 広告クリック→分析イベント送信（多少落ちてもOK）

**模範解答** ✅

1. ○（漏れたら事故＆外部通知）
2. ×（DB結果返すだけ）
3. ×（DB内だけならまず不要）
4. ○（外部通知で漏れが痛い）
5. △（要件次第。重要度が低いならまずシンプルに）

---

## 演習2：あなたのプロジェクトに当てはめる「判断シート」🗒️💡

次の質問に YES が多いほど、Outbox候補だよ😊

* DB更新のたびに外へ送る処理がある？
* 送信先は落ちる可能性がある？
* 送信漏れがビジネス事故になる？
* “あとで送る”でもユーザー体験的にOK？
* 重複が起きても対策（冪等性）できる？

---

## 8) AI活用（Copilot/Codex）で判断を速くする 🤖🧠✨

![AI Fail Pattern Analysis](./picture/outbox_cs_study_008_ai_fail_pattern.png)

## 使いどころ1：失敗パターン洗い出し⛈️

AIにこう聞くと便利👇

* 「DB更新＋外部送信で起きる失敗パターンを列挙して」
* 「それぞれの失敗が起きたときのユーザー影響も書いて」

## 使いどころ2：Outbox採用/非採用の理由を文章化📝

* 「この要件でOutboxを採用する理由を、初心者向けに短く説明して」
* 「採用しない場合の代替案（同期リトライ等）も出して」

## 最後に人間が見るポイント👀✅

* その“通知漏れ”は本当に事故か？
* “あとで送る”で要件を満たすか？
* 重複を許容できるか？（次の冪等性につながる！）

---

## 9) よくある誤解あるある 😵‍💫➡️🙂

## 誤解①：「Outboxなら完全に一回だけ送れるよね？」

→ だいたいは **“最低1回（重複あり得る）”** を前提にすることが多いよ📬🔁
だから、受け手側の冪等性が大事になる🧷✨ ([Microsoft Learn][7])

## 誤解②：「難しそう…だから分散トランザクション（二相コミット）で…」

分散トランザクションは、参加者が増えるほど運用も難しくなりがち😵‍💫
（調整役やロールバック、耐障害性など考えることが多い） ([martinfowler.com][10])
Outboxは「まずローカルDBで確実に残す」方向で、設計の形をシンプルにしやすい✨ ([microservices.io][4])

---

## まとめ 🧡📌

* Outboxが効くのは **「DB更新＋外部への副作用」** がセットのとき📦➡️📩 ([microservices.io][4])
* 送信漏れが事故になるなら、Outboxは強い味方🛡️✨
* でも“なんでもOutbox”は複雑さが増えがちなので、**重要なところから小さく**がコツ📏🌱 ([squer.io][6])
* 次章から、いよいよ **Outboxテーブル設計（ミニマム版）** に入るよ📦🧱

[1]: https://chatgpt.com/c/697e8d43-3614-83a8-b83a-77b955df2340 "状態遷移手書き演習"
[2]: https://chatgpt.com/c/696d0f55-9da0-8320-b777-d0aff4030dd8 "第14章 粒度ルール"
[3]: https://chatgpt.com/c/6980d354-63b0-83a6-b04d-f3efa515e6f3 "設計の優先度"
[4]: https://microservices.io/patterns/data/transactional-outbox.html?utm_source=chatgpt.com "Pattern: Transactional outbox"
[5]: https://learn.microsoft.com/en-us/dotnet/architecture/microservices/architect-microservice-container-applications/asynchronous-message-based-communication?utm_source=chatgpt.com "Asynchronous message-based communication - .NET"
[6]: https://www.squer.io/blog/stop-overusing-the-outbox-pattern?utm_source=chatgpt.com "Stop overusing the outbox pattern | Blog"
[7]: https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-outbox-cosmos?utm_source=chatgpt.com "Transactional Outbox pattern with Azure Cosmos DB"
[8]: https://learn.microsoft.com/en-us/dotnet/core/extensions/workers?utm_source=chatgpt.com "Worker Services - .NET"
[9]: https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core?utm_source=chatgpt.com "NET and .NET Core official support policy"
[10]: https://martinfowler.com/articles/patterns-of-distributed-systems/two-phase-commit.html?utm_source=chatgpt.com "Two-Phase Commit"
