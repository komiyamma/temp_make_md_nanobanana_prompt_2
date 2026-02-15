# 第08章：DRYの落とし穴（やりすぎ注意！）🐙⚠️

この章は「DRYができる人」から「**DRYを“判断できる人”**」にレベルアップする回だよ〜😊💪✨
DRYって、効かせると超強いけど、**やりすぎると逆に保守が地獄**になることがあるの…🥹🌪️

---

## 8.0 ゴール🎯✨

章の終わりに、これができるようになるよ👇😊

* 「似てるから共通化！」を**一旦ストップ**して、落ち着いて判断できる🧘‍♀️🛑
* 共通化するなら「どこに置く？」「どういう形にする？」が選べる🗂️🧠
* **Util地獄**（CommonUtil.csが肥大化するやつ）を回避できる🐘🔥
* DRYとYAGNIのバランスが取れる⚖️✨（未来に怯えすぎない！）

---

## 8.1 まず大前提：DRYは「コピペ禁止」じゃなくて「知識（ルール）の重複禁止」😺🧻

DRYの本体は、ざっくり言うとこう👇

* **同じ“知識/ルール”が複数箇所に散るのがダメ**🙅‍♀️
* だから「変更するときに直す場所が増える」→バグりやすい💥
* 逆に「同じ知識を1箇所に集める」→変更が楽になる✨

このニュアンス（知識の一意化）が大事だよ〜🧠✨ ([ウィキペディア][1])

---

## 8.2 落とし穴①：「似てる」≠「同じルール」😵‍💫🌀

![similar_but_different_fruit](./picture/dry_cs_study_008_similar_but_different_fruit.png)


![dry_cs_study_008_wrong_abstraction](./picture/dry_cs_study_008_wrong_abstraction.png)


ここ、初心者が一番ハマるやつ！！😭💦
**見た目が似てる**だけで共通化すると、あとで爆発する💣

### 例：送料計算（見た目そっくり、でもルールが違う）🚚📦

* 国内：5000円以上で送料無料
* 海外：10000円以上で送料無料＋関税（ざっくり例）

「送料だし一緒でしょ〜」で共通化すると…👇

```csharp
public static int CalcShipping(int amount, bool isOverseas, bool includeDuty)
{
    // え、条件どんどん増える…😇
    if (!isOverseas)
    {
        return amount >= 5000 ? 0 : 500;
    }
    else
    {
        var shipping = amount >= 10000 ? 0 : 1200;
        if (includeDuty) shipping += (int)(amount * 0.1);
        return shipping;
    }
}
```

**ダメな匂いポイント**👃💥

* `bool`フラグが増える（未来で地獄になる合図）🚨
* “国内”と“海外”の仕様変更が入った瞬間、1メソッドがカオスに🌀
* 呼び出し側が読めない：「includeDutyって何の義務…？」😇

✅ **結論**：
似てる処理でも、**変わる理由（変更要因）が違う**なら、同居させない方が安全だよ😊🧠

---

## 8.3 落とし穴②：共通化の目的は「コードを減らす」じゃない✂️❌➡️🧰✅

![generic_plug_fail](./picture/dry_cs_study_008_generic_plug_fail.png)


DRYで本当に欲しいのは「行数削減」じゃなくて👇

* **変更箇所を減らす**🧩
* **意味を集めて、読みやすくする**📖✨
* **ミスの入り口を減らす**🚪🔒

だから、こんな共通化は危険⚠️

### 「行数は減ったけど意味が消えた」例😶‍🌫️

```csharp
public static decimal Calc(decimal baseValue, decimal rate, bool roundDown, bool clampZero)
{
    var v = baseValue * rate;
    if (roundDown) v = Math.Floor(v);
    if (clampZero && v < 0) v = 0;
    return v;
}
```

これ、汎用っぽいけど…

* 割引？税？手数料？ポイント？何の計算？😵‍💫
* 呼び出しが「パラメータ暗号」になる🔐
* 将来ちょっと仕様が増えたらフラグ地獄👹

✅ **結論**：
「共通化＝汎用関数化」じゃないよ〜！
**“何のルールか”が読める形**が正解に近い😊✨

---

## 8.4 落とし穴③：Util地獄（CommonUtil.csが宇宙になる）🪐🐘🔥

![util_hell_garbage_bin](./picture/dry_cs_study_008_util_hell_garbage_bin.png)


![dry_cs_study_008_swiss_army_knife](./picture/dry_cs_study_008_swiss_army_knife.png)


DRYを頑張るほど、こうなりがち👇

* `CommonUtil`
* `Utils`
* `Helper`
* `Manager`

📦 **何でも入る箱**ができる → 肥大化 → 誰も触れない → 終わり😇

### Util地獄のサイン🚨

* ファイルがでかい（数千行）📜
* メソッド名が抽象的（`Process`, `Handle`, `DoStuff`）😵
* いろんな層から呼ばれる（UIからもDBからも呼ぶ）🧟‍♀️
* 変更が怖い（影響範囲が読めない）😱

