from pathlib import Path
from datetime import datetime
import markdown
import yaml
import html


# ============================================================
# フォルダ設定
# ============================================================

# k.pyが入っているフォルダ
BUILDER = Path(__file__).parent

# プロジェクトのルート
BASE = BUILDER.parent

# 記事
ARTICLES = BASE / "03 Articles"

# カテゴリ一覧
CATEGORIES_FILE = BUILDER / "Categories.md"

# HTML出力先
OUTPUT = BASE / "output"

# CSS・ロゴ
ASSETS = OUTPUT / "assets"

# outputフォルダがなければ作る
OUTPUT.mkdir(exist_ok=True)


# ============================================================
# Categories.mdを読み込む
# ============================================================

def load_categories():
    """
    Categories.mdからカテゴリ一覧を読み込む。

    「- カテゴリ名」
    の形式の行をカテゴリとして扱う。
    """

    if not CATEGORIES_FILE.exists():
        print("⚠ Categories.md が見つかりません")
        return []

    text = CATEGORIES_FILE.read_text(encoding="utf-8")

    categories = (
        text.split("\n")
        and [
            line.strip()[2:].strip()
            for line in text.split("\n")
            if line.strip().startswith("- ")
            and line.strip()[2:].strip() != ""
        ]
    )

    if not categories:
        print("⚠ Categories.md にカテゴリがありません")
        return []

    return categories


# ============================================================
# Markdownのセクションを<section>で囲む
# ============================================================

def add_sections(html_text):
    """
    結論・解説・関連資料・小児科医のコメントを
    <section>で囲む。
    """

    sections = {
        "結論": "conclusion",
        "解説": "explanation",
        "関連資料": "references",
        "小児科医のコメント": "doctor-comment",
    }

    current_section = None

    lines = html_text.splitlines()
    result = []

    for line in lines:

        # --------------------------------
        # <h2>...</h2> を探す
        # --------------------------------

        if line.startswith("<h2>") and line.endswith("</h2>"):

            # h2の中身だけ取り出す
            title = line[4:-5]

            # このh2が4つのセクションのどれか？
            if title in sections:

                # すでにsectionが開いていたら閉じる
                if current_section is not None:
                    result.append("</section>")

                # CSS用のclass名
                class_name = sections[title]

                # sectionを開始
                result.append(
                    f'<section class="{class_name}">'
                )

                # h2自体はそのまま残す
                result.append(line)

                current_section = class_name

                continue

        # 普通の行はそのまま追加
        result.append(line)

    # 最後のsectionを閉じる
    if current_section is not None:
        result.append("</section>")

    return "\n".join(result)


# ============================================================
# Frontmatterを読み取る
# ============================================================

def read_article(article_path):
    """
    Markdownファイルから
    Frontmatterと本文を分離して読み取る。
    """

    text = article_path.read_text(encoding="utf-8")

    # Frontmatterがない場合
    if not text.startswith("---"):
        print(f"⚠ Frontmatterがありません: {article_path.name}")
        return None

    # 最初の---の次から、次の---までを取得
    parts = text.split("---", 2)

    if len(parts) != 3:
        print(f"⚠ Frontmatterを読み取れません: {article_path.name}")
        return None

    frontmatter_text = parts[1]
    body = parts[2].lstrip()

    data = yaml.safe_load(frontmatter_text)

    if data is None:
        data = {}

    return data, body


# ============================================================
# Markdown → HTML
# ============================================================

def markdown_to_html(md_text):

    body = markdown.markdown(
        md_text,
        extensions=[
            "extra",
            "tables",
            "fenced_code",
            "nl2br",
        ]
    )

    body = add_sections(body)

    return body


# ============================================================
# Markdownファイルの最終更新日を取得
# ============================================================

def get_update_date(article_path):

    timestamp = article_path.stat().st_mtime

    date = datetime.fromtimestamp(timestamp)

    return f"{date.year}年{date.month}月{date.day}日"


# ============================================================
# 記事HTMLを作る
# ============================================================

