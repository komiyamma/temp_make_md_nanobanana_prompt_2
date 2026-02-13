# 第14章：契約（バージョン）をちょい意識する 🏷️🔁

## 🎯 今日のゴール

* Outbox の **Payload（中身）** は未来でほぼ確実に変わる前提で、**壊さずに進化させるコツ**をつかむ🧠✨
* 「v1 → v2」に変わっても、**古い受け手が即死しない**＆**新しい受け手も困らない**状態を目指す🛡️

---

## 1) そもそも「契約」ってなに？📜🤝

![Contract Break](./picture/outbox_cs_study_014_contract_break.png)

Outbox のメッセージは、ざっくり言うと **送り手（Producer）と受け手（Consumer）の約束ごと**だよ📦➡️📩

* 送り手：「この形（JSON）で送るね！」📤
* 受け手：「じゃあこの形だと思って読むね！」📥

この“形”が変わると、受け手は **読めなくなったり**、**間違って解釈したり**する😵‍💫
だから「変えるのはOK、でも壊さないでね」の工夫が必要になるよ🔧✨

---

## 2) 互換性の考え方（超重要）🧩🧡

![Backward vs Forward Compatibility](./picture/outbox_cs_study_014_backward_vs_forward.png)

メッセージの形が変わるとき、気にするのはこの2つ👇

## ✅ 後方互換（Backward compatibility）⏪

**新しい受け手**が、**古いメッセージ**を読める
（例：v2 の受け手が v1 の Payload も読める）👍

## ✅ 前方互換（Forward compatibility）⏩

**古い受け手**が、**新しいメッセージ**を“ある程度”読める
（例：v1 の受け手が v2 の余計なフィールドを無視して動ける）👍

メッセージの設計では「バージョンを上げたなら、受け手が追随できる仕組みを用意してね」が定石だよ📌
（Producer が version を付ける／Consumer が変更を追跡する、など）([Microsoft Learn][1])

---

## 3) 初心者向け「壊さず進化」ミニルール 🧡🧰

ここから先は “迷ったらこれ守っておけばだいたい平和” ルールだよ🕊️✨

## ルールA：フィールドは「追加」が最強 ➕💪

![Add Field Safe](./picture/outbox_cs_study_014_add_field_safe.png)

* v1 に `CustomerId` を **追加**して v2 にする、みたいな進化はやりやすい🎉
* 受け手が新フィールドを知らなくても、無視できれば助かる（前方互換）😌

## ルールB：フィールド名の「変更」「削除」は爆発しやすい 💥🙅‍♀️

* `totalPrice` を `amount` にリネーム → 受け手は `totalPrice` を探して落ちる😱
* 削除も同じ（受け手が期待してたものが消える）😱([Microsoft Learn][1])

## ルールC：「意味」を変えない（これ地味に大事）🧠⚠️

* 同じ `status` でも、意味が変わるとバグが一番こわい😇
* “名前は同じだけど解釈が違う” は地雷💣

## ルールD：型を変えるのも危険（string→number など）🔁💥

* JSON は柔らかそうで、実際は受け手のコードが固いことが多い😵‍💫

---

## 4) バージョンの付け方：おすすめ3パターン 🏷️📦

![Versioning Evolution](./picture/outbox_cs_study_014_versioning.png)

「契約（Payloadの形）」が変わるとき、バージョンをどう持つかはだいたいこの3つ👇

## パターン①：Envelope（封筒）に `Version` を持つ 📩🏷️（おすすめ）

Outbox の “外側” に

* `Type`（何のイベント？）
* `Version`（何版？）
  を持たせるやつ✨

## パターン②：Type名に `v1` / `v2` を埋める 🏷️🔤（分かりやすい）

例：

* `OrderCreated.v1`
* `OrderCreated.v2`

## パターン③：スキーマ管理（Schema Registry等）📚🔒（上級）

Avro / Protobuf / JSON Schema などのスキーマと互換性ルールで運用する方式。大規模で強い💪
（ただし初心者には導入コスト高め）([Confluent Documentation][2])

この教材の段階では、**①＋②** がいちばん扱いやすいよ😊✨

---

## 5) まずは形を決めよう：Envelope の最小構成 🧾✨

Outbox の1行を、こんな“封筒＋中身”で考えるよ📦

