# 第13章：期間（DateRange）を作る📅💎

前章の **Email VO** では「`new`禁止＋`Create(...)`で生成を集中」って流れだったよね🏭🔒（Result型もそれ！）
この章はそのノリのまま、**「開始日 <= 終了日」** を **型で固定**していくよ〜🥰🛡️✨

---

## 0. 2026年“最新版”前提メモ🆕🪟✨

* **C# 14 / .NET 10** を前提に進めるよ（新機能に依存はしないけど、最新版が気持ちいい😊）([Microsoft Learn][1])
* **Visual Studio 2026** は安定版が継続的に更新されてる想定でOK（例：2026-02-10の安定版ビルドが掲載）([Microsoft Learn][2])

---

## 1. DateRangeで起きがちな事故あるある😇💥

* 予約やサブスクで **開始日と終了日を逆に保存** → 料金計算がマイナス🌀
* “日付だけ”のはずが `DateTime` で扱われて、**タイムゾーンや時刻でズレる**⏰🌍
* 「チェック書き忘れ」で、どこかの画面から **壊れた期間が混入**🚪💣

だからこの章のゴールはこれ👇
✅ **壊れた期間（start > end）を“そもそも作れない”** ようにする💎🛡️

---

## 2. まずは「日付」か「日時」かを分ける🧠✨

今回は「◯月◯日〜◯月◯日」みたいな **“日付だけ”** の期間を想定して、`.NET` の **`DateOnly`** を使うよ〜📅
`DateOnly` は「時間を持たない日付」を表す型だよ（まさにこれが欲しいやつ！）([Microsoft Learn][3])

> もし「2026-02-13 10:00〜」みたいな **日時＋TZ** が必要なら、別VOで `DateTimeOffset` を使うのがおすすめ🙆‍♀️（この章では“日付だけ”に集中！）

---

## 3. この章の“仕様”を決めよう📜🎀

**DateRange（期間）VO** の仕様はシンプルにいくね🙂✨

* `Start` と `End` は **`DateOnly`**
* **不変条件：`Start <= End`**
* 同日（Start == End）は **OK**（1日だけの予約とかあるしね😉）

---

## 4. 実装：DateRange 値オブジェクトを作る💎📅

前章と同じ **Resultパターン** でいくよ〜🧾✨（そのまま流用できる👍）

```csharp
public enum DateRangeError
{
    StartAfterEnd
}

public sealed record DateRange
{
    public DateOnly Start { get; }
    public DateOnly End { get; }

    private DateRange(DateOnly start, DateOnly end)
    {
        Start = start;
        End :contentReference[oaicite:5]{index=5}de string ToString() => $"{Start:yyyy-MM-dd}..{End:yyyy-MM-dd}";

    public int DaysInclusive => End.DayNumber - Start.DayNumber + 1; // 両端込み

    public bool Contains(DateOnly date) => Start <= date && date <= End;

    public static Result<DateRange, DateRangeError> Create(DateOnly start, DateOnly end)
    {
        if (start > end)
            return Result<DateRange, DateRangeError>.Fail(DateRangeError.StartAfterEnd);

        return Result<DateRange, DateRangeError>.Ok(new DateRange(start, end));
    }
}
```

ポイントはこれだよ👇✨

* `new DateRange(...)` を外からできない 🔒
* `Create` でしか作れない 🏭
* だから **逆転した期間が中に入ってこれない** 🛡️💎

---

## 5. 境界（UI/API）で “文字列→DateOnly→DateRange” に変換する🚪➡️💎

ここが **「境界で守る」** の見せ場だよ〜🎀✨
入力はだいたい文字列で来るから、境界で `DateOnly.TryParseExact` を使って整えてから VOへ！🧼

`DateOnly` のパースは公式にも載ってるよ📝([Microsoft Learn][4])

```csharp
using System.Globalization;

public sealed record SubscribeRequest(string? StartDate, string? EndDate);

public static class Subscription
{
    // 例：yyyy-MM-dd固定の入力だと思って進めるよ🙂
    private const string DateFormat = "yyyy-MM-dd";

    public static string Subscribe(SubscribeRequest req)
    {
        if (string.IsNullOrWhiteSpace(req.StartDate) || string.IsNullOrWhiteSpace(req.EndDate))
            return "開始日と終了日を入力してね🙂📅";

        if (!DateOnly.TryParseExact(req.StartDate.Trim(), DateFormat, CultureInfo.InvariantCulture,
                DateTimeStyles.None, out var start))
            return "開始日の形式が違うかも🥺（例: 2026-02-13）";

        if (!DateOnly.TryParseExact(req.EndDate.Trim(), DateFormat, CultureInfo.InvariantCulture,
                DateTimeStyles.None, out var end))
            return "終了日の形式が違うかも🥺（例: 2026-02-20）";

        var rangeResult = DateRange.Create(start, end);

        if (!rangeResult.IsSuccess)
        {
            return rangeResult.Error switch
            {
                DateRangeError.StartAfterEnd => "期間が逆だよ🥺（開始日 <= 終了日）",
                _ => "期間が変かも🥺"
            };
        }

        var range = rangeResult.Value!; // ここから先は安全✨
        return $"登録OK！利用期間 = {range}（{range.DaysInclusive}日）🎉";
    }
}
```

