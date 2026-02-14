# 第15章：合成のご褒美🍬：テストがラクになる✅⚡

ここまで「差し替えできる部品🧩」を作ってきたよね？
この章は、そのご褒美タイム🍰✨ 「え、テストってこんなに気持ちよく書けるの！？」を体験する回だよ〜😊💕

---

## 0. この章でできるようになること🎯✨

* 外部I/O（日時⌚・メール📧・Web🌐・DB🗄️）を **Fake/Stub** に置き換えてテストする✅
* 「どこをモックして、どこはしないか」判断できるようになる🧠
* テストが **速い⚡・安定✅・読みやすい📖** になる感覚をつかむ

---

## 1. なんで「合成」だとテストがラクになるの？🧩➡️✅

![Testing Fakes](./picture/isa_hasa_cs_study_015_testing_fakes.png)

テストがしんどい原因、だいたいコレ👇

* `DateTime.Now` みたいな **時間** に依存⌚（実行タイミングで結果がブレる）
* メール送信📧 / HTTP🌐 / ファイル📁 / DB🗄️ みたいな **外部I/O** を直接呼ぶ（遅い・落ちる・環境依存）
* `new` がコードの奥深くに埋まってて、差し替えできない😵‍💫

合成（Composition）で「部品を外から渡す🧩🎁」形にすると…

* テストでは **Fake部品** を渡すだけでOK🧸✨
* 本番では **本物部品** を渡して動かす🚀

この「差し替えの入り口」があるだけで、テストが別ゲーになるよ😊✅

---

## 2. Fake / Stub / Mock ざっくり使い分け🧸🎭🧪

![Test Double Trio](./picture/isa_hasa_cs_study_015_test_double_trio.png)



ふわっとでOK！使ううちに体に染みるやつ🙂✨

* **Fake**🧸：それっぽく動く「簡易の実装」
  例：送信内容をリストに溜めるメール送信Fake📧
* **Stub**🪵：決まった値を返すだけ
  例：常に「成功」を返す決済Stub💳
* **Mock**🎭：呼び出し回数や引数を検証したい時に使う
  例：「Sendが1回だけ呼ばれた？」を確認✅

※テストフレームワークは MSTest / NUnit / xUnit.net などが一般的だよ（最近は TUnit もよく名前を見る）([Microsoft Learn][1])

---

## 3. 今日のお題（ミニ題材）🍬📦

**注文確定（Confirm）** すると👇

* 合計金額を計算🧮
* 期間限定割引（“今日だけ”）があれば適用🎁
* 確定メールを送る📧

「時間⌚」と「メール📧」が外部要素なので、ここを差し替えてテストするよ✅✨

---

## 4. まずは “テストしにくい” 例😱（new と Now が直書き）

![Hard Code Concrete](./picture/isa_hasa_cs_study_015_hard_code_concrete.png)



```csharp
public class OrderService
{
    public void Confirm(Order order)
    {
        var now = DateTimeOffset.Now; // ← テストで制御しづらい😵
        var discountRate = (now.Day == 15) ? 0.10m : 0m; // 例：毎月15日だけ10%OFF

        var total = order.Subtotal * (1 - discountRate);

        var mailer = new SmtpMailer(); // ← ここでnewしちゃうと差し替えできない😭
        mailer.Send(order.CustomerEmail, $"Total: {total}");
    }
}
```

これ、テストするときに詰むポイントが2つあるよね😇

* 日付が変わるとテスト結果が変わる⌚💥
* テスト実行で本当にメール飛ぶ📧💥（怖すぎ）

---

## 5. 合成で “差し替え可能” にする🧩🎁（テストが勝つ形）

![Testable Slots](./picture/isa_hasa_cs_study_015_testable_slots.png)



### 5-1. 依存を「契約（interface）」にする🔌

```csharp
public interface IMailer
{
    void Send(string to, string body);
}
```

時間は `System.TimeProvider` を使うのが今どきでラクだよ⌚✨
`TimeProvider` は「テスト可能で予測可能にするための時間の抽象化」として紹介されてるよ([Microsoft Learn][2])
さらにテスト用の `FakeTimeProvider` も用意されてる([Microsoft Learn][3])

### 5-2. OrderService を合成向きにする🧩

```csharp
public class OrderService
{
    private readonly IMailer _mailer;
    private readonly TimeProvider _time;

    public OrderService(IMailer mailer, TimeProvider time)
    {
        _mailer = mailer;
        _time = time;
    }

    public decimal Confirm(Order order)
    {
        var now = _time.GetLocalNow(); // ← テストで時間を固定できる😊
        var discountRate = (now.Day == 15) ? 0.10m : 0m;

        var total = order.Subtotal * (1 - discountRate);

        _mailer.Send(order.CustomerEmail, $"Total: {total}");
        return total;
    }
}

public record Order(decimal Subtotal, string CustomerEmail);
```

ポイントはこれ👇✨

* **OrderService の中で new しない**
* **時間も外から渡す**
  これだけでテストが超ラクになるよ✅

---

## 6. Fake を作って “爆速テスト” する⚡🧸

### 6-1. メール送信 Fake📧🧸（送った内容を保存するだけ）

![Fake Mailer Bag](./picture/isa_hasa_cs_study_015_fake_mailer_bag.png)



```csharp
public class FakeMailer : IMailer
{
    public List<(string To, string Body)> Sent { get; } = new();

    public void Send(string to, string body) => Sent.Add((to, body));
}
```

### 6-2. 時間を固定する FakeTimeProvider⌚🧊

NuGet でこれを追加するイメージ👇（テストプロジェクト側）

* `Microsoft.Extensions.TimeProvider.Testing`（FakeTimeProvider が入ってる）([NuGet][4])

---

