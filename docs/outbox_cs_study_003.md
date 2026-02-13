# 第03章：開発環境セットアップ（Windows）🪟🧰

## 今日のゴール🏁✨

この章が終わったら、**Outbox学習用のソリューション一式**を作って、
**Web API（注文など）＋配送係（Relay）＋DB** まで「動き出す準備」完了！になります🎉

---

## 1) この章で作る“ミニ構成”🧩📦

![Mini Architecture Components](./picture/outbox_cs_study_003_mini_architecture.png)

最初はシンプルでOK！あとから育てます🌱

* **Orders.Api**：注文を作るWeb API（あとで「業務テーブル＋Outbox」を同じトランザクションで書く）🛒🌐
* **Outbox.Relay**：Outboxテーブルを見て、未送信を“配送”する常駐Worker🚚⏱️
* **Shared.Contracts**：イベント（メッセージ）の型を共有するクラスライブラリ📮🧾
* **DB（SQL Server LocalDB）**：ローカルで軽く動かす用🗄️✨

---

## 2) まずは最新の .NET / EF Core をそろえる🧠✨

2026年2月時点では **.NET 10（LTS）** が最新で、最新パッチは **10.0.2** です。([Microsoft][1])
EF Core も **EF Core 10（LTS）** があり、**.NET 10 が必要**です。([Microsoft Learn][2])

---

## 3) Visual Studio で準備する（おすすめ）🧑‍💻💖

![Visual Studio Setup](./picture/outbox_cs_study_003_visual_studio_setup.png)

## 3-1. Visual Studio を入れる🧰✨

**Visual Studio 2026** が出ています（安定版のリリース履歴も公開されています）。([Microsoft Learn][3])

インストーラーで、ざっくりこのへんを入れておくと安心です✅

* **ASP.NET と Web 開発**（Orders.Api 用）([Microsoft Learn][4])
* （必要なら）**.NET デスクトップ開発**（便利ツール系が増える）([Microsoft Learn][5])

> 💡「どのワークロード入れればいい？」って迷ったら、Visual Studio の公式手順もこれが入口だよ🧭([Microsoft Learn][5])

---

## 3-2. ソリューションを作る📁✨

![Solution Structure](./picture/outbox_cs_study_003_solution_structure.png)

1. Visual Studio → **新しいプロジェクトの作成**
2. まずは **空のソリューション**（Blank Solution）を作成（例：`OutboxTutorial`）🧳
3. ソリューションを右クリック → **追加** → **新しいプロジェクト**

   * **ASP.NET Core Web API**（プロジェクト名：`Orders.Api`）🌐
   * **Worker Service**（プロジェクト名：`Outbox.Relay`）🚚
   * **クラス ライブラリ**（プロジェクト名：`Shared.Contracts`）📦

> 🎯 ここでは「雛形が作れて、ビルドできる」まで行けばOK！

---

## 4) DB（SQL Server LocalDB）を用意する🗄️🪄

## 4-1. LocalDB ってなに？（超ざっくり）😺

![SQL LocalDB Concept](./picture/outbox_cs_study_003_localdb_concept.png)

“ローカルでだけ”軽く使える **SQL Server** だよ！
本番DBの代わりに、まずは学習用で使うのにちょうどいい感じ✨

LocalDB の公式ドキュメントもここにまとまってます。([Microsoft Learn][6])

---

## 4-2. LocalDB が入ってるかチェック👀✅

PowerShell で確認（ダメなら後ろの「困ったとき」へ🧯）

```powershell
sqllocaldb info
```

`MSSQLLocalDB` みたいなのが出てくればOK🎉

---

## 4-3. 接続文字列（あとで使う）🔗✨

まずはこの形を覚えちゃえばOK（あとで `appsettings.json` に入れるよ📄）

```json
{
  "ConnectionStrings": {
    "Default": "Server=(localdb)\\MSSQLLocalDB;Database=OutboxDemo;Trusted_Connection=True;TrustServerCertificate=True"
  }
}
```

---

## 5) EF Core と CLI ツールを入れる🧪🔧

## 5-1. NuGet パッケージ（プロジェクト側）📦✨

`Orders.Api` に入れる想定（あとでDbContext作る用）🧠

* `Microsoft.EntityFrameworkCore`
* `Microsoft.EntityFrameworkCore.SqlServer`
* `Microsoft.EntityFrameworkCore.Design`

EF Core のリリースと対応関係（EF10が .NET 10 対応）も公式にまとまってます。([Microsoft Learn][2])

---

## 5-2. `dotnet ef` を使えるようにする（おすすめ）🛠️✨

![EF Core CLI Tools](./picture/outbox_cs_study_003_ef_core_cli_tools.png)

EF Core のCLI（`dotnet ef`）は、公式が手順を案内しています。([Microsoft Learn][7])
NuGet 側にも `dotnet-ef` パッケージがあります。([NuGet][8])

インストール（PowerShell）👇

```powershell
dotnet tool install --global dotnet-ef
dotnet tool update --global dotnet-ef
```

入ったか確認👇

```powershell
dotnet ef --version
```

> 💡 もしここで失敗したら、「.NET 10 SDK が入ってるか」をまず疑うのが近道だよ（次の“自己チェック”へ）🧯

---

## 6) ここまでの“自己チェック”✅🎯