この “境界→VO” の流れができると…
💖 ドメイン内部は **「DateRangeは必ず正しい」前提** で書ける！
→ ifチェックが減って、設計がスッキリするよ〜🥰✨

---

## 6. テストで“仕様”を固めよう🧪✨（超だいじ！）

最低ラインはこれだけでOK🙆‍♀️

* 同日OK（Start==End）✅
* 逆転はFail（Start > End）🚫
* DaysInclusive が両端込みになる✅
* Contains が端っこも含む✅

```csharp
using Xunit;

public class DateRangeTests
{
    [Fact]
    public void Create_AllowsSameDay()
    {
        var d = new DateOnly(2026, 2, 13);
        var r = DateRange.Create(d, d);
        Assert.True(r.IsSuccess);
        Assert.Equal(1, r.Value!.DaysInclusive);
    }

    [Fact]
    public void Create_FailsWhenStartAfterEnd()
    {
        var start = new DateOnly(2026, 2, 20);
        var end = new DateOnly(2026, 2, 13);
        var r = DateRange.Create(start, end);
        Assert.False(r.IsSuccess);
        Assert.Equal(DateRangeError.StartAfterEnd, r.Error);
    }

    [Fact]
    public void Contains_IsInclusive()
    {
        var r = DateRange.Create(new DateOnly(2026, 2, 13), new DateOnly(2026, 2, 20)).Value!;
        Assert.True(r.Contains(new DateOnly(2026, 2, 13))); // start
        Assert.True(r.Contains(new DateOnly(2026, 2, 20))); // end
        Assert.False(r.Contains(new DateOnly(2026, 2, 12)));
        Assert.False(r.Contains(new DateOnly(2026, 2, 21)));
    }
}
```

---

## 7. Visual Studioでの進め方🧑‍💻🪟✨（かんたん）

1. **Solution作成**：`InvariantsPractice`
2. **Class Library**：`InvariantsPractice.Domain`（DateRange置き場）
3. **xUnit Test Project**：`InvariantsPractice.Domain.Tests`
4. Testsプロジェクトから Domain に参照追加
5. テストを実行（Test Explorer）→ 緑✅にする

---

## 8. AI（Copilot / Codex）使い方🤖💘（この章も相性いい！）

### ✅ 境界値テストを増やす

* 「`DateRange.Create` の仕様（Start<=End、同日OK、DaysInclusive両端込み）で、追加テストケースを20個。入力と期待結果で。」

### ✅ 仕様の穴をレビューさせる

* 「このDateRange設計をレビューして。事故りやすい点（タイムゾーン、Inclusive/Exclusive、DayNumberの注意点）を指摘して。」

### ✅ “このアプリの都合”の追加不変条件を提案させる

* 「サブスク期間としてDateRangeを使う。最大365日まで、開始日は今日以降、などの追加不変条件案を3つ。」

※AIは便利だけど、最後の採用判断はあなたがやるのが大事だよ😉🫶

---

## 9. 演習（ここまでやれば勝ち🏁🎉）

* 演習①：`DaysExclusive`（両端含まない版）を追加して、テストも書く🧪
* 演習②：`Overlaps(DateRange other)` を追加して、重なり判定をテスト🧩
* 演習③：境界の入力を **`yyyy/MM/dd`** も許可する（複数フォーマット）🧼
* 演習④：サブスクっぽく「最大365日」を不変条件に追加してFailさせる🛡️📏

---

次はこの流れで気持ちよく行けるよ👇😊🎀
**第14章：record / immutable を味方にする❄️🧊**（“途中で壊れないデータ構造”を増やす！）

[1]: https://learn.microsoft.com/ja-jp/dotnet/csharp/whats-new/csharp-14?utm_source=chatgpt.com "C# 14 の新機能"
[2]: https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-history?utm_source=chatgpt.com "Visual Studio Release History"
[3]: https://learn.microsoft.com/en-us/dotnet/standard/datetime/how-to-use-dateonly-timeonly?utm_source=chatgpt.com "How to use DateOnly and TimeOnly - .NET"
[4]: https://learn.microsoft.com/ja-jp/dotnet/standard/datetime/how-to-use-dateonly-timeonly?utm_source=chatgpt.com "DateOnly と TimeOnly の使用方法 - .NET"
