# 第13章：Payload（中身）設計：JSON化とサイズ感 🧾📏

## 今日のゴール 🎯✨

* Outbox の **Payload（中身）に何を入れるべきか** が判断できるようになる🧠💡
* JSONにして **DBに保存 → 読み出して確認** までできるようになる👀✅
* 「大きすぎて運用がつらい」「個人情報を詰めすぎて怖い」みたいな事故を避ける😱🧯

---

## 1) Payloadってなに？超ざっくり言うと📦✨

![Payload Contract](./picture/outbox_cs_study_013_payload_contract.png)

Outbox の Payload は、「あとで配送係（Relay）が外に送る“荷物の中身”」だよ〜📮🚚
つまり、**別プロセス・別サービスに渡っても意味が伝わるデータ** が入っているのが理想👍

ここで大事なのはこれ👇

* **Payloadは“契約（Contract）”の一部** 📝🔗
* 送る側の気分でフィールドを増やすと、受け手が壊れることがある💥（次章で“壊さず進化”をやるよ🏷️🔁）

---

## 2) まず結論：Payload設計の「最小ルール」🍙✅

迷ったら、まずこれだけ守ればOKだよ〜🙆‍♀️✨

## ルールA：必要最小限が正義👼📌

* 「受け手がやるべき処理に必要な情報」だけ入れる
* “便利そう”で入れた情報が、あとで重荷になりがち😇🪨

## ルールB：個人情報（PII）は詰めすぎない🙈🔒

![PII Warning](./picture/outbox_cs_study_013_pii_warning.png)

* PayloadはログやDBに残りやすい（＝漏れたら痛い）😱
* 例えばメールアドレス・住所・氏名などは **原則入れない** 方向で考えるのが安全💖

## ルールC：「ID参照」を基本にする🔗🧠

* だいたいのケースは **参照ID（OrderIdなど）だけ送る** のがラク✨
* 受け手が必要なら、受け手側でAPI/DBから取りに行く（または受け手のキャッシュ）🏃‍♀️💨

---

## 3) Payloadの代表的な3パターン🧩✨

![Payload Patterns](./picture/outbox_cs_study_013_payload_patterns.png)

| パターン          | どんな形？                          | いいところ😍        | 注意点😅                      |
| ------------- | ------------------------------ | -------------- | -------------------------- |
| **ID参照型**     | `{ orderId }`                  | 小さい・安全・変更に強い💪 | 受け手が追加取得する手間🌀             |
| **スナップショット型** | `{ orderId, total, items... }` | 受け手がすぐ処理できる⚡   | 大きくなりやすい📦💦 / 個人情報混入しがち🙈 |
| **ハイブリッド型**   | `{ orderId, total }` + 必要最小限   | ほどよい🎯         | “最小限”の判断が必要🧠              |

初心者コースでは **ID参照 or ハイブリッド** を推しでいくよ〜🍀✨

---

## 4) 「入れる / 入れない」の具体例🧾👀

## ✅ 入れたい（例）

* `orderId`（参照のキー）🔑
* `occurredAt`（いつ起きた？※テーブルにあれば省略でもOK）⏰
* `outboxId`（受け手の重複排除に使える✨ 次の章の伏線🎣）
* `version`（次章の伏線🏷️）

## ❌ できれば入れたくない（例）

* 氏名・住所・電話番号・メールアドレス…（PII）🙈📛
* “画面表示用”の文言（受け手の都合で変わる）🌀
* 巨大な配列（items 1000件とか）📦📦📦💦

---

## 5) JSONの形（おすすめの“封筒”スタイル）✉️🧡

![Envelope Structure](./picture/outbox_cs_study_013_envelope.png)

Outboxテーブルに `Type` があるとしても、送信先（キュー/HTTP）に出すときは **封筒（Envelope）** があると強いよ💪✨
（受け手がメッセージ単体で理解できるから）

例：こんなJSON（読みやすさ優先）👇

