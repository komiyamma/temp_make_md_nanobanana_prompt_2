# 第11章：値オブジェクト（Value Object）①：Moneyを作る💰💎

この章は「**お金を“ただのdecimal”にしない**」練習だよ〜🙂✨
`Money` を作って、**不変条件を“型の中”に閉じ込める**体験をしよう🛡️🎀
（C# 14 / .NET 10 が現行ラインだよ） ([Microsoft Learn][1])

---

## 1) 今日のゴール🎯✨

![Money VO](./picture/invariants_cs_study_011_money.png)


できるようになること👇

* `Money` が **値で同一性を持つ**（Value Object）って説明できる🙂💎 ([Microsoft Learn][2])
* `Money` を **不変（immutable）**にして、壊れた金額を作らせない🔒❄️
* **通貨＋金額＋丸め**のルールを `Money` の中に入れられる💰📌
* **足し算・引き算**で「通貨が違う」事故を防げる🚫💥

---

## 2) まず「Moneyの仕様」を決めよっか📝💡

![money_blueprint](./picture/invariants_cs_study_011_money_blueprint.png)



`Money` を作る前に、最低限これを決めると迷子にならないよ🥰

### ✅ 仕様その1：通貨はISO 4217の3文字コードにする💱

例：`JPY` `USD` `EUR` みたいなやつね✨（ISO 4217） ([ISO][3])
👉 ルール：**英字3文字・大文字**だけ許可

### ✅ 仕様その2：金額は decimal を使う💎

お金系は `double` じゃなくて `decimal` が基本🫶
理由：10進数の計算に強くて、金融計算向きって公式でも明言されてるよ✨ ([Microsoft Learn][4])

### ✅ 仕様その3：この章では「支払い金額」用途で **負数は禁止**🙅‍♀️

サブスク料金や商品価格って、通常マイナスはおかしいよね？🙂
（残高や差額みたいに負数が必要な世界は、後で “用途別VO” に分ければOK🎀）

### ✅ 仕様その4：小数点以下は「通貨の桁」に合わせる🔢

* JPY：0桁
* USD：2桁
* BHD：3桁 …など（ISO 4217に minor unit がある） ([ウィキペディア][5])

この章では簡単にするために👇の方針にするよ：

* `Money` は **通貨ごとの小数桁を“設定で渡す”**（後で拡張しやすい）

### ✅ 仕様その5：丸めは “ToEven（銀行丸め）” をデフォにする🏦

.NET の `Round` はデフォが **MidpointRounding.ToEven**（いわゆる銀行丸め）だよ✨ ([Microsoft Learn][6])

---

## 3) 設計の狙い：decimal直渡しの何が怖いの？😱💥

![currency_chaos](./picture/invariants_cs_study_011_currency_chaos.png)



たとえばこんなの👇が起きるのが嫌なの：

![Currency Mismatch](./picture/invariants_cs_study_011_currency.png)

* 通貨が混ざって足される（`JPY + USD` とか）💣
* 小数桁が合ってない（JPYなのに `100.5` 円が通る）🌀
* どこかで `-1` 円が入り込む😵‍💫
* 画面入力の `"1,000"` が国/文化で解釈ズレる🧨

DDDでも `Money` は代表的な Value Object って言われるくらい「型にすると嬉しい」やつだよ💎 ([Microsoft Learn][7])

---

## 4) 実装してみよう🏗️💖（Money + Result）

ここからは、**壊れない `Money`** を作るよ〜！✨
（第7章の `Result` が既にある前提なら、そこは読み替えてOKだよ🙂）

### 4-1) まずはミニResult🧾🙂

```csharp
public readonly record struct Result<T>(bool IsSuccess, T? Value, string? Error)
{
    public static Result<T> Success(T value) => new(true, value, null);
    public static Result<T> Failure(string error) => new(false, default, error);
}
```

### 4-2) Money本体（不変＋Factoryで生成集中）💰🔒

![banker_scale_rounding](./picture/invariants_cs_study_011_banker_scale_rounding.png)



![money_vault_safe](./picture/invariants_cs_study_011_money_vault_safe.png)



ポイントはこれ👇

* **コンストラクタは private**（外からnewさせない）🏭
* **TryCreate で不変条件チェック**🛡️
* **record を使って値の等価性**（同じ通貨・同じ金額なら同一扱い）💎 ([Microsoft Learn][2])