## 6-1. .NET SDK 確認🔍

```powershell
dotnet --info
```

* `.NET SDK` に **10.0.x** が見えたらOK（最新は 10.0.2）。([Microsoft][9])

---

## 6-2. Visual Studio でビルド確認🧱✨

* ソリューションを右クリック → **ソリューションのビルド**
* エラーが0ならOK🎉

---

## 6-3. LocalDB 確認🗄️

```powershell
sqllocaldb info
```

---

## 7) Visual Studio Code でやる場合（軽量ルート）⌨️✨

![VS Code Lightweight Dev](./picture/outbox_cs_study_003_vscode_lightweight.png)

## 7-1. C# 開発キット（C# Dev Kit）を入れる🧩

VS Code のC#サポートは **C# Dev Kit** が中心になっています。([Visual Studio Code][10])
（拡張機能マーケットにも載ってます。）([Visual Studio Marketplace][11])

VS Code → 拡張機能で **「C# Dev Kit」** を検索してインストール🔎✨

---

## 7-2. VS Code でソリューションを開く📂

* `OutboxTutorial.sln` のあるフォルダを開く
* 自動で「必要な拡張入れる？」って聞かれたらOK押す🙆‍♀️

---

## 7-3. CLIで雛形を作る（VS Code派におすすめ）🧪

作業用フォルダで👇

```powershell
dotnet new sln -n OutboxTutorial

dotnet new webapi -n Orders.Api
dotnet new worker -n Outbox.Relay
dotnet new classlib -n Shared.Contracts

dotnet sln OutboxTutorial.sln add Orders.Api/Orders.Api.csproj
dotnet sln OutboxTutorial.sln add Outbox.Relay/Outbox.Relay.csproj
dotnet sln OutboxTutorial.sln add Shared.Contracts/Shared.Contracts.csproj
```

ビルド👇

```powershell
dotnet build OutboxTutorial.sln
```

---

## 8) 困ったとき（ありがち）🧯😭

## A) `dotnet` が見つからない💥

* だいたい **SDKが入ってない** or **PATHが通ってない**
* `.NET 10 SDK` を入れ直して、PC再起動で直ること多いよ✨([Microsoft][9])

---

## B) `dotnet ef` が入らない / 動かない😵‍💫

* まず `dotnet --info` で **.NET 10 SDK** が見えてるか確認👀
* そのうえで `dotnet tool update --global dotnet-ef` でもう一回🔁([Microsoft Learn][7])

---

## C) LocalDB がいない / `sqllocaldb` が動かない🗄️💦

LocalDB の公式説明を見ながら、LocalDB を入れ直すのが早いです。([Microsoft Learn][6])

---

## 9) AI（Copilot/Codex系）に聞くときの“うまい聞き方”🤖💡

セットアップで詰まりやすいから、AIはめっちゃ便利✨
コピペでOKな聞き方👇

* 「`dotnet --info` の結果はこれ。VS 2026でWeb API作りたいのにテンプレが出ない。原因候補を3つと確認手順を出して」🧩
* 「`sqllocaldb info` が失敗する。考えられる原因と直し方を、PowerShellコマンド付きで」🪄
* 「このエラー全文を貼るので、まず“何が起きてるか”を日本語で超やさしく説明して」📘💗

---

## ✅この章のクリア条件（チェックリスト）🎀

* Visual Studio で `Orders.Api / Outbox.Relay / Shared.Contracts` が作れている🧩
* ソリューションがビルドできる（エラー0）✅
* `dotnet --info` で .NET 10 SDK が見える👀([Microsoft][9])
* `sqllocaldb info` が動く🗄️
* `dotnet ef --version` が動く🛠️([Microsoft Learn][7])

[1]: https://dotnet.microsoft.com/en-us/download/dotnet?utm_source=chatgpt.com "Browse all .NET versions to download | .NET"
[2]: https://learn.microsoft.com/en-us/ef/core/what-is-new/?utm_source=chatgpt.com "EF Core releases and planning"
[3]: https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-history?utm_source=chatgpt.com "Visual Studio Release History"
[4]: https://learn.microsoft.com/en-us/visualstudio/get-started/csharp/tutorial-aspnet-core?view=visualstudio&utm_source=chatgpt.com "Tutorial: Create C# ASP.NET Core web application"
[5]: https://learn.microsoft.com/ja-jp/visualstudio/install/install-visual-studio?view=visualstudio&utm_source=chatgpt.com "Visual Studio をインストールし、お好みの機能を選択する"
[6]: https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/sql-server-express-localdb?view=sql-server-ver17&utm_source=chatgpt.com "SQL Server Express LocalDB"
[7]: https://learn.microsoft.com/en-us/ef/core/cli/dotnet?utm_source=chatgpt.com "EF Core tools reference (.NET CLI)"
[8]: https://www.nuget.org/packages/dotnet-ef?utm_source=chatgpt.com "dotnet-ef 10.0.2"
[9]: https://dotnet.microsoft.com/en-US/download/dotnet/10.0?utm_source=chatgpt.com "Download .NET 10.0 (Linux, macOS, and Windows) | .NET"
[10]: https://code.visualstudio.com/docs/languages/csharp?utm_source=chatgpt.com "Installing C# support"
[11]: https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.csdevkit&utm_source=chatgpt.com "C# Dev Kit"