```json
{
  "messageId": "8b8f3d2a-7a56-4f9e-8d9f-3bce4b5b8a5f",
  "type": "OrderCreated",
  "version": 1,
  "occurredAt": "2026-02-03T03:12:34.567+09:00",
  "data": {
    "orderId": "c8cbe0c4-8a60-4a4f-9f36-1b8b8f0f7c2a",
    "customerId": "CUST-001234",
    "total": 2980,
    "currency": "JPY"
  }
}
```

> `version` は次章で本格的に扱うけど、今のうちに入れておくと後がラク〜🏷️✨
> C# 14 は .NET 10 でサポートされてるよ。([Microsoft Learn][1])

---

## 6) サイズ感の話：Payloadは小さいほど運用がラク📏🧹

![Size Impact](./picture/outbox_cs_study_013_payload_size_impact.png)

Payload が大きいと、地味にこうなるよ〜😵‍💫

* DBが太る🐘💥（バックアップも遅くなる）
* Relayの読み出し・送信が遅い🐢
* キューやHTTPで制限に引っかかる可能性が上がる🚧
* ログに出たときの事故率アップ🙈🔥

なので指針としては👇

* **まずは「小さく」**（ID参照 or 最小ハイブリッド）🥹✨
* どうしても大きくなるなら、**別ストレージに置いて参照IDだけ送る**（発展）🔗🗄️

---

## 7) C#でPayloadをJSON化する（System.Text.Json）🧑‍💻✨

![Serialization Process](./picture/outbox_cs_study_013_serialization_process.png)

JSONは .NET 標準の `System.Text.Json` を使うのが今の基本だよ〜🧡
`System.Text.Json` は .NET のランタイムに含まれる（.NET Core 3.1 以降）って明記されてるよ。([Microsoft Learn][2])

## 7.1 送るデータ（data部分）を record で作る📦

```csharp
public sealed record OrderCreatedData(
    Guid OrderId,
    string CustomerId,
    int Total,
    string Currency
);
```

## 7.2 封筒（Envelope）も record にする✉️

```csharp
public sealed record OutboxEnvelope<T>(
    Guid MessageId,
    string Type,
    int Version,
    DateTimeOffset OccurredAt,
    T Data
);
```

## 7.3 JSONにシリアライズしてサイズを軽くチェック📏✅

```csharp
using System.Text;
using System.Text.Json;

public static class OutboxJson
{
    // 迷ったらこのへんでOK（まずは分かりやすさ重視）
    private static readonly JsonSerializerOptions Options = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false
    };

    public static string ToJson<T>(OutboxEnvelope<T> envelope, int maxBytes)
    {
        var json = JsonSerializer.Serialize(envelope, Options);

        var bytes = Encoding.UTF8.GetByteCount(json);
        if (bytes > maxBytes)
        {
            throw new InvalidOperationException(
                $"Payload too large: {bytes} bytes (limit: {maxBytes} bytes)");
        }

        return json;
    }
}
```

> サイズ上限の値（`maxBytes`）はチームや送信先で決めるところだよ〜📏
> （ここでは“チェックのやり方”を覚えるのが目的✨）

---

## 8) ミニ演習：PayloadをDBに保存して読めることを確認👀✅

## 8.1 Outboxエンティティ（Payloadは文字列でOK）🧱

```csharp
public sealed class OutboxMessage
{
    public Guid Id { get; set; }
    public string Type { get; set; } = default!;
    public int Version { get; set; }
    public DateTimeOffset OccurredAt { get; set; }

    public string Payload { get; set; } = default!;
}
```

## 8.2 Outboxに積む処理（注文作成のついでに）🛒📦

