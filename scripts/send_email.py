"""每次仓库被更新（push 到 main）后，把本次新增/修改的论文 Markdown 内容渲染成 HTML 邮件发送。

所有敏感配置通过环境变量（GitHub Actions Secrets）注入，不写入仓库。
"""

import datetime
import os
import smtplib
import subprocess
import sys
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

try:
    import markdown as md
except ImportError:
    md = None

SENDER = os.environ.get("SENDER")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER = os.environ.get("RECEIVER")
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
BEFORE_SHA = os.environ.get("BEFORE_SHA", "")
AFTER_SHA = os.environ.get("AFTER_SHA", "HEAD")
FORCE_LATEST = os.environ.get("FORCE_LATEST", "") not in ("", "0", "false", "False")

ZERO_SHA = "0000000000000000000000000000000000000000"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


def is_content_md(path):
    p = path.lower()
    return (
        p.endswith(".md")
        and not p.endswith("readme.md")
        and not path.startswith(".github/")
    )


def get_changed_files():
    """返回本次 push 中新增/修改的论文 Markdown 文件列表。"""
    if BEFORE_SHA and BEFORE_SHA != ZERO_SHA:
        out = run(["git", "diff", "--name-only", BEFORE_SHA, AFTER_SHA])
    else:
        out = run(["git", "show", "--name-only", "--pretty=format:", AFTER_SHA])

    seen, result = set(), []
    for f in out.splitlines():
        f = f.strip()
        if f and is_content_md(f) and f not in seen and os.path.exists(f):
            seen.add(f)
            result.append(f)
    return result


def get_latest_content_md():
    """兜底：在所有受版本控制的论文 Markdown 中，挑选最近一次提交修改的那个。"""
    tracked = run(["git", "ls-files", "*.md"]).splitlines()
    candidates = [f for f in tracked if is_content_md(f) and os.path.exists(f)]
    if not candidates:
        return []
    candidates.sort(
        key=lambda f: run(["git", "log", "-1", "--format=%ct", "--", f]) or "0",
        reverse=True,
    )
    return [candidates[0]]


def render_markdown(text):
    if md:
        return md.markdown(text, extensions=["tables", "fenced_code", "toc"])
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<pre>{escaped}</pre>"


def build_html(files, date_str):
    sections = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            sections.append(
                f'<h2 style="border-bottom:1px solid #eee;padding-bottom:6px;">'
                f"📄 {os.path.basename(f)}</h2>\n{render_markdown(fh.read())}"
            )
    body = "\n<hr style='margin:24px 0;'/>\n".join(sections)
    return (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;'
        'max-width:820px;margin:0 auto;color:#24292f;line-height:1.6;">'
        f"<p>PaperDaily 仓库已更新（{date_str}），本次更新内容如下：</p>\n{body}\n"
        '<p style="color:#8b949e;font-size:12px;margin-top:32px;">'
        "本邮件由 GitHub Actions 自动发送。</p></div>"
    )


def send(subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr(("PaperDaily", SENDER))
    msg["To"] = RECEIVER
    msg.attach(MIMEText(html, "html", "utf-8"))

    receivers = [r.strip() for r in RECEIVER.split(",") if r.strip()]
    if SMTP_PORT == 465:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
    else:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.starttls()
    try:
        server.login(SENDER, SENDER_PASSWORD)
        server.sendmail(SENDER, receivers, msg.as_string())
    finally:
        server.quit()


def main():
    missing = [
        k
        for k in ("SENDER", "SENDER_PASSWORD", "RECEIVER", "SMTP_SERVER")
        if not os.environ.get(k)
    ]
    if missing:
        print(f"缺少必要的 Secrets: {missing}", file=sys.stderr)
        sys.exit(1)

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    files = get_changed_files()

    if not files and FORCE_LATEST:
        files = get_latest_content_md()
        if not files:
            send(
                f"[PaperDaily] 邮件配置测试 {date_str}",
                "<p>✅ SMTP 配置成功！仓库里暂时还没有论文内容文件，"
                "等 Cursor 自动更新后即可收到每日论文邮件。</p>",
            )
            print("仓库暂无论文内容，已发送配置测试邮件。")
            return

    if not files:
        print("本次更新没有论文 Markdown 内容，跳过发送。")
        return

    html = build_html(files, date_str)
    send(f"[PaperDaily] 每日论文更新 {date_str}", html)
    print(f"已发送邮件到 {RECEIVER}，包含 {len(files)} 个文件。")


if __name__ == "__main__":
    main()
