from pathlib import Path
import markdown
import shutil

# ===== フォルダ設定 =====

BASE = Path(__file__).parent.parent

ARTICLES = BASE / "03 Articles" 
OUTPUT = BASE / "output"
CSS = BASE / "output" / "style.css"
# outputフォルダがなければ作る
OUTPUT.mkdir(exist_ok=True)

def add_sections(html):
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

    # 最後に開いているsectionを閉じるための変数
    current_section = None

    lines = html.splitlines()
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


# Markdown → HTML
for ARTICLE in ARTICLES.glob("*.md"):
    print(f"変換中 : {ARTICLE.name}")
    # Markdownを読む
    md_text = ARTICLE.read_text(encoding="utf-8")
    # HTMLへ変換
    body = markdown.markdown(
        md_text,
        extensions=[
            "extra",
            "tables",
            "fenced_code",
            "nl2br",
         ]
    )

    # セクションを追加
    body = add_sections(body)
    title = ARTICLE.stem
    # HTML全体
    html = f"""<!DOCTYPE html>
    <html lang="ja">

    <head>

    <meta charset="UTF-8">

    <meta name="viewport"
         content="width=device-width, initial-scale=1">

    <title>{title}</title>

    <link rel="stylesheet"
         href="assets/style.css">

    </head>

    <body>

    <header>

    <h1><img src="assets/logo.svg" alt="こじかノート"> こじかノート</h1>

    </header>

    <main>

    <article>

    {body}

    </article>

    </main>

    <footer>

    <p>© 2026 こじかノート</p>

    </footer>

    </body>

    </html>
    """
    # 保存
    html_file = OUTPUT / f"{ARTICLE.stem}.html"

    html_file.write_text(html, encoding="utf-8")
    print(f"{ARTICLE.name} を変換しました")

# ===== index.htmlを作成 =====

index_html = """<!DOCTYPE html>
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

</main>

<footer>

<p>© 2026 こじかノート</p>

</footer>

</body>

</html>
"""

index_file = OUTPUT / "index.html"
index_file.write_text(index_html, encoding="utf-8")

print("index.htmlを作成しました")
print()
print("=====")
print("すべての記事のHTMLを生成しました!")
print("=====")