```csharp
public async Task CreateOrderAndEnqueueOutboxAsync(AppDbContext db)
{
    // 例：注文を作った想定（詳細は前章までの実装を利用）
    var orderId = Guid.NewGuid();

    var data = new OrderCreatedData(
        OrderId: orderId,
        CustomerId: "CUST-001234",
        Total: 2980,
        Currency: "JPY"
    );

    var envelope = new OutboxEnvelope<OrderCreatedData>(
        MessageId: Guid.NewGuid(),          // 後で“重複排除キー”にも使える✨
        Type: "OrderCreated",
        Version: 1,
        OccurredAt: DateTimeOffset.Now,
        Data: data
    );

    var payloadJson = OutboxJson.ToJson(envelope, maxBytes: 16 * 1024); // 例：16KB上限

    db.OutboxMessages.Add(new OutboxMessage
    {
        Id = envelope.MessageId,
        Type = envelope.Type,
        Version = envelope.Version,
        OccurredAt = envelope.OccurredAt,
        Payload = payloadJson
    });

    await db.SaveChangesAsync();
}
```

## 8.3 保存されたJSONを読んで「目で確認」👀✨

```csharp
using System.Text.Json;

public async Task DumpLatestOutboxAsync(AppDbContext db)
{
    var msg = await db.OutboxMessages
        .OrderByDescending(x => x.OccurredAt)
        .FirstAsync();

    Console.WriteLine("=== OutboxMessage ===");
    Console.WriteLine($"Id: {msg.Id}");
    Console.WriteLine($"Type: {msg.Type}");
    Console.WriteLine($"Version: {msg.Version}");
    Console.WriteLine($"OccurredAt: {msg.OccurredAt}");
    Console.WriteLine("Payload:");
    Console.WriteLine(msg.Payload);

    // おまけ：JSONとしてパースできるかチェック✅
    using var doc = JsonDocument.Parse(msg.Payload);
    Console.WriteLine("JSON Parse: OK ✅");
}
```

---

## 9) AI（Copilot/Codex）に手伝わせるなら🤖🪄

おすすめの頼み方はこんな感じ👇（短くてOK！）

* 「OrderCreated の payload 用 record を作って。PIIは入れないで。orderId と customerId と total と currency だけで」🧾✨
* 「OutboxEnvelope を record で。messageId/type/version/occurredAt/data にして」✉️
* 「System.Text.Json で camelCase でシリアライズする helper を作って。UTF-8 bytes でサイズ制限チェックも入れて」📏✅

AIが出したコードは、ここだけは人間がチェックしてね👇👀

* **Payloadに個人情報が混ざってない？** 🙈
* **サイズチェックが“文字数”じゃなく“UTF-8バイト”になってる？** 📏
* **messageId（OutboxId）が入ってる？**（次章以降で効く✨）🪪

---

## 10) まとめ：この章で覚えたこと🎁✨

* Payloadは「あとで送る荷物の中身」📦🚚
* まずは **必要最小限** ＋ **ID参照** が安全でラク🔗🧡
* JSONは `System.Text.Json` でシリアライズしやすい✨([Microsoft Learn][2])
* サイズチェックを入れると、運用の地雷を踏みにくい📏🧯

---

## 仕上げチェックリスト✅📝（提出前にこれだけ！）

* [ ] Payloadは必要最小限？（便利そうな情報を盛ってない？）👼
* [ ] 個人情報（住所・氏名・メール等）が入ってない？🙈
* [ ] `messageId`（OutboxId）が入ってる？🪪
* [ ] `version` がある？（次章で助かる🏷️）
* [ ] JSONとしてパースできる？（保存後に `JsonDocument.Parse` で確認✅）
* [ ] サイズチェックがある？（UTF-8 bytesで）📏

---

## 次章チラ見せ👀🏷️

次は「Payloadの形が変わる未来」に備えて、**契約（バージョン）** をやるよ〜🔁✨
（`v1` → `v2` にしても壊れない設計、ここが“強いOutbox”の分かれ道💪）

[1]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14?utm_source=chatgpt.com "What's new in C# 14"
[2]: https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/migrate-from-newtonsoft?utm_source=chatgpt.com "Migrate from Newtonsoft.Json to System.Text.Json - .NET"
