# 第04章：AI（Copilot/Codex系）を“安全に使う”流れ 🤖✅

## 今日のゴール 🎯✨

AIに「うまく頼るところ」と「絶対に人が守るところ」を分けて、Outbox実装で事故りにくい開発の型を身につけるよ〜💪💕

---

## 4.1 AIは“爆速だけど、責任は取らない相棒”🏎️💨🧑‍🤝‍🧑

AIは、雛形づくり・アイデア出し・テスト観点の洗い出しが得意だよ✨
でも、**それっぽいウソ**や**危ない実装**も平気で混ぜてくることがあるのが注意ポイント⚠️（特にセキュリティや例外処理）

GitHubのガイドでも「コードはそれっぽく見えても安全とは限らないから、セキュアコーディングとレビューが必要だよ」と明確に言ってるよ🛡️([GitHub Docs][1])

---

## 4.2 まず“お願いの仕方”を固定する 🧩💬

AIに丸投げするとブレるので、毎回この順番で頼むと安定しやすいよ〜✅

1. **要件の確認**（不足を質問させる）❓
2. **設計のたたき台**（箇条書きで）🗺️
3. **雛形コード**（コメント多めで）🧱
4. **テスト案＆失敗パターン**（表っぽく）🧪
5. **レビュー観点チェック**（チェックリストで）📝

---

## 4.3 AIに頼んでOKなこと ✅🤖

Outbox文脈だと、ここはAIがめちゃ頼れる✨

* 雛形生成（DTO、簡単なRepository、BackgroundServiceの骨組み）🧱
* **失敗パターンの洗い出し**（タイムアウト、重複、部分成功、再実行…）⛈️
* テストケース案（正常系/異常系/境界値）🧪
* ログに入れるべき項目案（OutboxId、相関ID、リトライ回数など）🧵
* “読みやすい命名”提案（イベント名、ハンドラ名）🏷️

---

## 4.4 AIに頼んじゃダメ（または“人が最終決定”）なこと 👀⚠️

Outboxで事故が起きやすいのは、だいたいここ👇
ここはAIの案を参考にしても、**最後は人が決める**のが鉄則だよ🍙🔒

* **トランザクション範囲**（どこからどこまで同一トランザクション？）🔒
* **再試行（リトライ）の方針**（回数・間隔・バックオフ）🔁⏳
* **冪等性の設計**（重複が来ても1回にする）🧷
* **「At-least-once前提」かどうか**（“必ず1回だけ”は危険）📮
* **外部送信の扱い**（DB保存と同時にHTTP送る、を同一Txでやらない）🚫🌍

---

## 4.5 この教材で毎回使う「AIレビュー用チェックリスト」📝✅

AIが出したコードを読むときは、毎回これを“指差し確認”しよう〜👆😺

### 🔒 トランザクション（超重要）

* [ ] **業務テーブル更新**と**Outbox追加**が「同じTx」になってる？🍙
* [ ] Txの中で **外部通信（HTTP/Queue）** してない？してたら危険🚫📡
* [ ] 例外が起きたとき、ちゃんとロールバックされる？🧯

### 🔁 リトライ（事故りやすい）

* [ ] リトライ回数が無限になってない？♾️🙅‍♀️
* [ ] 失敗理由がログに残る？（例外握りつぶしNG）💥🪵
* [ ] バックオフ（だんだん待つ）や間隔が雑すぎない？⏳

### 🧷 冪等性（重複に勝つ）

* [ ] “同じOutboxIdが2回来ても1回扱い”の発想がある？🔁➡️1️⃣
* [ ] 受け手側の重複排除の道筋がある？📥🛡️

### 🧱 セキュリティ＆安全

* [ ] パスワードやトークンがハードコードされてない？🔑🙈
* [ ] SQLが文字列連結になってない？（インジェクション注意）🧨
  GitHubの責任ある利用ガイドでも「ハードコードパスワードやSQLインジェクションみたいな典型事故に注意してレビューしてね」と書いてあるよ🛡️([GitHub Docs][1])

---

## 4.6 “危ない実装”の典型パターン集 🚨🧯

### パターンA：トランザクション中に外へ送る（やりがち）😱

「DB保存できたのに送信失敗」「送信できたのにDB失敗」みたいな地獄の入口…💀

```csharp
// ❌ やりがち：DB更新の途中で外部送信してる
using var tx = await db.Database.BeginTransactionAsync();

db.Orders.Add(order);
await db.SaveChangesAsync();

// ここでHTTP送信とかQueue送信すると、失敗時に整合が壊れやすい😱
await httpClient.PostAsJsonAsync("/notify", new { orderId = order.Id });

await tx.CommitAsync();
```

### パターンB：Outboxに積んで、送信は後で（こっち）📦➡️📩

```csharp
// ✅ まずはDB内で完結：Orders + Outbox を同じTxで保存
using var tx = await db.Database.BeginTransactionAsync();

db.Orders.Add(order);
db.OutboxMessages.Add(new OutboxMessage { /* 送る内容を積む */ });

await db.SaveChangesAsync();
await tx.CommitAsync();

// 送信は“配送係(Worker)”が後でやる🚚
```

---

## 4.7 AIに渡す情報は“最小限”が基本 🙈📏

AIチャットに貼る内容が増えるほど、事故の芽も増えるよ🌱💦