## 7. テストを書こう🧪✅（例：xUnit）

### 7-1. 15日なら10%OFFになる？🎁

```csharp
using Microsoft.Extensions.Time.Testing;
using Xunit;

public class OrderServiceTests
{
    [Fact]
    public void Confirm_On15th_Gives10PercentOff_AndSendsMail()
    {
        // Arrange
        var fakeMailer = new FakeMailer();

        var fakeTime = new FakeTimeProvider();
        fakeTime.SetLocalTimeZone(TimeZoneInfo.Local);
        fakeTime.SetLocalNow(new DateTimeOffset(2026, 1, 15, 10, 0, 0, TimeZoneInfo.Local.BaseUtcOffset));

        var sut = new OrderService(fakeMailer, fakeTime);
        var order = new Order(1000m, "a@example.com");

        // Act
        var total = sut.Confirm(order);

        // Assert
        Assert.Equal(900m, total);
        Assert.Single(fakeMailer.Sent);
        Assert.Contains("Total: 900", fakeMailer.Sent[0].Body);
    }
}
```

> ※FakeTimeProvider は “時間依存コードのテストを容易にする” ために使えるよ、って Microsoft のドキュメントにも書かれてるよ([Microsoft Learn][3])

### 7-2. 15日じゃないなら割引なし？🙂

```csharp
[Fact]
public void Confirm_Not15th_NoDiscount()
{
    var fakeMailer = new FakeMailer();

    var fakeTime = new FakeTimeProvider();
    fakeTime.SetLocalNow(new DateTimeOffset(2026, 1, 14, 10, 0, 0, TimeSpan.FromHours(9)));

    var sut = new OrderService(fakeMailer, fakeTime);
    var order = new Order(1000m, "a@example.com");

    var total = sut.Confirm(order);

    Assert.Equal(1000m, total);
}
```

✅ ここまでの感想：
テストが **ネット不要🌐❌**、**メール送信なし📧❌**、**時間ブレなし⌚❌** で、秒速で回る⚡✨
これが「合成のご褒美」だよ〜🍬😊

---

## 8. 「何をモックし、何をモックしない？」の目安🧭✨

![Mocking Strategy Scale](./picture/isa_hasa_cs_study_015_mocking_strategy_scale.png)



モックしがちだけど、しない方がラクなこと多いよ🙂

### モック（差し替え）しやすいもの✅

* 時間⌚（TimeProvider）
* ランダム🎲
* HTTP🌐 / DB🗄️ / ファイル📁 / メール📧
* OS依存（環境変数、時計、スレッドタイミング）🪟

### モックしない（本物でOK）になりやすいもの🧡

* ただの計算🧮
* 文字列整形📄
* 値オブジェクト（Money とか）💰

「外の世界」と「中のロジック」を分けるほど、テストが強くなる💪✨

---

## 9. Mockフレームワークはいつ使う？🎭

手書きFakeが最強な場面、多いよ🧸✨
でも「呼ばれ方の検証」が増えるなら Mock が便利！

有名どころだと Moq（GitHub でも定番）([GitHub][5])
ただし最初は **手書きFake** で全然OKだよ😊

---

## 10. AI活用🤖🫶（テストが増える瞬間にめっちゃ効く）

### 使える頼み方テンプレ💬✨

* 「この仕様のテストケースを10個、重複なしで出して🧪」
* 「境界値と例外系を中心にテスト観点を出して⚠️」
* 「この依存はFakeで十分？Mockが必要？理由つきで教えて🧠」
* 「命名を読みやすくして（AAAに沿って）✍️」

👉 ただし “採用するのは自分” ね😊（AIの案は混ざり物もあるから✅）

---

## 11. ミニ課題（15分）📮✨

1. 割引ルールを「毎月15日」じゃなくて「週末だけ」に変えて、テストも更新してみよ📅🎁
2. メール本文に「注文ID」を入れて、FakeMailer で検証してみよ🧾📧
3. 例外系：「メールアドレスが空なら送らない」ルールを足してテストしてみよ🧪🛡️

---

## 12. 今日のまとめ🌈✅

* 合成で「差し替え口🧩」を作ると、テストは速く・安定して・気持ちよくなる⚡
* `TimeProvider` + `FakeTimeProvider` で “時間ガチャ” を消せる⌚🧊([Microsoft Learn][2])
* テストフレームワーク周りも最新では整理が進んでて、`dotnet test` でも VSTest / Microsoft.Testing.Platform の話が出てくる（混在は注意）([Microsoft Learn][6])

---

次章（第16章）は「継承→合成へ安全に移行🛠️🙂」だね！
この第15章で “テストの気持ちよさ” を掴んでおくと、移行作業がめっちゃ怖くなくなるよ〜🍀😊

[1]: https://learn.microsoft.com/ja-jp/dotnet/core/testing/?utm_source=chatgpt.com "NET でのテスト"
[2]: https://learn.microsoft.com/en-us/dotnet/standard/datetime/timeprovider-overview?utm_source=chatgpt.com "What is the TimeProvider class - .NET"
[3]: https://learn.microsoft.com/ja-jp/dotnet/api/system.timeprovider?view=net-8.0&utm_source=chatgpt.com "TimeProvider クラス (System)"
[4]: https://www.nuget.org/packages/Microsoft.Extensions.TimeProvider.Testing/8.10.0?utm_source=chatgpt.com "Microsoft.Extensions.TimeProvider.Testing 8.10.0"
[5]: https://github.com/devlooped/moq?utm_source=chatgpt.com "devlooped/moq: The most popular and friendly mocking ..."
[6]: https://learn.microsoft.com/ja-jp/dotnet/core/testing/unit-testing-with-dotnet-test?utm_source=chatgpt.com "'dotnet test' を使用したテスト - .NET"
