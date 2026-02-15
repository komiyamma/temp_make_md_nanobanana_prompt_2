# 第01章：DRYってなに？「コピペがダメ」だけじゃないよ 😺🧻

## この章のゴール 🎯✨

* DRYを「コピペ禁止」じゃなくて、**“同じ知識（ルール）を複数に持たない”**って感覚でつかむ 🧠💡
* ありがちな例（税率・送料・割引・入力チェック）で、**“どこ直す？”がすぐ言える**ようになる 🗺️🛠️
* Copilotに「重複っぽいところ」を手伝ってもらいつつ、**最後は自分の目で判断**できるようになる 🤖👀✨

---

## DRYを一言でいうと？📌

![dry_cs_study_001_single_source](./picture/dry_cs_study_001_single_source.png)


DRYは、ざっくり言うと…

> **同じ“知識（ルール）”は、システムの中に1つだけ置こう** 🧩✨

たとえば「送料は500円」「税率は10%」「学生割引は2,000円以上で5%」みたいな“決まり”って、**変わりやすい**よね？💦
それがコードのあちこちに散らばってると、変更が入ったときに **直し忘れ** が起きて事故る…😇🔥
（DRYは「同じ情報の繰り返しを減らす」という考え方として整理されています） ([ウィキペディア][1])