* ✅ **必要最小限のコード断片**だけ貼る（丸ごと貼らない）✂️
* ✅ **秘密情報（鍵/トークン/接続文字列）**は絶対貼らない🔑🙅‍♀️
* ✅ 仕様は「箇条書き + 例」くらいにする📝

GitHub Copilotは設定によって、入力したプロンプトや提案が「収集・保持され、さらにMicrosoftと共有されうる」ことが明記されていて、ON/OFFを選べるよ⚙️([GitHub Docs][2])
また、GitHubの設定では「公開コードに一致する提案を許可する/ブロックする」や「プロンプト・提案の収集保持を許可する/ブロックする」などの制御も案内されてるよ🔧([GitHub Docs][3])

---

## 4.8 “プロンプト注入”に気をつける 🧨🧠

最近よくあるのがこれ👇
**見た目はただのテキスト（READMEやIssueやログ）なのに、AIにだけ効く“悪い指示”が混ざってて、トークン漏えい・機密ファイル漏えい・意図しないコマンド実行につながる**やつ😱

VS Code周りでも、間接的なプロンプト注入で「GitHubトークンや機密ファイルの露出」や「ユーザーの明示的な同意なしの任意コード実行」につながりうる、と注意喚起されてるよ⚠️([The GitHub Blog][4])

### だからルールはこれだけ覚えてね👶✨

* ✅ AIが「このコマンド実行して」って言っても、**そのまま実行しない**（まず読む）👀
* ✅ 外部から来た文章（Issue/PR/コピペ/ログ）をAIに入れるときは“毒が混ざるかも”前提☠️
* ✅ “秘密情報に触れそうな操作”はAIに任せない🔒

---

## 4.9 すぐ使える「お願いテンプレ」3つ 🧁💬

### テンプレ①：設計たたき台（まずは箇条書き）

```text
目的：Outboxパターンを実装したい（C#）
状況：Ordersテーブル更新とOutbox保存を同一Txにしたい
制約：外部送信はTxの外。At-least-once前提。冪等性が必要
お願い：
1) 主要コンポーネント（書き込み側/Outbox/配送係/送信アダプタ）を箇条書きで
2) 失敗パターンを10個、対策も一言で
3) 最後にレビュー用チェックリストを作って
```

### テンプレ②：雛形コード（コメント多め）

```text
次の構成の“雛形”だけ作って：
- Orders作成ユースケース
- OutboxMessageエンティティ（最低限）
- 同一TxでOrders+Outboxを保存する処理
条件：
- 例外時にロールバックされることが分かる書き方
- 外部送信処理は書かない（Outboxに積むだけ）
- 重要ポイントにコメントを入れて
```

### テンプレ③：テスト観点（表で）

```text
Outboxの書き込み側について、テスト観点を表形式で出して：
列：ケース名 / 事前条件 / 操作 / 期待結果 / 追加で見るログ
最低：
- 正常系
- DB保存失敗
- Outbox保存失敗
- 途中例外
- 同じ操作を2回実行（冪等性の前提に触れる）
```

---

## 4.10 この章で出てきた代表ツール名（1回だけ）📌🤖

* GitHub Copilot（提供：GitHub）は、個人設定で「プロンプト/提案の収集保持」などを調整できるよ⚙️([GitHub Docs][2])
* Codex（提供：OpenAI）はIDE拡張として使えて、エージェント的にコードを読んだり編集したりもできるよ🧠✨([OpenAI Developer Hub][5])
* Visual Studioなど（提供：Microsoft）側でもAI/オンライン機能にはプライバシー説明が用意されてることが多いよ🔍🪟([Microsoft Learn][6])

---

## 4.11 ミニ演習（10〜15分）⏱️✍️

### 演習4-1：失敗パターンをAIに出させて“自分の言葉で”直す 🌩️➡️🧠

1. AIに「Outboxで起きる失敗パターン10個」を出してもらう🤖
2. それを見て、**自分の言葉で**「この教材のチェックリストに追加するならどれ？」を3つ選ぶ📝
3. その3つについて「どう検知する？（ログ/メトリクス）」も一言書く📈

### 演習4-2：危険コードを見抜く目を作る 👀🧯

1. AIに「Outbox実装のダメな例」を作らせる（わざと）😈
2. 4.5のチェックリストで、**どこがアウトか**に赤ペン入れる🟥✍️
3. “Txの外へ出す”形に書き直す（擬似コードでOK）✅

---

[1]: https://docs.github.com/en/copilot/responsible-use/copilot-coding-agent "Responsible use of GitHub Copilot coding agent on GitHub.com - GitHub Docs"
[2]: https://docs.github.com/copilot/how-tos/manage-your-account/managing-copilot-policies-as-an-individual-subscriber "Managing GitHub Copilot policies as an individual subscriber - GitHub Docs"
[3]: https://docs.github.com/copilot/configuring-github-copilot/configuring-github-copilot-in-your-environment?tool=visualstudio "Configuring GitHub Copilot in your environment - GitHub Docs"
[4]: https://github.blog/security/vulnerability-research/safeguarding-vs-code-against-prompt-injections/ "Safeguarding VS Code against prompt injections - The GitHub Blog"
[5]: https://developers.openai.com/codex/ide/ "Codex IDE extension"
[6]: https://learn.microsoft.com/en-us/visualstudio/ide/intellicode-privacy?view=visualstudio&utm_source=chatgpt.com "IntelliCode privacy - Visual Studio (Windows)"
