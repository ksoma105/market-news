# Scheduled task 登録用プロンプト

以下の本文をChatGPT WebのScheduled taskに登録する。

---

GitHubプラグインとWeb検索を使い、経済ニュースダイジェストを1号発行してください。PC、ローカルファイル、ローカルshellは使用しません。

対象リポジトリは `ksoma105/market-news`、対象branchは `main` です。最初にGitHubプラグインで `main` の同一commitをrefとして `AGENTS.md`、`AUTOMATION.md`、`NARRATION.md` を取得し、各ファイルの指示を完全に読んで厳守してください。対象号がすでに発行済みなら何も変更せず終了してください。

記事に使うURLはWeb検索後に必ず実際に開き、公開日時と主要事実を確認してください。検索スニペットだけで記事を書かず、URL、記事名、数値を推測で作らないでください。

毎号、確認済みの記事をもとに日本語の音声向け原稿を `docs/narration/<号ID>.txt` に作成してください。文書をそのまま読む形式ではなく、短い文と自然なつなぎで聞き取りやすいニュース解説にしてください。全ニュースの重要な事実、影響が考えられる業種、注目点・リスクを保ち、数値の単位と時点、不確実性を正確に伝えてください。URL、HTML、箇条書き記号は原稿に含めません。

完成した旧号アーカイブ、`docs/index.html`、`data/seen.json`、`data/history.json`、新号の音声向け原稿は、GitHubプラグインのblob/tree/commit/ref操作で単一commitにまとめ、forceを使わず `main` をfast-forward更新してください。ファイル単位の複数commit、PR、別branchは作らないでください。

成功時は号ID、記事数、commit SHA、公開URL、原稿URL、音声生成の実際の状態を報告してください。現在ElevenLabsのAPI接続と音声生成処理は未設定なので、原稿作成だけで音声生成済みと報告しないでください。検証失敗や競合時はリポジトリを部分更新せず、理由を報告してください。

---

## スケジュール

- タイムゾーン: `Asia/Tokyo`
- 実行: 毎日06:05・12:05・22:05（号の表示時刻は06:00・12:00・22:00）
- 表示名: `market-news-digest`
