# Scheduled task 登録用プロンプト

以下の本文をChatGPT WebのScheduled taskに登録する。

---

GitHubプラグインとWeb検索を使い、経済ニュースダイジェストを1号発行してください。PC、ローカルファイル、ローカルshellは使用しません。

対象リポジトリは `ksoma105/market-news`、対象branchは `main` です。最初にGitHubプラグインで `main` の同一commitをrefとして `AGENTS.md` と `AUTOMATION.md` を取得し、両ファイルの指示を完全に読んで厳守してください。対象号がすでに発行済みなら何も変更せず終了してください。

記事に使うURLはWeb検索後に必ず実際に開き、公開日時と主要事実を確認してください。検索スニペットだけで記事を書かず、URL、記事名、数値を推測で作らないでください。

完成した旧号アーカイブ、`docs/index.html`、`data/seen.json`、`data/history.json` は、GitHubプラグインのblob/tree/commit/ref操作で単一commitにまとめ、forceを使わず `main` をfast-forward更新してください。ファイル単位の複数commit、PR、別branchは作らないでください。

成功時は号ID、記事数、commit SHA、公開URLを報告してください。検証失敗や競合時はリポジトリを部分更新せず、理由を報告してください。

---

## スケジュール

- タイムゾーン: `Asia/Tokyo`
- cron: `0 6,12,22 * * *`
- 表示名: `market-news-digest`