### 回避テク（おすすめの“置き場所”）🗂️✨

**① ルールは「ドメイン寄り」に寄せる**💎
例：`Money`, `ShippingFee`, `DiscountPolicy` みたいに「意味のある名前」

**② “共通処理”じゃなく“共通ルール”にする**🧠
例：`IsFreeShippingEligible(amount)` みたいに意図が読めるやつ

**③ 迷ったら「近いところ」に置く**📍
遠くのUtilに投げるより、**使う場所の近く**に置いた方が保守しやすいことが多いよ😊

---

## 8.5 落とし穴④：YAGNI vs DRY（未来対応しすぎ問題）🔮⚖️

未来を見すぎると、こうなる👇

* 「将来、種類が増えるかも」→ 早すぎる抽象化😇
* 「今は2パターンだけど、拡張のためにStrategy！」→ 読みにくい…😭

YAGNIは「たぶん必要になる機能を先に作らない」って考え方だよ🧠
（“必要になってから作ろう” の合言葉） ([martinfowler.com][2])

### じゃあDRYはどうするの？🥺

![rule_of_three_traffic_light](./picture/dry_cs_study_008_rule_of_three_traffic_light.png)


ここで便利なのが、よく言われる **Rule of Three**（3回出たら抽出）🧩✨
2回は様子見、3回目で「パターン確定！」って判断しやすいんだよね😊 ([ウィキペディア][3])

✅ **覚え方**

* 1回：ただの実装
* 2回：たまたま似た
* 3回：だいたいルール（抽象化の材料が揃う）✨

---

## 8.6 DRYやりすぎを止める「判断の4軸」🧭✨

![judgment_compass](./picture/dry_cs_study_008_judgment_compass.png)


共通化したくなったら、この4つをチェックしてね👇😊

### 軸①：同じ理由で変わる？（変更要因が同じ？）🔁

* YES → 共通化しやすい
* NO → 一緒にすると爆発しやすい💥

### 軸②：呼び出し側が“文章”として読める？📖

* `Calc(total, 0.9m, true, true)` ← しんどい😇
* `ApplyMemberDiscount(total)` ← 最高😊✨

### 軸③：共通化で「分岐 or 引数」が増えない？🌿➡️🌪️

* フラグ増えたら黄色信号🚦
* フラグ2つ超えたら赤信号🚨（目安）

### 軸④：テストで“ルール同一”を証明できる？🧪

* 「同じルール」って言うなら、**同じテスト**が通るはず😊
* テストが分かれるなら、ルールも分かれてる可能性が高いよ✨
 
 ```mermaid
 flowchart TD
   Start([共通化したい？]) --> Q1{変更理由は同じ？<br>同じ仕様変更で変わる？}
   Q1 -- No ---> Stop([共通化しない🙅‍♀️])
   Q1 -- Yes --> Q2{読める？<br>命名できる？}
   Q2 -- No ---> Stop
   Q2 -- Yes --> Q3{分岐・引数が<br>増えすぎない？}
   Q3 -- No ---> Stop
   Q3 -- Yes --> Q4{テストで<br>ルール同一を証明できる？}
   Q4 -- No ---> Stop
   Q4 -- Yes --> Go([共通化OK！🙆‍♀️])
 ```
 
 ---

## 8.7 判断チェックリスト（実戦用）📋✅✨

共通化の前に、これに◯×つけてみてね😆💕

* [ ] 変更要因が同じ（同じ仕様変更が来る）🔁
* [ ] 名前でルールが説明できる（`ApplyXxx` / `IsXxx`）📛
* [ ] `bool`や`string`で挙動を切り替えない🚫
* [ ] 引数が増えすぎない（4つ以上は要注意）⚠️
* [ ] 呼び出し側が読みやすくなる📖✨
* [ ] テストが書きやすくなる🧪
* [ ] “今”の問題を解決している（未来の妄想だけで作ってない）🔮❌

✅ 目安：

* ◯が多い → 共通化してOK寄り😊
* ×が多い → まずは重複のままにする勇気💪✨（※これも判断力！）

---

## 8.8 クイズ：共通化する？しない？🧩😆

### Q1：会員割引とクーポン割引（どっちも「10%OFF」）🏷️

* 会員：常に10%OFF
* クーポン：10%OFFだけど「上限500円」あり

👉 共通化する？
**答え：しない寄り**🙅‍♀️
“10%”は同じでも、**ルールが違う（上限）**ので、同居させると分岐が増えやすい💦

---

### Q2：入力チェック（メールとユーザーID）📧🆔

* どっちも「空欄NG」
* どっちも「長すぎNG」

👉 共通化する？
**答え：する寄り**✅
“空欄NG” “長さ制限” は **共通の知識**になりやすい。
ただし「メール形式」みたいな固有ルールは別にするのが◎😊✨

---

### Q3：ログ出力（注文と決済）📝💳

* どっちも同じフォーマットでログ
* でも保存先が違うかもしれない（将来）