* `Id`：Outbox の一意ID（冪等性キーにも使いやすい）🪪
* `Type`：イベント種別（例：OrderCreated）🏷️
* `Version`：契約の版（1,2,3…）🔢
* `OccurredAt`：発生時刻🕒
* `Payload`：JSON本文🧾

> 「複数バージョンがしばらく共存する」前提で設計すると移行が安全になるよ🧡([Microsoft Learn][3])

---

## 6) C# 実装例：v1 / v2 を作ってみる ✍️😺

## 6-1) 契約クラス（v1 / v2）📦

```csharp
using System.Text.Json;

public sealed record OutboxEnvelope(
    Guid Id,
    string Type,
    int Version,
    DateTimeOffset OccurredAt,
    JsonElement Payload
);

public sealed record OrderCreatedV1(
    Guid OrderId,
    decimal Total,
    string Currency
);

// v2で CustomerId を追加（追加は比較的安全）➕
public sealed record OrderCreatedV2(
    Guid OrderId,
    decimal Total,
    string Currency,
    string CustomerId // 追加フィールド
);
```

## 6-2) 送る側：Payload を JsonElement にして封筒へ 📤📩

```csharp
using System.Text.Json;
using System.Text.Json.Serialization;

public static class OutboxFactory
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        // unmapped(=知らない)フィールドの扱いは後述！
    };

    public static OutboxEnvelope CreateOrderCreatedV1(Guid outboxId, OrderCreatedV1 payload)
    {
        var json = JsonSerializer.SerializeToElement(payload, JsonOptions);

        return new OutboxEnvelope(
            Id: outboxId,
            Type: "OrderCreated",
            Version: 1,
            OccurredAt: DateTimeOffset.UtcNow,
            Payload: json
        );
    }

    public static OutboxEnvelope CreateOrderCreatedV2(Guid outboxId, OrderCreatedV2 payload)
    {
        var json = JsonSerializer.SerializeToElement(payload, JsonOptions);

        return new OutboxEnvelope(
            Id: outboxId,
            Type: "OrderCreated",
            Version: 2,
            OccurredAt: DateTimeOffset.UtcNow,
            Payload: json
        );
    }
}
```

---

## 7) 受け手の基本：Type + Version で分岐する 🧭🔀

最初はこれで十分強いよ💪✨

```csharp
using System.Text.Json;

public static class Consumer
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
    };

    public static void Handle(OutboxEnvelope env)
    {
        if (env.Type != "OrderCreated")
            return; // 今回はOrderCreatedだけ扱う想定

        switch (env.Version)
        {
            case 1:
            {
                var v1 = env.Payload.Deserialize<OrderCreatedV1>(JsonOptions)
                         ?? throw new InvalidOperationException("Payload is null");
                HandleOrderCreated(Upcast(v1));
                break;
            }
            case 2:
            {
                var v2 = env.Payload.Deserialize<OrderCreatedV2>(JsonOptions)
                         ?? throw new InvalidOperationException("Payload is null");
                HandleOrderCreated(Upcast(v2));
                break;
            }
            default:
                // 未知のVersionをどうするかは運用ルール（ログ＋スキップ等）
                throw new NotSupportedException($"Unknown version: {env.Version}");
        }
    }

    // “最終形”に寄せる（Upcast）🧙‍♀️✨
    private static OrderCreatedLatest Upcast(OrderCreatedV1 v1)
        => new(v1.OrderId, v1.Total, v1.Currency, CustomerId: "UNKNOWN");

    private static OrderCreatedLatest Upcast(OrderCreatedV2 v2)
        => new(v2.OrderId, v2.Total, v2.Currency, v2.CustomerId);

    private static void HandleOrderCreated(OrderCreatedLatest latest)
    {
        // 以降のビジネスロジックは “最新形” だけ見ればOKになる🎉
        Console.WriteLine($"Order {latest.OrderId} total={latest.Total} {latest.Currency} customer={latest.CustomerId}");
    }

    private sealed record OrderCreatedLatest(Guid OrderId, decimal Total, string Currency, string CustomerId);
}
```

## ✅ Upcast（アップキャスト）が嬉しい理由 🎁

![Upcast Pattern](./picture/outbox_cs_study_014_upcast_pattern.png)

* 分岐は入口だけで済む → 中のロジックがスッキリ🍱✨
* v3 が増えても、`Upcast(v3)` を足していけばいい🧩

---

## 8) “知らないフィールド”が来たらどうする？🧾🌀