```csharp
using System.Text.RegularExpressions;

public sealed record Money
{
    public string Currency { get; }
    public decimal Amount { get; }

    private Money(string currency, decimal amount)
        => (Currency, Amount) = (currency, amount);

    // 例: "JPY" -> 0, "USD" -> 2
    public static Result<Money> TryCreate(string currency, decimal amount, int minorDigits)
    {
        // currency
        if (string.IsNullOrWhiteSpace(currency))
            return Result<Money>.Failure("通貨コードが空だよ🥺");

        currency = currency.Trim().ToUpperInvariant();

        // ISO 4217 っぽく「英字3文字」だけに制限
        if (!Regex.IsMatch(currency, "^[A-Z]{3}$"))
            return Result<Money>.Failure("通貨コードは英字3文字（例: JPY, USD）にしてね💱");

        // amount
        if (amount < 0m)
            return Result<Money>.Failure("金額がマイナスはダメだよ🙅‍♀️");

        if (minorDigits is < 0 or > 28)
            return Result<Money>.Failure("小数桁設定が変だよ😵‍💫");

        // 小数桁を通貨の桁に揃える（桁が多すぎたら拒否）
        var rounded = decimal.Round(amount, minorDigits, MidpointRounding.ToEven);
        if (rounded != amount)
            return Result<Money>.Failure($"小数点以下は {minorDigits} 桁までだよ🔢");

        return Result<Money>.Success(new Money(currency, amount));
    }

    public Result<Money> Add(Money other, int minorDigits)
    {
        if (Currency != other.Currency)
            return Result<Money>.Failure("通貨が違うものは足せないよ💥");

        return TryCreate(Currency, Amount + other.Amount, minorDigits);
    }

    public Result<Money> Subtract(Money other, int minorDigits)
    {
        if (Currency != other.Currency)
            return Result<Money>.Failure("通貨が違うものは引けないよ💥");

        var result = Amount - other.Amount;
        return TryCreate(Currency, result, minorDigits); // マイナスならここで落ちる
    }

    public Result<Money> Multiply(decimal rate, int minorDigits)
    {
        if (rate < 0m)
            return Result<Money>.Failure("倍率がマイナスはダメだよ🙅‍♀️");

        // 金融系は丸め方が大事：ToEven（銀行丸め）が.NETの標準寄り :contentReference[oaicite:8]{index=8}
        var raw = Amount * rate;
        var rounded = decimal.Round(raw, minorDigits, MidpointRounding.ToEven);
        return TryCreate(Currency, rounded, minorDigits);
    }

    public override string ToString() => $"{Currency} {Amount}";
}
```

> 丸めの話：`.Round` の既定は `ToEven` だよ（.NET docs） ([Microsoft Learn][6])

---

## 5) 使ってみよ〜🥰🎀（サブスク課金の例）

![shopping_cart_money](./picture/invariants_cs_study_011_shopping_cart_money.png)



```csharp
const int JpyDigits = 0;

var fee = Money.TryCreate("JPY", 980m, JpyDigits);
var discount = Money.TryCreate("JPY", 100m, JpyDigits);

if (fee.IsSuccess && discount.IsSuccess)
{
    var payable = fee.Value!.Subtract(discount.Value!, JpyDigits);
    Console.WriteLine(payable.IsSuccess ? payable.Value!.ToString() : payable.Error);
}
```

---

## 6) テストを書こう🧪✨（xUnit例）

![scientist_money_test](./picture/invariants_cs_study_011_scientist_money_test.png)



「Money の不変条件が“壊れない”」って、テストで守るのが超大事だよ🫶

```csharp
using Xunit;

public class MoneyTests
{
    [Fact]
    public void Create_Fails_When_Negative()
    {
        var r = Money.TryCreate("JPY", -1m, 0);
        Assert.False(r.IsSuccess);
    }

    [Fact]
    public void Create_Fails_When_TooManyDecimals_For_JPY()
    {
        var r = Money.TryCreate("JPY", 100.5m, 0);
        Assert.False(r.IsSuccess);
    }

    [Fact]
    public void Add_Fails_When_Currency_Differs()
    {
        var a = Money.TryCreate("JPY", 100m, 0).Value!;
        var b = Money.TryCreate("USD", 1m, 2).Value!;
        var r = a.Add(b, 0);
        Assert.False(r.IsSuccess);
    }

    [Fact]
    public void Multiply_Rounds_ToEven()
    {
        // 例: ToEven を確認するテストは値を丁寧に選ぶのがコツ🙂
        var m = Money.TryCreate("USD", 2.345m, 3).Value!;
        var r = m.Multiply(1m, 2); // 2桁へ丸め
        Assert.True(r.IsSuccess);
        Assert.Equal(2.34m, r.Value!.Amount); // ToEvenの例として（docs参照） :contentReference[oaicite:10]{index=10}
    }
}
```

