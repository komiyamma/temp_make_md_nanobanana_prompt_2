# 第13章：合成の型③ Adapter入門🎁🔌（型を合わせるだけ）

## この章でできるようになること🎯✨

* 外部APIの“クセ強データ”を、アプリ内部の“きれいな型”に変換できるようになる🧼✨
* `snake_case` → `camelCase` みたいな「形合わせ」を、アプリの“境界”でまとめて引き受けられる🛡️
* 「外部の都合」がコード全体に漏れてベタベタになるのを防げる🚧💦

※ちなみに本日時点の安定版TypeScriptは npm 上で `5.9.3` が “Latest” になっています。([npm][1])
そして TypeScript 6.0 は「5.9 と 7.0 の橋渡し（bridge）」で、7.0 はネイティブ化（Project Corsa）に向かって進んでいる、という流れが公式ブログで説明されています。([Microsoft for Developers][2])
（だからこそ、“境界で型を整える”の価値がどんどん上がるよ〜って話🥰）

---

## 1) Adapterってなに？🧠🔌（めっちゃ短く）

Adapter（アダプター）は一言でいうと…

**「外から来たデータ（外部の形）を、アプリの中で使いやすい形に変換する“変換係”」**だよ💡✨

イメージは“変換プラグ”🔌
コンセントの形が違っても、変換プラグをかませれば使えるでしょ？それと同じ〜😊

---

## 2) なぜ必要？（入れないと起きる事故💥）

外部APIって、こういう“外部都合”がよくあるの👇

* `snake_case` でキーが来る🐍
* 日付が文字列 `"2026-01-15T..."` で来る📅
* 数字が `"1200"` みたいに文字で来る😇
* `null` が混ざる / optional がぐちゃぐちゃ🌀
* 命名がアプリ内と合わない（`user_id` vs `id` とか）

これを変換せずにそのままアプリ内に持ち込むと…

* 画面・ロジック・保存・テスト、全部が外部形式に引きずられる😱
* 途中からAPI仕様が変わったら、修正箇所が爆発する🌋

だから、**境界でまとめて変換**するのが超大事🛡️✨
その役が Adapter だよ🎁

---

## 3) “境界”ってどこ？🏠🚪

雑に言うとここ👇

* 外部APIを叩くところ（HTTP）🌐
* DBや外部SDKを呼ぶところ🧰
* ファイルやCSV読み込み📄

つまり **「外から中へ入る瞬間」** が境界！🚪✨
ここで “内部の型” に変換してから、内部ロジックへ渡すのがキレイ🧼

---

## 4) Adapterの黄金ルール🌟（これだけ覚えて！）

### ✅ ルールA：Adapterは「変換だけ」🧊

* OK：`snake_case` → `camelCase`、型変換、日付パース、必須チェック
* NG：割引計算とか、業務ルールを混ぜる（それはStrategy/ドメイン側の仕事）🙅‍♀️

### ✅ ルールB：内部の型（ドメイン）を汚さない🧼

* 内部は内部の命名・型で統一
* 外部の命名（`user_id`）を内部に持ち込まない

### ✅ ルールC：境界の外側の変更を、Adapterに閉じ込める🧰

* 外部仕様が変わっても、基本は Adapter だけ直せばOKにする💪✨

---

## 5) 例題：外部APIの `snake_case` を `camelCase` に直す🐍➡️🐫✨

### 5-1) 外部から来るデータ（外部DTO）📦

たとえば外部APIがこんなJSON返すとするね👇

```ts
// 外部APIのレスポンス（例）
type ExternalUserDto = {
  user_id: number;
  display_name: string;
  created_at: string;      // ISO文字列
  is_premium: 0 | 1;       // 0/1で来るタイプ😇
};
```

### 5-2) アプリ内部で使いたい型（内部モデル）🧼

内部はこうしたい👇

```ts
// アプリ内部で使う型
type User = {
  id: number;
  displayName: string;
  createdAt: Date;
  isPremium: boolean;
};
```

ポイントはここ💡
**内部は“自分の都合のいい型”でOK**。外部に合わせなくていいよ🙆‍♀️✨

---

## 6) Adapter本体：DTO → 内部型へ変換する🛠️✨

```ts
export function adaptUser(dto: ExternalUserDto): User {
  // 最低限の“安全チェック”🛡️（必要に応じて増やしてOK）
  if (typeof dto.user_id !== "number") throw new Error("user_id must be number");
  if (typeof dto.display_name !== "string") throw new Error("display_name must be string");
  if (typeof dto.created_at !== "string") throw new Error("created_at must be string");

  const createdAt = new Date(dto.created_at);
  if (Number.isNaN(createdAt.getTime())) throw new Error("created_at is invalid date string");

  return {
    id: dto.user_id,
    displayName: dto.display_name,
    createdAt,
    isPremium: dto.is_premium === 1,
  };
}
```

