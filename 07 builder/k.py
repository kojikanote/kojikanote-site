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

    「関連資料」だけは <details> で折りたたむ。
    """

    sections = {
        "結論": "conclusion",
        "解説": "explanation",
        "関連資料": "references",
        "小児科医のコメント": "doctor-comment",
    }

    current_section = None
    current_is_references = False

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

                # すでにsection/detailsが開いていたら閉じる
                if current_section is not None:
                    if current_is_references:
                        result.append("</div>")
                        result.append("</details>")
                    else:
                        result.append("</section>")

                # CSS用のclass名
                class_name = sections[title]

                # --------------------------------
                # 関連資料だけ折りたたむ
                # --------------------------------
                if title == "関連資料":

                    result.append(
                        '<details class="references">'
                    )

                    result.append(
                        '<summary>関連資料</summary>'
                    )

                    result.append(
                        '<div class="references-content">'
                    )

                    current_is_references = True

                # --------------------------------
                # その他のセクション
                # --------------------------------
                else:

                    result.append(
                        f'<section class="{class_name}">'
                    )

                    # h2自体はそのまま残す
                    result.append(line)

                    current_is_references = False

                current_section = class_name

                continue

        # 普通の行はそのまま追加
        result.append(line)

    # 最後のsection/detailsを閉じる
    if current_section is not None:

        if current_is_references:
            result.append("</div>")
            result.append("</details>")
        else:
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
# ============================================================
# ObsidianリンクをHTMLリンクに変換
# ============================================================

def convert_obsidian_links(md_text, article_map):
    """
    本文中の [[記事名]] をHTMLリンクに変換する。
    """

    for title, filename in article_map.items():

        obsidian_link = f"[[{title}]]"

        html_link = (
            f'<a href="{html.escape(filename)}">'
            f'{html.escape(title)}'
            f'</a>'
        )

        md_text = md_text.replace(
            obsidian_link,
            html_link
        )

    return md_text


# ============================================================
# Markdown → HTML
# ============================================================

def markdown_to_html(md_text, article_map):

    # --------------------------------------------------------
    # ObsidianリンクをHTMLリンクに変換
    # --------------------------------------------------------

    md_text = convert_obsidian_links(
        md_text,
        article_map
    )

    # --------------------------------------------------------
    # Markdown → HTML
    # --------------------------------------------------------

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
# 公開記事をすべて読み込む
# ============================================================

def load_articles():

    articles = []

    for article_path in ARTICLES.glob("*.md"):

        result = read_article(article_path)

        if result is None:
            continue

        data, md_body = result

        # statusを確認
        status = data.get("status")

        if status != "公開":
            continue

        title = data.get("title", article_path.stem)

        categories = data.get("categories", [])

        if not isinstance(categories, list):
            categories = [categories]

        related = data.get("related", [])

        if not isinstance(related, list):
            related = [related]

        articles.append({
            "path": article_path,
            "title": title,
            "categories": categories,
            "related": related,
            "data": data,
            "body": md_body,
            "filename": f"{article_path.stem}.html",
        })

    return articles

# ============================================================
# 関連記事を解析する
# ============================================================

def build_related_map(articles, article_map):
    """
    各記事のrelatedから関連記事を取得する。

    Obsidianの [[記事名]] を読み取り、
    記事タイトルをキーにして関連関係を作る。

    A → B と指定されていた場合、
    自動的に B → A も追加する。
    """

    related_map = {}

    # --------------------------------------------------------
    # まず、すべての記事に空の関連記事リストを作る
    # --------------------------------------------------------

    for article in articles:

        title = article["title"]

        related_map[title] = []

    # --------------------------------------------------------
    # Frontmatterのrelatedを読み込む
    # --------------------------------------------------------

    for article in articles:

        title = article["title"]

        for related in article["related"]:

            # [[記事名]] → 記事名
            if isinstance(related, str):

                related_title = related.strip()

                if (
                    related_title.startswith("[[")
                    and related_title.endswith("]]")
                ):

                    related_title = related_title[2:-2].strip()

                else:

                    print(
                        f"  ⚠ relatedの形式が正しくありません: "
                        f"{title} → {related}"
                    )

                    continue

            else:

                continue

            # ------------------------------------------------
            # 公開記事として存在するか確認
            # ------------------------------------------------

            if related_title not in article_map:

                print(
                    f"  ⚠ 関連記事が見つかりません: "
                    f"{title} → {related_title}"
                )

                continue

            # ------------------------------------------------
            # 自分自身へのリンクは除外
            # ------------------------------------------------

            if related_title == title:
                continue

            # ------------------------------------------------
            # A → B を追加
            # ------------------------------------------------

            if related_title not in related_map[title]:

                related_map[title].append(
                    related_title
                )

            # ------------------------------------------------
            # B → A を自動追加
            # ------------------------------------------------

            if title not in related_map[related_title]:

                related_map[related_title].append(
                    title
                )

    return related_map

# ============================================================
# 記事HTMLを作る
# ============================================================

def create_article_html(
    article_path,
    data,
    body,
    related_articles,
    article_map
):
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
    # 関連記事
    # --------------------------------------------------------

    related_html = ""

    if related_articles:

        related_links = []

        for related_title in related_articles:

            related_filename = article_map[related_title]

            related_links.append(
                f'<li>'
                f'<a href="{html.escape(related_filename)}">'
                f'{html.escape(related_title)}'
                f'</a>'
                f'</li>'
            )

        related_html = f"""
<section class="related">
<h2>関連する記事</h2>
<ul>
{chr(10).join(related_links)}
</ul>
</section>
"""
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
<link rel="icon"
     type="image/svg+xml"
     href="assets/favicon.svg">
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

{related_html}

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
<link rel="icon"
     type="image/svg+xml"
     href="../assets/favicon.svg">
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
<link rel="icon"
     type="image/svg+xml"
     href="assets/favicon.svg">
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
    # 以前生成したHTMLを削除
    # --------------------------------------------------------

    print("以前のHTMLを削除しています...")

    for html_file in OUTPUT.glob("*.html"):
        html_file.unlink()
        print(f"  → {html_file.name} を削除")

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
    # 公開記事をすべて読み込む
    # --------------------------------------------------------

    articles = load_articles()

    print(f"公開記事数：{len(articles)}")
    print()
    # --------------------------------------------------------
    # 記事タイトルとHTMLファイル名の対応表
    # --------------------------------------------------------

    article_map = {}

    for article in articles:
        article_map[article["title"]] = article["filename"]

    # --------------------------------------------------------
    # 関連記事の関係を作る
    # --------------------------------------------------------

    related_map = build_related_map(
        articles,
        article_map
    )
    print("関連記事：")

    for title, related_titles in related_map.items():

        if related_titles:
            print(f"  {title}")
            for related_title in related_titles:
                print(f"    → {related_title}")

    print()

    # --------------------------------------------------------
    # categoryフォルダを作り直す
    # --------------------------------------------------------

    category_output = OUTPUT / "category"
    if category_output.exists(): 
        for html_file in category_output.glob("*.html"): 
            html_file.unlink()
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
        body = markdown_to_html(
            md_body,
            article_map
        )

        # ----------------------------------------------------
        # 記事HTMLを作る
        # ----------------------------------------------------

        article_html = create_article_html(
            article_path,
            data,
            body,
            related_map[data.get("title", article_path.stem)],
            article_map
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