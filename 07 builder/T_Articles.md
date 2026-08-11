<%*
/* ========================================
こじかノート：記事テンプレート
======================================== */

// ----------------------------------------
// ① 記事タイトルを入力
// ----------------------------------------

const title = await tp.system.prompt(
"記事タイトルを入力してください"
);

if (!title) {
new Notice("タイトルが入力されていません");
return;
}

// ----------------------------------------
// ② ファイル名をタイトルに変更
// ----------------------------------------

await tp.file.rename(title);

// ----------------------------------------
// ③ Categories.md を読み込む
// ----------------------------------------

const categoryFile = tp.app.vault.getAbstractFileByPath(
"07 builder/Categories.md"
);

if (!categoryFile) {
new Notice("Categories.md が見つかりません");
return;
}

const categoryText = await tp.app.vault.read(categoryFile);

// 「- カテゴリー名」の行だけを取得
const categories = categoryText
.split("\n")
.map(line => line.trim())
.filter(line => line.startsWith("- "))
.map(line => line.substring(2).trim())
.filter(line => line !== "");

if (categories.length === 0) {
new Notice("Categories.md にカテゴリーがありません");
return;
}

// ----------------------------------------
// ④ statusを選択
// ----------------------------------------

const status = await tp.system.suggester(
["未公開", "公開"],
["未公開", "公開"],
false,
"公開状態を選択"
);

if (!status) {
return;
}

// ----------------------------------------
// ⑤ Primary categoryを1つ選択
// ----------------------------------------

const primary = await tp.system.suggester(
categories,
categories,
false,
"Primary categoryを選択"
);

if (!primary) {
return;
}

// ----------------------------------------
// ⑥ 追加カテゴリーを複数選択
// ----------------------------------------
let remainingCategories = categories.filter(
category => category !== primary
);

const additionalCategories = [];

while (remainingCategories.length > 0) {

const choices = [
    ...remainingCategories,
    "選択終了"
];

const selected = await tp.system.suggester(
    choices,
    choices,
    false,
    "追加カテゴリーを選択"
);

if (!selected || selected === "選択終了") {
    break;
}

additionalCategories.push(selected);

remainingCategories = remainingCategories.filter(
    category => category !== selected
);

}

// ----------------------------------------
// ⑦ categoriesを作成
// Primaryを必ず先頭にする
// ----------------------------------------

const allCategories = [
primary,
...additionalCategories
];

// ----------------------------------------
// ⑧ Frontmatter + 本文
// ----------------------------------------

tR += `---
title: "${title}"
status: "${status}"
categories:
${allCategories.map(category => `  - "${category}"`).join("\n")}
---

# ${title}

## 結論

## 解説

## 関連資料
### ①
> 引用
#### 翻訳
#### ポイント

### ②
> 引用
#### 翻訳
#### ポイント


## 小児科医のコメント
`;
%>