### ここが気持ちいいポイント😍✨

* 変換ロジックが **1か所に集まる**
* 内部側は `User` だけ見ればよくなる（`snake_case` を忘れられる）🧠✨

---

## 7) 使う側：外部呼び出し→Adapter→内部へ🌈

外部API取得は `fetch` で例を出すね（Node.js 18 では `fetch` がデフォルトで使える形で提供された流れが公式ブログにあるよ）([Node.js][3])

```ts
async function fetchUserFromApi(userId: number): Promise<User> {
  const res = await fetch(`https://example.com/api/users/${userId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const dto = (await res.json()) as ExternalUserDto;

  // 🌟ここが境界！ここで内部型へ！
  return adaptUser(dto);
}
```

```mermaid
flowchart LR
  Api["External API"] -->|"JSON (snake_case)"| DTO["ExternalUserDto"]
  DTO --> Adapter["adaptUser Function"]
  Adapter -->|Transform| Domain["User Model (camelCase)"]
```

内部の他のコードは、もう `User` しか知らなくてOK😌✨

---

## 8) よくある命名・置き場所のコツ🗂️📝

* `ExternalUserDto`：外部レスポンス用（DTO）📦
* `adaptUser` / `UserAdapter`：変換役🔌
* フォルダ例（イメージ）🧺

  * `src/domain/...`（内部の中心🫶）
  * `src/infra/api/...`（外部通信🌐）
  * `src/infra/adapters/...`（Adapter置き場🎁）

「外部の匂いがするもの」は `infra` 側に寄せると迷子になりにくいよ🐣✨

---

## 9) Adapterの落とし穴🕳️🛑（初心者がハマりやすい）

### ❌ 落とし穴1：業務ルールを混ぜる

「プレミアムなら割引率が…」とかをAdapterに書き始めると、責務が混ざってグチャる🥲
➡️ Adapterは“変換だけ”にして、業務ルールは別（Strategyやドメイン）へ✨

### ❌ 落とし穴2：外部型を内部へ漏らす

画面側で `dto.display_name` を直接触り始めると、漏れ始めて終わる😇
➡️ 境界で `User` にして渡す！

### ❌ 落とし穴3：例外メッセージが雑

`throw new Error("bad")` だと原因が追えない💦
➡️ 何がダメか分かるメッセージにする（最低限でOK）🧩

---

## 10) ミニ演習✍️🎀（手を動かそ！）

### 演習A：DTO変換を書いてみよう🧪✨

次の外部DTOを、内部型に変換してね👇

```ts
type ExternalProductDto = {
  product_id: string;       // 文字で来る😇
  product_name: string;
  price_yen: number;
  tags: string[] | null;    // nullが来ることもある
};

type Product = {
  id: string;
  name: string;
  priceYen: number;
  tags: string[];           // 内部では必ず配列にしたい
};
```

✅ 目標

* `product_id` → `id`
* `product_name` → `name`
* `price_yen` → `priceYen`
* `tags` が `null` なら `[]` にする

ヒント：`tags ?? []` が使えるよ😉✨

---

## 11) AI拡張の使い方（賢くお願いするコツ）🤖✨

そのまま丸投げじゃなくて、**条件をちゃんと付ける**のが勝ち🏆

### お願い例📣

* 「このDTOを内部型に変換するAdapter関数を書いて。変換以外のロジックは禁止。nullは空配列にして。例外メッセージは具体的に」
* 「snake_case を camelCase に変換する mapping を、型安全にしたい。境界で閉じる設計で提案して」
* 「Adapterのユニットテスト例も一緒に出して（正常系/異常系）」

### 出力レビュー観点👀✅

* 変換“だけ”になってる？
* 外部型が内部に漏れてない？
* エラー時に原因が追える？
* 変換が1か所に集まってる？

---

## 12) 章末チェック✅🌸

* Adapterは「変換係」🔌
* 外部の形は、境界で内部の形へ🎁
* Adapterに業務ルールを混ぜない🧊
* 内部は内部の命名・型で統一🧼

---

次章（第14章）では、このAdapterを **「境界を守る」設計としてどう育てるか**（置き場所・命名・増えた時の整理📦✨）を、もう一段リアルにやっていくよ〜！😊🛡️

[1]: https://www.npmjs.com/package/typescript?activeTab=versions&utm_source=chatgpt.com "typescript"
[2]: https://devblogs.microsoft.com/typescript/progress-on-typescript-7-december-2025/?utm_source=chatgpt.com "Progress on TypeScript 7 - December 2025"
[3]: https://nodejs.org/en/blog/announcements/v18-release-announce?utm_source=chatgpt.com "Node.js 18 is now available!"
