#!/usr/bin/env python3
"""Generate the public support homepage from one app registry. No remote calls."""
from __future__ import annotations
from html import escape
from pathlib import Path
from urllib.parse import quote, urlsplit
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "apps.json"
OUTPUT = ROOT / "index.html"


def validate_registry(data):
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        raise ValueError("unsupported apps.json schemaVersion")
    email = data.get("contactEmail")
    if not isinstance(email, str) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("invalid contact email")
    privacy_url = data.get("privacyPolicyUrl")
    p = urlsplit(privacy_url) if isinstance(privacy_url, str) else None
    if not p or p.scheme != "https" or not p.netloc or not p.path.startswith("/"):
        raise ValueError("invalid HTTPS privacy policy URL")
    apps = data.get("apps")
    if not isinstance(apps, list) or not apps:
        raise ValueError("apps must be non-empty")
    if len(apps) > 100:
        raise ValueError("too many apps")
    slugs = set()
    names = set()
    text_fields = ("name", "emoji", "descriptionJa", "descriptionEn", "saveJa", "saveEn",
                   "backupJa", "backupEn", "purchasesJa", "purchasesEn")
    for app in apps:
        if not isinstance(app, dict):
            raise ValueError("app entry must be an object")
        slug = app.get("id")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError("invalid app id: " + str(slug))
        if slug in slugs:
            raise ValueError("duplicate app id: " + slug)
        slugs.add(slug)
        for field in text_fields:
            value = app.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > 500:
                raise ValueError(f"{slug}: invalid field {field}")
        if app["name"] in names:
            raise ValueError("duplicate app name")
        names.add(app["name"])
    return data


