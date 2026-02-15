# 第02章：重複の種類を見分けよう 👀🔍（コピペ／条件分岐／データ／例外処理）

## 0. まずはイメージ🌸「重複＝同じ“知識”が散らばってる状態」🧠🧻

DRYって、**「同じコードを消す」**だけじゃなくて、もっと大事なのは **「同じルール（知識）を1か所にする」** って感覚だよ〜😊✨

たとえば「送料は500円」ってルールが3か所に書いてあると…
送料が600円に変わった瞬間、**3か所全部直さないと事故る**😇💥
これがDRYで避けたいやつ！

---

## 1. 今日のゴール🎯✨

この章が終わるころには…

* 「これって重複だ！」を **4種類に分類**できる 👀🏷️
* コードを見て「どこが危ない重複か」を言葉にできる 🗣️💡
* 修正はまだ先でもOK！まずは **見つけてラベル付け**できる 🙆‍♀️✨

---

## 2. 重複の4分類 🏷️✨（この章の主役）

![dry_cs_study_002_duplication_types](./picture/dry_cs_study_002_duplication_types.png)


重複にはだいたいこの4パターンがあるよ〜😊

1. **コピペ重複**（同じ処理が複数）📄
2. **ルール重複**（同じ条件・同じ計算が複数）🧮
3. **データ重複**（同じ文字列・ID・数値・列挙が複数）🏷️
4. **エラー重複**（同じtry/catch、同じログが複数）🚨

> 補足：コピペの重複は「コードクローン（code clone）」って呼ばれることもあるよ〜👯‍♀️📄 ([FSE Ritsumeikan][1])

---

## 3. 見分けるコツ：重複センサーON 👀⚡

![dry_cs_study_002_classification_flowchart](./picture/dry_cs_study_002_classification_flowchart.png)


迷ったら、この質問を自分にしてみてね😊

* 仕様変更が来たら、**何か所直す？**（2か所以上なら黄色信号🟡）
* Ctrl+Shift+F（全文検索）で同じ単語がいっぱい出る → **データ重複**っぽい🏷️
* 似たようなifがいろんな所に出る → **ルール重複**っぽい🧮
* try/catchがコピペされてる → **エラー重複**っぽい🚨
* “ちょっとだけ違う”のに説明が同じ → **ルール重複**の可能性大😵‍💫

---

## 4. 4種類を「あるある」で理解しよう😊✨

### 4-1. コピペ重複（同じ処理が複数）📄✂️

**特徴：見た目がほぼ同じ**（コピペしたのバレるやつ😆）

**ありがち例**

* 入力チェックが3か所に同じようにある
* 画面表示用の整形があちこちに同じようにある

**なにが困る？😇**

* バグ修正しても、**直し漏れ**が起きる💥
* 片方だけ微妙に変わって、挙動がズレる🌀

**見つけ方👀**

* 目視で「これ見たことある…」😳
* もしVisual StudioのEnterprise系が使えるなら、**Code Clone分析**で探せることもあるよ（メニューから重複コード検出の流れ）🔎 ([Stack Overflow][2])

---

### 4-2. ルール重複（同じ条件・同じ計算が複数）🧮🧠

**特徴：見た目は違うのに、説明が同じ**（ここが一番むずい！😵‍💫）

**ありがち例**

* 「会員なら10%引き」ロジックが2か所にある（片方は小数点切り上げ、片方は切り捨て…みたいな地獄😇）
* 「合計が5,000円以上なら送料無料」条件がいろんな所にある

**なにが困る？😇**

* ルール変更のときに**全部直す必要**がある
* 直し漏れで「注文画面では送料無料なのに、確定画面で送料が付く」みたいな事故が起きる🚚💥

**見つけ方👀**

* 「これって一言で説明できる？」→ できるなら同じルールかも🗣️
* 数式・閾値・条件が似てるifが散らばってたら要注意⚠️

---

### 4-3. データ重複（同じ文字列・ID・列挙が複数）🏷️📌

**特徴：魔法の文字／数字がそこら中にいる**🪄😈

**ありがち例**

* `"PAID"` が複数ファイルに出てくる
* `5000`（送料無料の閾値）を直接書いてる
* エラーメッセージがコピペされてる

**なにが困る？😇**

* `"Paid"` と `"PAID"` みたいに**表記ゆれ**が起きる
* 仕様変更で数値が変わったとき、直し漏れが出る💥

**見つけ方👀**

* Ctrl+Shift+Fで `"PAID"` とか `5000` を検索🔍
* “意味がある数値”が直書きされてたら、まず疑う🧐

---

### 4-4. エラー重複（同じtry/catch、同じログが複数）🚨🧯

**特徴：例外処理がコピペで増殖**🧫😇

**ありがち例**

* API呼び出しのたびに、同じtry/catch + 同じログ
* 例外握りつぶし（`catch { return false; }`）があちこちにある😱

**なにが困る？😇**

* ログ形式がバラバラになって、調査が地獄👻
* 例外を飲み込むと、原因不明の不具合になる💥

**見つけ方👀**

* try/catchの形が似てたらすぐ疑う🚨
* ログ文言が同じ（または似てる）のが散らばってる

---

## 5. ミニ演習：重複ラベルを付けよう🏷️✨（付箋を貼る気持ちで！）

次のコードを見て、コメントの `// TODO:` にラベルを付けてみてね😊
ラベルはこんな感じでOK👇