def create_article_html(article_path, data, body):

    title = data.get("title", article_path.stem)

    categories = data.get("categories", [])

    # categoriesが正しくリストになっているか確認
    if not isinstance(categories, list):
        categories = [categories]

    # Primary category
    if categories:
        primary = categories[0]
    else:
        primary = None

    # 最終更新日
    update_date = get_update_date(article_path)

    # --------------------------------------------------------
    # パンくずリスト
    # --------------------------------------------------------

    if primary:

        breadcrumb = f"""
<nav class="breadcrumb">

<a href="index.html">こじかノート</a>

<span> &gt; </span>

<a href="category/{html.escape(primary)}.html">
{html.escape(primary)}
</a>

<span> &gt; </span>

<span>{html.escape(title)}</span>

</nav>
"""

    else:

        breadcrumb = f"""
<nav class="breadcrumb">

<a href="index.html">こじかノート</a>

<span> &gt; </span>

<span>{html.escape(title)}</span>

</nav>
"""

    # --------------------------------------------------------
    # HTML全体
    # --------------------------------------------------------

    article_html = f"""<!DOCTYPE html>
<html lang="ja">

<head>

<meta charset="UTF-8">

<meta name="viewport"
     content="width=device-width, initial-scale=1">

<title>{html.escape(title)} | こじかノート</title>

<link rel="stylesheet"
     href="assets/style.css">

</head>

<body>

<header>

<h1>
<img src="assets/logo.svg" alt="こじかノート">
こじかノート
</h1>

</header>

<main>

{breadcrumb}

<article>

{body}

<p class="update-date">
最終更新日：{update_date}
</p>

</article>

</main>

<footer>

<p>© 2026 こじかノート</p>

</footer>

</body>

</html>
"""

    return article_html


# ============================================================
# カテゴリページを作る
# ============================================================

def create_category_page(category, articles):

    # --------------------------------------------------------
    # このカテゴリがcategoriesの何番目にあるかで並べる
    # --------------------------------------------------------

    def category_priority(article):

        categories = article["categories"]

        return categories.index(category)

    articles.sort(key=category_priority)

    # --------------------------------------------------------
    # 記事一覧
    # --------------------------------------------------------

    article_list = []

    for article in articles:

        title = article["title"]
        filename = article["filename"]

        article_list.append(
            f'<li><a href="../{filename}">'
            f'{html.escape(title)}'
            f'</a></li>'
        )

    article_list_html = "\n".join(article_list)

    # --------------------------------------------------------
    # カテゴリページ
    # --------------------------------------------------------

    category_html = f"""<!DOCTYPE html>
<html lang="ja">

<head>

<meta charset="UTF-8">

<meta name="viewport"
     content="width=device-width, initial-scale=1">

<title>{html.escape(category)} | こじかノート</title>

<link rel="stylesheet"
     href="../assets/style.css">

</head>

<body>

<header>

<h1>
<img src="../assets/logo.svg" alt="こじかノート">
こじかノート
</h1>

</header>

<main>

<nav class="breadcrumb">

<a href="../index.html">こじかノート</a>

<span> &gt; </span>

<span>{html.escape(category)}</span>

</nav>

<h2>{html.escape(category)}</h2>

<ul class="article-list">

{article_list_html}

</ul>

</main>

<footer>

<p>© 2026 こじかノート</p>

</footer>

</body>

</html>
"""

    return category_html


# ============================================================
# index.htmlを作る
# ============================================================