def render(data):
    data = validate_registry(data)
    E = lambda value: escape(str(value), quote=True)
    privacy = E(data["privacyPolicyUrl"])
    email = E(data["contactEmail"])
    cards = []
    for app in data["apps"]:
        name, slug = E(app["name"]), E(app["id"])
        subject = quote(f"【{app['name']}】お問い合わせ", safe="")
        cards.append(f"""<article class="app-card" id="app-{slug}">
  <div class="app-title"><span class="app-icon" aria-hidden="true">{E(app["emoji"])}</span><div><h3>{name}</h3><p class="app-description">{E(app["descriptionJa"])}<span lang="en">{E(app["descriptionEn"])}</span></p></div></div>
  <details><summary>よくあるご質問 / Help &amp; FAQ</summary>
    <dl>
      <dt>保存されたデータはどこにありますか？ / Where is my data?</dt><dd>{E(app["saveJa"])}<span lang="en">{E(app["saveEn"])}</span></dd>
      <dt>アプリを削除・機種変更するときは？ / Backups &amp; migration</dt><dd>{E(app["backupJa"])}<span lang="en">{E(app["backupEn"])}</span></dd>
      <dt>広告削除を購入した場合は？ / Restore purchases</dt><dd>{E(app["purchasesJa"])}<span lang="en">{E(app["purchasesEn"])}</span></dd>
    </dl>
  </details>
  <div class="links"><a href="{privacy}">プライバシーポリシー <span lang="en">/ Privacy</span> ↗</a><a href="mailto:{email}?subject={subject}">このアプリについて問い合わせる ↗</a></div>
</article>""")
    cards_html = "\n".join(cards)
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="light">
<meta name="theme-color" content="#f5f9f7">
<meta name="description" content="iPhoneアプリ共通サポートページ。お問い合わせ、データ保存、バックアップ、広告削除とプライバシー情報。">
<title>アプリサポート / App Support</title>
<style>
:root{{--bg:#f5f9f7;--ink:#233c39;--muted:#697b78;--line:#dce9e3;--green:#226858;--card:#fff}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif}}
a{{color:var(--green);text-underline-offset:3px;overflow-wrap:anywhere}}a:hover{{color:#114a3c}}a:focus-visible,summary:focus-visible{{outline:3px solid #edb75e;outline-offset:3px}}
.wrap{{max-width:780px;margin:0 auto;padding:0 19px}}
header{{padding:44px 0 37px;background:linear-gradient(130deg,#e7f5ee,#fefaf0);border-bottom:1px solid #e1ece4}}
.eyebrow{{font-size:12px;font-weight:800;letter-spacing:.16em;color:#498071}}
h1{{font-size:clamp(28px,5vw,37px);margin:13px 0;letter-spacing:-.025em}}header p{{line-height:1.85;color:#56716b;margin:9px 0 0}}
main{{padding-top:27px!important;padding-bottom:56px!important}}.lead{{margin:0 0 19px;color:var(--muted);line-height:1.8}}
.app-list{{display:grid;gap:17px}}.app-card{{background:var(--card);border:1px solid var(--line);border-radius:19px;padding:24px;box-shadow:0 6px 22px #20534108}}
.app-title{{display:flex;gap:14px;align-items:flex-start}}.app-icon{{border-radius:14px;background:#eaf5ed;width:51px;height:51px;display:grid;place-items:center;flex:none;font-size:27px}}
h2{{font-size:18px;margin:26px 0 15px}}h3{{font-size:20px;margin:3px 0 7px}}.app-description{{color:var(--muted);font-size:14px;line-height:1.8;margin:0}}
span[lang=en]{{display:block;font-size:.92em;color:#81918f;line-height:1.65}}
details{{margin:19px 0 6px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}summary{{list-style-position:inside;cursor:pointer;color:var(--green);font-size:14px;padding:14px 0;font-weight:700}}
dl{{margin:0 0 17px}}dt{{font-weight:700;font-size:14px;margin:18px 0 6px}}dd{{margin:0;color:#647774;font-size:14px;line-height:1.8}}
.links{{display:flex;flex-wrap:wrap;gap:10px 25px;padding-top:14px}}.links a{{font-size:14px;font-weight:700}}
.help{{background:#edf5f1;border-radius:17px;padding:20px 23px;margin-top:26px}}.help h2{{margin:0 0 9px}}.help p{{font-size:14px;line-height:1.8;margin:8px 0;color:#59716a}}
footer{{border-top:1px solid var(--line);font-size:12px;color:#829490;padding:23px 0 31px}}
@media(max-width:500px){{header{{padding:31px 0 29px}}.app-card{{padding:19px}}.app-icon{{width:44px;height:44px;font-size:23px}}h3{{font-size:18px}}.links a{{line-height:1.6}}}}
</style>
</head>
<body>
<header><div class="wrap"><div class="eyebrow">APP SUPPORT / アプリサポート</div>
<h1>アプリのサポート窓口</h1>
<p>お問い合わせやアプリの使い方、プライバシー情報はこちらから。<br>
<span lang="en">Support and privacy information for our iPhone apps.</span></p></div></header>
<main class="wrap" id="main">
<p class="lead">アプリを選ぶと、データの保存方法やバックアップについて確認できます。<br>
<span lang="en">Choose an app below for details about local data, backups and purchases.</span></p>
<section aria-labelledby="apps-heading"><h2 id="apps-heading">サポート対象アプリ / Apps</h2>
<div class="app-list">
{cards_html}
</div></section>
<section class="help"><h2>共通のお問い合わせ / Contact</h2>
<p>不具合やご意見は、アプリ名、利用しているiPhone・iOSのバージョン、発生した操作を添えてご連絡ください。パスワード・決済情報などの機密情報は送らないでください。</p>
<p lang="en">For support, include your app name, device/iOS version, and steps to reproduce the issue. Do not email passwords or payment details.</p>
<p><a href="mailto:{email}">{email}</a></p>
<p><a href="{privacy}">共通プライバシーポリシー / Privacy Policy ↗</a></p>
</section>
</main>
<footer><div class="wrap">© 2026 App Support · English / 日本語</div></footer>
</body></html>
"""


def main():
    raw = json.loads(REGISTRY.read_text(encoding="utf-8"))
    page = render(raw)
    if len(page.encode("utf-8")) > 200_000:
        raise ValueError("generated HTML unusually large")
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Generated {OUTPUT}, {len(raw['apps'])} app cards")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        raise
