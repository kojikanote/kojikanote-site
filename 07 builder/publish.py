from pathlib import Path
from datetime import datetime
import subprocess


# ============================================================
# フォルダ設定
# ============================================================

# publish.py が入っているフォルダ
BUILDER = Path(__file__).parent

# mainObsidian
BASE = BUILDER.parent

# Webサイト完成形
OUTPUT = BASE / "output"


# ============================================================
# Gitコマンド実行
# ============================================================

def run_git(command):
    result = subprocess.run(
        command,
        cwd=BASE,
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        print("Gitでエラーが発生しました。")
        print(result.stderr)
        raise SystemExit(1)

    return result.stdout.strip()


# ============================================================
# 公開処理
# ============================================================

print()
print("========================================")
print("  こじかノート 公開処理")
print("========================================")
print()

# outputフォルダが存在するか確認
if not OUTPUT.exists():
    print("エラー：outputフォルダが見つかりません。")
    raise SystemExit(1)


# ------------------------------------------------------------
# Gitの状態を確認
# ------------------------------------------------------------

print("変更を確認しています...")

status = run_git([
    "git",
    "status",
    "--short",
    "--",
    "output"
])

if not status:
    print()
    print("outputに変更はありません。")
    print("GitHubへのpushは行いません。")
    print()
    raise SystemExit(0)


# ------------------------------------------------------------
# 変更内容を表示
# ------------------------------------------------------------

print()
print("変更されたファイル：")
print(status)
print()


# ------------------------------------------------------------
# outputをGitに追加
# ------------------------------------------------------------

print("変更をGitに追加しています...")

run_git([
    "git",
    "add",
    "output"
])


# ------------------------------------------------------------
# 現在日時を取得
# ------------------------------------------------------------

now = datetime.now()

commit_time = now.strftime("%Y-%m-%d %H:%M")

commit_message = f"Website update: {commit_time}"


# ------------------------------------------------------------
# commit
# ------------------------------------------------------------

print()
print(f"commitしています：{commit_message}")

run_git([
    "git",
    "commit",
    "-m",
    commit_message
])


# ------------------------------------------------------------
# GitHubへpush
# ------------------------------------------------------------

print()
print("GitHubへpushしています...")

run_git([
    "git",
    "push"
])


# ------------------------------------------------------------
# 完了
# ------------------------------------------------------------

print()
print("========================================")
print("  公開処理が完了しました")
print("========================================")
print()
print(f"commit：{commit_message}")
print()
print("GitHubへのpushが完了しました。")
print("Cloudflare側で自動デプロイされます。")
print()