# 第04章：Sagaの超ざっくり定義（進む＋戻す）🧩🔁

![Forward flow and Compensation (Undo) flow.](./picture/saga_cs_study_004_compensation_flow.png)


## 4.1 今日のゴール🎯✨

この章が終わると、こんな感じで説明できるようになります😊

* Sagaって何？👉「**一連のステップ**」＋「**失敗したら帳尻合わせ（補償）**」のセットだよ🙆‍♀️
* 「戻す」って何？👉 DBのロールバックじゃなくて、**補償トランザクション**（後から取り消し操作）だよ🧾🔁
* ざっくりC#で「進む→失敗→戻す」をミニ実装して、動きの感覚をつかむよ💻✨

---

## 4.2 Sagaの定義（超ざっくり）📌

![Saga Definition](./picture/saga_cs_study_004_definition.png)

Saga（サーガ）は、分散システム（複数サービス・複数DB・外部APIなど）で、
**「サービスごとのローカルトランザクション」を順番に進めていく**パターンです🚶‍♀️🚶‍♂️

そして途中で失敗したら…
**すでに成功した分を、補償トランザクションで順番に“帳尻合わせ”していく**のがポイントです🧾✨
この考え方で、全体としてデータ整合性（最終的に筋が通る状態）を保ちます🛡️ ([Microsoft Learn][1])

---

## 4.3 「進む」フローと「戻す」フロー（図でイメージ）🗺️🧠

![Forward vs Backward](./picture/saga_cs_study_004_forward_backward.png)

例：ECの「注文→決済→在庫→配送」🛒💳📦🚚

### 成功と失敗（返金）の流れのイメージ 🗺️🧠
```mermaid
graph TD
    subgraph Forward [成功フロー (進む)]
        O[① 注文] --> P[② 決済]
        P --> S[③ 在庫]
        S --> Sh[④ 配送]
    end
    
    subgraph Compensation [失敗フロー (戻す/帳尻合わせ)]
        F[❌ ④ 配送失敗] -- "起点" --> C3[🔙 ③ 在庫戻し]
        C3 --> C2[🔙 ② 返金]
        C2 --> C1[🔙 ① キャンセル]
    end

    Sh -.-> F
    style F fill:#f66,stroke:#333
```

こんなふうに「成功した分を逆順で帳尻合わせ」していきます🔁💡

---

## 4.4 ここ超重要：「ロールバック」と「補償」は別モノ🙅‍♀️🧾

![Rollback vs Compensation](./picture/saga_cs_study_004_rollback_vs_comp.png)

**DBトランザクションのロールバック**

* 同じDBの中で「やっぱナシ！」って戻す感じ💾↩️
* 速いし確実（そのDBの中だけなら）✨

**Sagaの補償トランザクション**

* “後から”取り消し操作をする感じ🧾🔁
* しかも補償自体も「いつか成功する」世界（＝最終的整合性）🌙
* 補償も失敗することがあるので、**再開・再試行・冪等**が大事になるよ🛡️ ([Microsoft Learn][2])

---

## 4.5 「逆操作ができない」こと、普通にある😵‍💫

![Impossible Reversal](./picture/saga_cs_study_004_impossible_reversal.png)

補償は、数学みたいに「完全に元に戻す」とは限りません🙅‍♀️
現実にはこういうのがあるあるです👇

* ✅ **返金**はできるけど、手数料が戻らない
* ✅ **メール送信**は取り消せない（代わりに謝罪メール…📩🙏）
* ✅ **配送開始後**は止められない（代替：返品受付・返金・クーポン🎁）

![Compensation Strategy](./picture/saga_cs_study_004_comp_strategy.png)

だから補償は「逆操作」よりも、**帳尻合わせ（ユーザーと会社の被害を最小化）**って感覚が近いです🧠✨

---

## 4.6 ミニ演習①：補償を“1行”で書いてみよう📝😊

下の表の「補償（戻す）」を、まずは**1行**で埋めてみてください💪✨
（完璧じゃなくてOK！「まず案を出す」が大事💡）

| ステップ（進む）                  | 補償（戻す：帳尻合わせ）     |
| ------------------------- | ---------------- |
| 注文作成（OrderCreated）🛒      | 例：注文をキャンセル状態にする  |
| 決済確定（PaymentCaptured）💳   | 例：返金する（Refund）   |
| 在庫確保（InventoryReserved）📦 | 例：在庫予約を取り消す      |
| 配送手配（ShipmentCreated）🚚   | 例：配送をキャンセル（可能なら） |

🧠コツ：補償は「ユーザー体験」もセットで考えると強いです😊✨

---

## 4.7 ミニ演習②：C#で“超ミニSaga”を書いて動きを掴む💻🔁

![Code Flow Visualization](./picture/saga_cs_study_004_code_flow.png)

ここでは「本物の決済や在庫」じゃなくて、**コンソールで流れだけ再現**します🎮
（動きの理解がゴールなので、まずはミニでOK🙆‍♀️）