👉 共通化する？
**答え：今は小さく共通化でOK**✅
フォーマット部分だけ共通化して、保存先は呼び出し側に残す…みたいに
**“分離ライン”を引く**のがコツだよ😊✍️

---

## 8.9 ミニ演習：「悪い共通化」を“良い形”に直す🛠️✨

### お題：フラグ地獄の割引関数を救出する🆘

![flag_hell_maze](./picture/dry_cs_study_008_flag_hell_maze.png)


```csharp
public static int CalcDiscountedPrice(int price, bool isMember, bool isCampaign, bool roundDown)
{
    var rate = 1.0m;

    if (isMember) rate -= 0.1m;
    if (isCampaign) rate -= 0.05m;

    var result = price * rate;
    if (roundDown) result = Math.Floor(result);

    return (int)result;
}
```

#### ステップ課題（順番が大事だよ😊）🌸

1. **「何のルールが混ざってる？」を日本語で箇条書き**📝

   * 会員割引
   * キャンペーン割引
   * 端数処理

2. **“意図が読める”メソッドに分解**✂️

   * `ApplyMemberDiscount`
   * `ApplyCampaignDiscount`
   * `RoundDownYen` など

3. `bool` を消す（または減らす）🚫

   * 割引の組み合わせは「ポリシー」や「手順」で表現する

たとえば、まずはこういう形に寄せるだけで読みやすさが跳ねるよ📖✨

```csharp
public static int CalcMemberCampaignPrice(int price)
{
    var discounted = ApplyMemberDiscount(price);
    discounted = ApplyCampaignDiscount(discounted);
    return RoundDownYen(discounted);
}

private static decimal ApplyMemberDiscount(decimal price) => price * 0.9m;
private static decimal ApplyCampaignDiscount(decimal price) => price * 0.95m;
private static int RoundDownYen(decimal price) => (int)Math.Floor(price);
```

✅ これなら「何をしてるか」読める😊
（このあと発展で“割引の種類が増えたら？”って時に、初めて抽象化を考えればOK👌）

---

## 8.10 AI活用（Copilot / Codex）🤖💡 ※やりすぎ防止に使う！

AIは「共通化しろ！」って言いがちなので、**逆方向の質問**が強いよ😆✨

### 使えるプロンプト例🪄

* 「この2つの処理、**同じルールじゃない可能性**を列挙して」🕵️‍♀️
* 「この共通化、将来仕様が増えたら **どこが破綻する？**」💥
* 「この関数の `bool` 引数を無くすリファクタ案を3つ。**読みやすさ優先**で」📖
* 「“共通化しない方が良い理由”をレビュー観点で書いて」📝
* 「共通化するなら、**命名案を10個**（意図が読めるものだけ）」📛✨

あと、Visual Studio 2026は .NET 10 / C# 14 を前提にした開発が進めやすくて、リファクタ→実行の回転が上げやすいのが嬉しいポイントだよ🔁✨ ([Microsoft Learn][4])
さらに C# 14 では拡張メンバー周りが強化されてるけど、便利なほど“どこでも生やせる”ので、**置き場所の判断**がより大事になるよ〜🧠⚠️ ([Microsoft Learn][5])

（ついでに：Copilotにはアプリ最新化みたいな“エージェント系”の動きもあるので、AIに棚卸しさせて、人間が判断する流れがますます現実的になってきてるよ🤖🧺） ([Microsoft Learn][6])

---

## 8.11 まとめ🌸✨

* DRYは「コード」より「知識（ルール）」を1箇所に集める話🧠 ([ウィキペディア][1])
* 「似てる」だけで共通化すると、フラグ地獄・Util地獄になりやすい🐙🔥
* 判断は **変更要因 / 読みやすさ / 分岐・引数増 / テスト** の4軸🧭
* 未来対応しすぎはYAGNIで止める🔮🛑 ([martinfowler.com][2])
* 迷ったら Rule of Three（3回目で抽象化）も使えるよ😊✨ ([ウィキペディア][3])

---

次が「総合演習（プロジェクトで1周）」の章なら、ここで作ったチェックリストがめちゃ効くよ〜📋💕
続けて第9章（まとめプロジェクト）も同じ温度感で作っていけるけど、今はまず第8章の内容で一回“判断筋”を育てようね😊💪✨

[1]: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself?utm_source=chatgpt.com "Don't repeat yourself"
[2]: https://martinfowler.com/bliki/Yagni.html?utm_source=chatgpt.com "Yagni"
[3]: https://en.wikipedia.org/wiki/Rule_of_three_%28computer_programming%29?utm_source=chatgpt.com "Rule of three (computer programming)"
[4]: https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-notes?utm_source=chatgpt.com "Visual Studio 2026 Release Notes"
[5]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14?utm_source=chatgpt.com "What's new in C# 14"
[6]: https://learn.microsoft.com/en-us/dotnet/core/porting/github-copilot-app-modernization/overview?utm_source=chatgpt.com "GitHub Copilot app modernization overview"