* `[COPY]` コピペ重複 📄
* `[RULE]` ルール重複 🧮
* `[DATA]` データ重複 🏷️
* `[ERROR]` エラー重複 🚨

```csharp
using System;

public static class Checkout
{
    public static int CalcTotalForMember(int subtotal)
    {
        // ① ルール：会員は10%引き（切り捨て）
        int discounted = (int)(subtotal * 0.9); // TODO: ラベル？
        int shipping = 0;

        // ② ルール：5000円以上で送料無料
        if (discounted >= 5000) shipping = 0;   // TODO: ラベル？
        else shipping = 500;                    // TODO: ラベル？

        // ③ データ：ステータス文字列
        string status = "PAID";                 // TODO: ラベル？

        return discounted + shipping;
    }

    public static int CalcTotalForGuest(int subtotal)
    {
        // ④ 似た処理：非会員は割引なし
        int discounted = subtotal;              // TODO: ラベル？（重複？）

        int shipping = 0;

        // ⑤ ルール：5000円以上で送料無料（また出た）
        if (discounted >= 5000) shipping = 0;   // TODO: ラベル？
        else shipping = 500;                    // TODO: ラベル？

        // ⑥ データ：同じステータス文字列（また出た）
        string status = "PAID";                 // TODO: ラベル？

        return discounted + shipping;
    }

    public static bool SaveOrder(string orderId, int amount)
    {
        try
        {
            // ⑦ コピペっぽいログ
            Console.WriteLine($"[INFO] Saving order... id={orderId}, amount={amount}"); // TODO: ラベル？

            // ここでは保存成功とする（例）
            return true;
        }
        catch (Exception ex)
        {
            // ⑧ 例外処理：ログしてfalse返す（よくある形）
            Console.WriteLine($"[ERROR] Save failed: {ex.Message}"); // TODO: ラベル？
            return false;
        }
    }

    public static bool SavePayment(string paymentId, int amount)
    {
        try
        {
            // ⑨ ⑦とほぼ同じログ（コピペ感）
            Console.WriteLine($"[INFO] Saving payment... id={paymentId}, amount={amount}"); // TODO: ラベル？

            return true;
        }
        catch (Exception ex)
        {
            // ⑩ ⑧と同じ例外処理
            Console.WriteLine($"[ERROR] Save failed: {ex.Message}"); // TODO: ラベル？
            return false;
        }
    }
}
```

### 模範ラベル（答え合わせ）✅✨

* ① `[RULE]`（会員10%引き＝ルール）🧮
* ② `[RULE]`（送料無料判定＝ルール）🧮
* ③ `[DATA]`（"PAID"＝データ）🏷️
* ④ 状態によるけど、**「割引計算の考え方が分かれてる」なら** `[RULE]` 寄り（会員/非会員の価格ルール）🧮
* ⑤ `[RULE]` 🧮 / ⑥ `[DATA]` 🏷️
* ⑦ `[COPY]`（似たログが増える）📄
* ⑧ `[ERROR]`（例外処理の型が増殖）🚨
* ⑨ `[COPY]` 📄（⑦とほぼ同じ）
* ⑩ `[ERROR]` 🚨（⑧と同じ）

> ポイント：**「同じ“意味”が増えてる」＝ルール重複**、**「同じ“値”が増えてる」＝データ重複**、**「同じ“形”が増えてる」＝コピペ/エラー重複** って覚えると強いよ💪✨

---

## 6. AI活用（Copilot/Codex）🤖✨：この章では“棚卸し係”にする

AIはめっちゃ便利だけど、**判断はあなた**がやるのが大事だよ〜😊🌸

### 使える頼み方テンプレ🧠🧾

* 「このファイルの重複っぽい箇所を列挙して、**4分類で**ラベル付けして」🏷️
* 「同じルールが散らばってそうな条件式（if）を探して、候補を教えて」🧮
* 「“文字列の直書き”を一覧にして、定数化候補を提案して」🏷️
* 「try/catchの重複パターンを探して、共通化案を3つ出して」🚨

### ひっかけ注意⚠️😇

* AIは「似てる＝同じ」と決めつけがち！
  **似てるけど別ルール**ってことも普通にあるよ（次章以降で判断力UPするよ✨）

---

## 7. 今日のまとめ🎀✨

* 重複は4種類：`コピペ / ルール / データ / エラー` 🏷️
* DRYは「同じ知識を1か所に」🧠🧻
* この章は **“消す”より先に“見分ける”** ができたら勝ち😊🎯

おつかれさま〜！🌸✨
次の第3章で、いよいよ「メソッド抽出」で気持ちよく消していくよ✂️🧩😺

※参考（最新の開発環境まわり）：Visual Studio 2026は .NET 10 / C# 14 をサポートする、といった案内がMicrosoft Learnのリリースノートにあるよ。([learn.microsoft.com][3])

[1]: https://www.fse.cs.ritsumei.ac.jp/ssr2013/clone.html?utm_source=chatgpt.com "コードクローンパターン"
[2]: https://stackoverflow.com/questions/77113392/how-to-identify-duplicate-code-in-visual-studio-2022?utm_source=chatgpt.com "How to identify duplicate code in Visual Studio 2022"
[3]: https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-notes?utm_source=chatgpt.com "Visual Studio 2026 Release Notes"