---

## 7) “落とし穴”チェックリスト🤖🔍（AIに洗い出しさせる）

AIにこう聞くと便利だよ〜✨（コピペOK）

* 「Money 値オブジェクトでありがちな落とし穴を10個、理由付きで」🤖
* 「通貨が違う加算をコンパイル時/実行時に防ぐ設計案を3つ」🤖⚖️
* 「JPY(0桁) / USD(2桁) / BHD(3桁) を想定したテストケースを大量生成して」🤖🧪

※AIが提案する「通貨の小数桁」を文化情報から取る案が出てきたら注意⚠️
`NumberFormatInfo.CurrencyDecimalDigits` は “カルチャの通貨表示” 寄りで、通貨コードそのものの厳密表とは別軸になりやすいよ〜🌀 ([Microsoft Learn][8])

---

## 8) ちょい発展🎀（通貨コードはどう取る？）

![currency_globe](./picture/invariants_cs_study_011_currency_globe.png)



「国/地域 → ISO通貨コード」を取りたい時は `RegionInfo.ISOCurrencySymbol` が使えるよ💱✨ ([Microsoft Learn][9])

```csharp
using System.Globalization;

var jp = new RegionInfo("JP");
Console.WriteLine(jp.ISOCurrencySymbol); // "JPY"
```

ただしこれは **“地域” から引く**ので、アプリの仕様によっては「ユーザー選択の通貨」を素直に受け取る方が安全なことも多いよ🙂

---

## 9) まとめ🏁🎉

* `Money` を VO にすると、**意図が伝わる**し、**事故が減る**💎✨ ([Microsoft Learn][7])
* `decimal`＋`record`＋`Factory` で「壊れないお金」を作れる🛡️
* **通貨一致・小数桁・丸め**は、`Money` の責務に入れると強い💰📌
* 丸めは .NET の標準（ToEven）を理解して使い分けできると安心🏦✨ ([Microsoft Learn][10])

---

## 次章予告📧💎

次は `Email` みたいな **文字列VO** にいくよ〜！
「正規表現はほどほど（KISS）」「正規化（trim/lower）」あたりが楽しいところ🥰🎀

[1]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14?utm_source=chatgpt.com "What's new in C# 14"
[2]: https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records?utm_source=chatgpt.com "Record types - C#"
[3]: https://www.iso.org/iso-4217-currency-codes.html?utm_source=chatgpt.com "ISO 4217 — Currency codes"
[4]: https://learn.microsoft.com/en-us/dotnet/fundamentals/runtime-libraries/system-decimal?utm_source=chatgpt.com "System.Decimal struct - .NET"
[5]: https://en.wikipedia.org/wiki/ISO_4217?utm_source=chatgpt.com "ISO 4217"
[6]: https://learn.microsoft.com/en-us/dotnet/api/system.math.round?view=net-10.0&utm_source=chatgpt.com "Math.Round Method (System)"
[7]: https://learn.microsoft.com/en-us/archive/msdn-magazine/2009/february/best-practice-an-introduction-to-domain-driven-design?utm_source=chatgpt.com "Best Practice - An Introduction To Domain-Driven Design"
[8]: https://learn.microsoft.com/en-us/dotnet/api/system.globalization.numberformatinfo.currencydecimaldigits?view=net-10.0&utm_source=chatgpt.com "NumberFormatInfo.CurrencyDecimalDigits Property"
[9]: https://learn.microsoft.com/ja-jp/dotnet/api/system.globalization.regioninfo.isocurrencysymbol?view=net-10.0&utm_source=chatgpt.com "RegionInfo.ISOCurrencySymbol Property"
[10]: https://learn.microsoft.com/en-us/dotnet/api/system.decimal.round?view=net-10.0&utm_source=chatgpt.com "Decimal.Round Method (System)"