![Ignore Unknown](./picture/outbox_cs_study_014_ignore_unknown.png)

ここ、前方互換に直結するよ⚡

## ✔️ 基本方針：知らないフィールドは「無視」できると助かる😌

JSON でフィールド追加しても、受け手が “余計なフィールドを無視” できれば、古い受け手は生き残りやすい🛟

## 🔧 でも「厳格にしたい」場面もある（セキュリティ/入力検証）🛡️

`System.Text.Json` には、**マップできない JSON プロパティ（=未知フィールド）**の扱いを制御するオプションがあるよ🧰
`JsonSerializerOptions.UnmappedMemberHandling` で挙動を指定できる（例：スキップ、エラーなど）([Microsoft Learn][4])

> 「普段はゆるく（互換性重視）」「外部入力は厳しく（検証重視）」みたいに、入口で使い分けるのが現実的だよ😊✨

---

## 9) バージョン番号の付け方：超ミニでOK 🔢💡

Outbox の Payload は、まずは **整数（1,2,3）**で十分！
もし将来 “互換性の意味” まで整理したくなったら、SemVer（例：2.1.0）みたいな考え方もあるよ📌
SemVer は **MAJOR を上げる＝互換性を壊す変更**、みたいにルールで意味を持たせる方式だよ🧠([Semantic Versioning][5])

---

## 10) ミニ演習（めっちゃ大事）🧪🏁

## 🎮 お題：OrderCreated を v1 → v2 に進化させる

1. v1 で Outbox に書く（`OrderId, Total, Currency`）🛒
2. 受け手が v1 を処理できることを確認✅
3. v2 を追加（`CustomerId` を追加）➕
4. 受け手を v1/v2 両対応にする（switch＋Upcast）🔀
5. **古い v1 データがDBに残ってても、処理が継続できる**のを確認🎯

## 🔍 観察ポイント👀

* v2 受け手が v1 を読める？（後方互換）⏪
* v1 受け手が v2 を受けたとき、未知フィールドで落ちない？（前方互換）⏩
* ロジックは最新形に寄せられてる？（Upcast の効果）✨

---

## 11) AI（Copilot/Codex）に頼むときのコツ 🤖📝

AIにはここを頼むとラクだよ😊

* `switch(env.Version)` の雛形を作ってもらう🧱
* v1/v2 の record と Serialize/Deserialize を用意してもらう🧾
* Upcast の設計案を出してもらう🧙‍♀️

ただし最後に人間が見るポイントはここ👇

* **Version の増やし方が“壊す変更”と一致してるか**🏷️
* **削除/リネームをしてないか**💥
* **未知フィールドの扱い（ゆるい/厳しい）が意図通りか**🛡️

---

## ✅ まとめ：この章の“持ち帰り”🎁✨

* Payload は変わる！だから **Type + Version** を付けておくのが安心😌([Microsoft Learn][1])
* 進化はまず **フィールド追加**でやるのが安全度高め➕
* 受け手は **Version 分岐 → Upcast → 最新形で処理**がスッキリ🍱
* `System.Text.Json` は未知フィールドの扱いを制御できる（必要なら厳格にもできる）🧰([Microsoft Learn][4])
* 2026年2月時点では .NET は **.NET 10** が現行のサポート対象として案内されているよ📌([dotnet.microsoft.com][6])

[1]: https://learn.microsoft.com/en-us/azure/architecture/best-practices/message-encode "Message Encoding Considerations - Azure Architecture Center | Microsoft Learn"
[2]: https://docs.confluent.io/cloud/current/sr/fundamentals/schema-evolution.html?utm_source=chatgpt.com "Schema Evolution and Compatibility for Schema Registry ..."
[3]: https://learn.microsoft.com/en-us/samples/azure-samples/cosmos-db-design-patterns/schema-versioning/?utm_source=chatgpt.com "Azure Cosmos DB design pattern: Schema Versioning"
[4]: https://learn.microsoft.com/ja-jp/dotnet/api/system.text.json.jsonserializeroptions.unmappedmemberhandling?view=net-10.0 "JsonSerializerOptions.UnmappedMemberHandling プロパティ (System.Text.Json) | Microsoft Learn"
[5]: https://semver.org/?utm_source=chatgpt.com "Semantic Versioning 2.0.0 | Semantic Versioning"
[6]: https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core ".NET and .NET Core official support policy | .NET"
