# 共通サポートページ

本リポジトリは https://arakiyuuta0314-sketch.github.io/ に配置する、iPhoneアプリ共通のサポート窓口です。

## 部品化
- `apps.json`：アプリ名、説明、保存・移行・購入復元の説明をまとめて管理。
- `scripts/build.py`：アプリ一覧とFAQを含む静的 `index.html` を再生成。
- `scripts/test_support.py`：リンク・データ妥当性・HTML文字エスケープ・広告認証ファイル保持を自動検証。
- `app-ads.txt`：Google AdMob向け公開認証。生成スクリプトによって書き換えない。

### アプリ追加時
1. 対象アプリのソースとリリース仕様を実際に確認する。機能を推測して説明しない。
2. `apps.json` の `apps` に独立したIDと日本語・英語の説明を追加する。
3. `python scripts/build.py`、`python -m unittest discover -s scripts -p test_support.py -v` を実行する。
4. `git diff --check`、`git diff -- app-ads.txt` で広告認証を無変更のまま維持できているか確認する。
5. 承認済みの更新をコミット・公開後に、HTTP 200、ページ本文、広告認証ファイルを確認する。

問い合わせメール：yuta.room.info@gmail.com

プライバシーポリシーは https://arakiyuuta0314-sketch.github.io/app-legal-pages/privacy/ に集約済み。アプリ別の取り扱いを先に追記してから案内する。

**注意**：このページは問い合わせの入口であり、App Store Connectのデータ収集申告やAdMob設定を代行するものではない。公開前に各アプリの実態と内容を照合する。