> 参考：2026年1月時点では .NET 10 / C# 14 が最新ラインです（.NET 10.0.2 が 2026-01-13 リリース）([Microsoft Learn][3])
> Visual Studio 2026 は .NET 10 をフルサポートします。([Microsoft for Developers][4])

```csharp
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

record SagaStep(string Name, Func<Task> Forward, Func<Task> Compensate);

class Program
{
    static async Task Main()
    {
        Console.WriteLine("=== Mini Saga: 進む → 失敗 → 補償 ===");

        var steps = new List<SagaStep>
        {
            new("① 注文作成", async () =>
            {
                await Task.Delay(200);
                Console.WriteLine("✅ 注文作成 OK");
            },
            async () =>
            {
                await Task.Delay(200);
                Console.WriteLine("↩️ 補償: 注文キャンセル");
            }),

            new("② 決済確定", async () =>
            {
                await Task.Delay(200);
                Console.WriteLine("✅ 決済確定 OK");
            },
            async () =>
            {
                await Task.Delay(200);
                Console.WriteLine("↩️ 補償: 返金処理");
            }),

            new("③ 在庫確保", async () =>
            {
                await Task.Delay(200);
                Console.WriteLine("✅ 在庫確保 OK");
            },
            async () =>
            {
                await Task.Delay(200);
                Console.WriteLine("↩️ 補償: 在庫予約取消");
            }),

            new("④ 配送手配（ここで失敗させる）", async () =>
            {
                await Task.Delay(200);
                throw new Exception("配送APIがタイムアウト💥");
            },
            async () =>
            {
                await Task.Delay(200);
                Console.WriteLine("↩️ 補償: 配送キャンセル（可能なら）");
            }),
        };

        try
        {
            await RunSagaAsync(steps);
            Console.WriteLine("🎉 Saga 全部成功！");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"🧯 Saga 失敗: {ex.Message}");
        }
    }

    static async Task RunSagaAsync(List<SagaStep> steps)
    {
        var completed = new Stack<SagaStep>();

        foreach (var step in steps)
        {
            Console.WriteLine($"\n➡️ {step.Name} を実行…");

            try
            {
                await step.Forward();
                completed.Push(step);
            }
            catch
            {
                Console.WriteLine("💥 失敗！補償を逆順で実行するよ…🔁");

                while (completed.Count > 0)
                {
                    var done = completed.Pop();
                    Console.WriteLine($"⬅️ {done.Name} の補償…");

                    try
                    {
                        await done.Compensate();
                    }
                    catch (Exception cex)
                    {
                        // ここは後の章で「冪等性」「再試行」「手動介入」に繋がるポイント！
                        Console.WriteLine($"⚠️ 補償も失敗: {cex.Message}");
                    }
                }

                throw;
            }
        }
    }
}
```

✅ポイント

* **進む**：Forward を順番に実行🚶‍♀️
* **失敗**：例外が出たらストップ🧯
* **戻す**：成功済みの分だけ、**逆順**で Compensate を実行🔁

---

## 4.8 よくある勘違い・事故ポイント集🚧😇

* 「補償＝完全に元通り」ではない🙅‍♀️（帳尻合わせ）
* 「補償は必ず成功」ではない😱（だから後で**冪等性**が超重要になる）

![Idempotency Importance](./picture/saga_cs_study_004_idempotency_need.png)([Microsoft Learn][2])
* 「補償を2回やる」事故が起きやすい⚠️（リトライ・重複メッセージで発生）
* 「キャンセルできない操作」を前に置くと地獄になりやすい🔥（順番設計が大事）

---

## 4.9 AI活用（Copilot / Codex）🤖✨

「補償案を増やす」「危険な点を見つける」にAIがめちゃ強いです💪

**① 補償案を複数出してもらう🧠💡**

* 「注文→決済→在庫→配送のSagaで、各ステップの補償案を3つずつ出して。ユーザー体験が良い順に並べて」

**② “取り消せない操作”を洗い出す🕳️😵‍💫**

* 「このフローで“後から取り消せない/取り消しづらい”操作を列挙して、代替の補償案も提案して」

**③ ミニSagaコードの改善を頼む🛠️✨**

* 「このC#のミニSagaを、ログが読みやすくなるように整形して。例外メッセージも分かりやすくして」

**④ 章のミニ演習の答え合わせ✅**

* 「この表の補償案、業務的におかしいところある？リスクと改善案をセットで教えて」

---

[1]: https://learn.microsoft.com/en-us/azure/architecture/patterns/saga?utm_source=chatgpt.com "Saga Design Pattern - Azure Architecture Center"
[2]: https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction?utm_source=chatgpt.com "Compensating Transaction pattern - Azure"
[3]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14?utm_source=chatgpt.com "What's new in C# 14"
[4]: https://devblogs.microsoft.com/dotnet/dotnet-conf-2025-recap/?utm_source=chatgpt.com "Celebrating .NET 10, Visual Studio 2026, AI, Community, & ..."