def create_index(categories):

    category_links = []

    for category in categories:

        category_links.append(
            f'<li>'
            f'<a href="category/{html.escape(category)}.html">'
            f'{html.escape(category)}'
            f'</a>'
            f'</li>'
        )

    category_links_html = "\n".join(category_links)

    index_html = f"""<!DOCTYPE html>
<html lang="ja">

<head>

<meta charset="UTF-8">

<meta name="viewport"
     content="width=device-width, initial-scale=1">

<title>こじかノート</title>

<link rel="stylesheet"
     href="assets/style.css">

</head>

<body>

<header>

<h1>
<img src="assets/logo.svg" alt="こじかノート">
こじかノート
</h1>

</header>

<main>

<h2>こじかノート</h2>

<p>
小児科医が、子どもに関する医学情報を
わかりやすく整理するサイトです。
</p>

<h2>カテゴリ</h2>

<ul class="category-list">

{category_links_html}

</ul>

</main>

<footer>

<p>© 2026 こじかノート</p>

</footer>

</body>

</html>
"""

    index_file = OUTPUT / "index.html"

    index_file.write_text(
        index_html,
        encoding="utf-8"
    )

    print("index.htmlを作成しました")


# ============================================================
# メイン処理
# ============================================================

def main():

    print("===== こじかノート サイト生成 =====")
    print()

    # --------------------------------------------------------
    # Categories.mdを読み込む
    # --------------------------------------------------------

    categories = load_categories()

    if not categories:
        print("カテゴリが取得できないため終了します。")
        return

    print("カテゴリ一覧：")
    for category in categories:
        print(f"  - {category}")

    print()

    # --------------------------------------------------------
    # categoryフォルダを作る
    # --------------------------------------------------------

    category_output = OUTPUT / "category"

    category_output.mkdir(exist_ok=True)

    # --------------------------------------------------------
    # カテゴリごとの記事を入れる箱
    # --------------------------------------------------------

    category_articles = {
        category: []
        for category in categories
    }

    # --------------------------------------------------------
    # Markdownファイルを処理
    # --------------------------------------------------------

    for article_path in ARTICLES.glob("*.md"):

        print(f"確認中 : {article_path.name}")

        result = read_article(article_path)

        if result is None:
            continue

        data, md_body = result

        # ----------------------------------------------------
        # statusを確認
        # ----------------------------------------------------

        status = data.get("status")

        if status != "公開":

            print("  → 未公開のためスキップ")
            continue

        # ----------------------------------------------------
        # categories
        # ----------------------------------------------------

        article_categories = data.get("categories", [])

        if not isinstance(article_categories, list):
            article_categories = [article_categories]

        if not article_categories:

            print("  ⚠ categoriesがありません")

        # ----------------------------------------------------
        # Categories.mdに存在するカテゴリか確認
        # ----------------------------------------------------

        valid_categories = []

        for category in article_categories:

            if category in categories:

                valid_categories.append(category)

            else:

                print(
                    f"  ⚠ Categories.mdに存在しないカテゴリ: "
                    f"{category}"
                )

        # ----------------------------------------------------
        # Markdown → HTML
        # ----------------------------------------------------

        body = markdown_to_html(md_body)

        # ----------------------------------------------------
        # 記事HTMLを作る
        # ----------------------------------------------------

        article_html = create_article_html(
            article_path,
            data,
            body
        )

        html_file = OUTPUT / f"{article_path.stem}.html"

        html_file.write_text(
            article_html,
            encoding="utf-8"
        )

        print(
            f"  → {html_file.name} を作成"
        )

        # ----------------------------------------------------
        # カテゴリ別に登録
        # ----------------------------------------------------

        for category in valid_categories:

            category_articles[category].append({
                "title": data.get(
                    "title",
                    article_path.stem
                ),
                "categories": article_categories,
                "filename": html_file.name,
            })

    # --------------------------------------------------------
    # カテゴリページを作る
    # --------------------------------------------------------

    for category in categories:

        articles = category_articles[category]

        category_html = create_category_page(
            category,
            articles
        )

        category_file = (
            category_output / f"{category}.html"
        )

        category_file.write_text(
            category_html,
            encoding="utf-8"
        )

        print(
            f"カテゴリページ作成: {category}.html"
        )

    # --------------------------------------------------------
    # index.html
    # --------------------------------------------------------

    create_index(categories)

    print()
    print("=====")
    print("サイト生成が完了しました！")
    print("=====")


# ============================================================
# 実行
# ============================================================

if __name__ == "__main__":
    main()