そしてDRYの本質は「同じコードを消す」より **“同じ意味（知識）を1つにする”** って話に近いよ〜、っていう説明も有名です ✨ ([Mathias Verraes' Blog][2])

---

## よくあるDRYの勘違いあるある 🙈💦

### ❌「コピペしたら即アウト！同じ行があったら全部まとめよ！」

…ってすると、逆に危険なことがあるよ⚠️🐙（これは後半の章でしっかりやるけど、1章なので軽く！）

### ✅「同じ知識ならまとめる。見た目が似てても“知識が別”なら無理にまとめない」

![knowledge_vs_code](./picture/dry_cs_study_001_knowledge_vs_code.png)


* 見た目同じでも **意味が違う** → 一緒にすると未来に壊れやすい 😵‍💫
* 意味が同じで **一緒に変わる** → 一箇所に寄せると安全 💪✨

---

## まず体感！DRYが必要になる“あるあるストーリー”📦💸

たとえば、ネットショップっぽいミニアプリで…

* 税率：10% 🧾
* 送料：500円 🚚
* 割引：2,000円以上で5%オフ 🎟️
* 入力チェック：数量は1以上、金額は0以上 ✅

この「決まり（知識）」が、画面・計算・請求書・メール文面…いろんな場所に散ると…
ある日、送料が **500円→600円** に変更 😇

![dry_cs_study_001_domino_effect](./picture/dry_cs_study_001_domino_effect.png)


* A画面は直した ✅
* B画面は直し忘れた ❌
* 「人によって請求が違う」地獄が発生 🤯🔥

これがDRYが効く瞬間だよ〜！🌪️➡️🌿

---

## ミニ演習：コピペだらけ小アプリで「どこ直す？」を言語化しよ 📝✨

![refactor_cycle](./picture/dry_cs_study_001_refactor_cycle.png)


### やること（ゴール）🎯

このコードを読んで、次を言葉にしてね👇

1. **同じ知識（ルール）が何箇所にある？** 🏷️
2. ルール変更が来たら、**どこを直すべき？** 🔧
3. 直し忘れが起きると、**どんなバグになる？** 🐛💥

---

## 演習用コード（わざとDRYじゃない版）😈📄

（そのまま `Program.cs` に貼って実行OKだよ〜✨）

```csharp
using System;

static decimal CalcTotal_A(decimal subtotal, int quantity)
{
    if (quantity <= 0) throw new ArgumentException("数量は1以上で入力してください。");
    if (subtotal < 0) throw new ArgumentException("小計は0以上で入力してください。");

    // 税率10%
    var tax = subtotal * 0.10m;

    // 送料500円（小計が3000円以上なら無料）
    var shipping = subtotal >= 3000m ? 0m : 500m;

    // 割引：2000円以上で5%オフ
    var discount = subtotal >= 2000m ? subtotal * 0.05m : 0m;

    return subtotal + tax + shipping - discount;
}

static decimal CalcTotal_B(decimal subtotal, int quantity)
{
    if (quantity <= 0) throw new ArgumentException("数量は1以上で入力してください。");
    if (subtotal < 0) throw new ArgumentException("小計は0以上で入力してください。");

    // 税率10%
    var tax = subtotal * 0.10m;

    // 送料500円（小計が3000円以上なら無料）
    var shipping = subtotal >= 3000m ? 0m : 500m;

    // 割引：2000円以上で5%オフ
    var discount = subtotal >= 2000m ? subtotal * 0.05m : 0m;

    return subtotal + tax + shipping - discount;
}

Console.WriteLine("=== DRYミニ演習 ===");
var subtotal = 2500m;
var qty = 1;

Console.WriteLine($"A: {CalcTotal_A(subtotal, qty)}");
Console.WriteLine($"B: {CalcTotal_B(subtotal, qty)}");

// 想定変更：送料が500→600になったら…？😇
Console.WriteLine("送料が変わったら、どこ直す？🤔");
```

---

## 問題：このコードの「同じ知識（ルール）」ってどれ？🏷️🧠

ぱっと見で、最低でもこのへんが散ってるはず👇

* ✅ 入力チェック（数量・小計）
* ✅ 税率10%
* ✅ 送料（無料条件つき）
* ✅ 割引条件（2,000円以上で5%）

ここで大事なのは、**同じ“計算式”が2個ある**よりも、
**同じ“ルール”が2個ある**ことが危ないってことだよ〜🧯🔥

---

## 「どこ直す？」を言語化するコツ 🗣️✨

変更要求が来た時に、こう聞くとDRY脳になるよ👇

* 「このルールって、**このアプリ内で唯一の正解はどこ？**」🧭
* 「このルールが変わったら、**必ず一緒に変わる場所はどこ？**」🔁
* 「直し忘れたら、**ユーザーに何が起きる？**」😱

**“直し忘れが起きる形”になってたら、DRYの改善余地あり**だよ🌸✨

---

## AI活用：Copilotに「重複っぽい箇所を列挙して」って頼もう 🤖🧺

![ai_finding_duplicates](./picture/dry_cs_study_001_ai_finding_duplicates.png)


Copilotはリファクタの相談にも使えるよ（例：リファクタの考え方・アイデア出し） ([GitHub Docs][3])
あと「重複ロジックをまとめる」系の学習モジュールもあります 📚🤖 ([Microsoft Learn][4])

### おすすめプロンプト例（コピペOK）🧠💬

* 「このコードの **重複している“知識（ビジネスルール）”** を箇条書きで指摘して。根拠も添えて」
* 「送料が500→600に変わるとしたら、**バグが起きそうな箇所**を列挙して」
* 「“同じ意味のルール”と“たまたま似てるだけ”を分けて説明して」

### ただし！鵜呑みにしないチェック ✅👀

Copilotは便利だけど、最終的には自分で確認しよ〜！😌✨

* その指摘、本当に **同じ知識**？（一緒に変わる？）
* 変更が入った時に、**直す場所が1つに寄る？**
* 実行して、結果が同じか確認できる？（この章はまず実行でOK）🔁🏃‍♀️

（補足）Copilotには“公開コードに一致しそうな提案を抑制する”設定や、提案が公開コードに一致した場合の参照確認などの仕組みもあります 🔍🧾 ([GitHub Docs][5])

---

## まとめ：1章で持ち帰るDRY感覚 🎁🌸

* DRYは「同じコードを消す」より **“同じ知識（ルール）を1つにする”** が本質 🧠✨ ([Mathias Verraes' Blog][2])
* 「税率・送料・割引・入力チェック」みたいな**変わりやすい決まり**が散ると事故る 😇🔥
* AIは「候補出し」に強いけど、**最終判断は“同じ知識か？”で自分がやる** 🤖➡️👀

---

## 次章予告ちょい見せ 👀🔍

次の2章では、重複を「コピペ」「ルール」「データ」「例外」みたいに分類して、見つける精度を上げていくよ〜🏷️✨



[1]: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself?utm_source=chatgpt.com "Don't repeat yourself"
[2]: https://verraes.net/2014/08/dry-is-about-knowledge/?utm_source=chatgpt.com "DRY is about Knowledge"
[3]: https://docs.github.com/en/copilot/tutorials/refactor-code?utm_source=chatgpt.com "Refactoring code with GitHub Copilot"
[4]: https://learn.microsoft.com/en-us/training/modules/consolidate-duplicate-logic-github-copilot-agent/?utm_source=chatgpt.com "Consolidate Duplicate Logic using GitHub Copilot Agent"
[5]: https://docs.github.com/enterprise-cloud%40latest/copilot/managing-copilot/managing-copilot-as-an-individual-subscriber/managing-copilot-policies-as-an-individual-subscriber?utm_source=chatgpt.com "Managing GitHub Copilot policies as an individual subscriber"
