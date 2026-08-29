# 経済ニュースダイジェスト

個人投資家向けの経済ニュースダイジェスト（日本・米国・世界）を、1日3回（JST 06:00 / 12:00 / 22:00）自動更新する静的Webサイトです。

## 公開URL

https://news.butterfalcon.com

## 自動発行の構成

ChatGPT WebのScheduled taskが、Web検索とGitHubプラグインを使って直接リポジトリを更新します。ローカルPC、Claude Code Routine、常時起動プロセスは不要です。

処理の流れは次の通りです。

1. GitHubの `main` から `AGENTS.md` と `AUTOMATION.md` を読む
2. 72時間以内のニュースを検索・検証する
3. 重複を除いて2〜7件を選ぶ
4. 最新号、旧号アーカイブ、重複台帳、発行履歴を生成する
5. 4ファイルを単一commitにして `main` をfast-forward更新する
6. GitHub Pagesが自動反映する

## Web Scheduled taskのセットアップ

### 1. GitHubを接続する

ChatGPT Webの設定からGitHubプラグインを接続し、`ksoma105/market-news` へのread/writeアクセスを許可します。

定期実行は途中で確認を求められないため、GitHubプラグインの権限設定で、blob/tree/commitの作成と `main` refのfast-forward更新が自動実行できることを確認してください。初回の通常チャットでテストし、書込み確認が出る場合は、対象を確認した上でGitHubプラグインの権限を調整します。

### 2. 通常チャットでテストする

Scheduled taskを有効にする前に、`SCHEDULE_PROMPT.md` の本文を通常のWebチャットで実行します。

確認項目:

- GitHubから `AGENTS.md` と `AUTOMATION.md` を読める
- Web検索で記事URLを開ける
- 4ファイルが1コミットで更新される
- `main` へのforce updateや別branch作成がない
- 公開サイトに新号が反映される

テスト実行も実際に1号を発行します。同じ号IDは再発行されないため、成功後に同じ時間枠でもう一度実行しても変更は発生しません。

### 3. Scheduled taskを登録する

ChatGPT WebのScheduledからスタンドアロンタスクを作り、`SCHEDULE_PROMPT.md` の本文を登録します。

- 表示名: `market-news-digest`
- タイムゾーン: `Asia/Tokyo`
- スケジュール: 毎日 06:00 / 12:00 / 22:00
- cron指定が使える場合: `0 6,12,22 * * *`
- 必要なツール: GitHubプラグイン、Web検索

Web Scheduled taskはローカルフォルダを保持しないため、手順と状態はすべてGitHubに置いています。

## ディレクトリ構成

```text
market-news/
├── AGENTS.md                       # Codex共通規約
├── AUTOMATION.md                   # Web自動発行の完全な手順
├── SCHEDULE_PROMPT.md              # Scheduled task登録用プロンプト
├── CLAUDE.md                       # 旧Claude Code向け規約（移行履歴）
├── README.md
├── docs/
│   ├── index.html                  # 最新号
│   ├── archive/                    # 過去号
│   └── assets/style.css
└── data/
    ├── seen.json                   # 直近72時間の重複排除台帳
    └── history.json                # 発行履歴
```

## 号IDとコミット規約

- 号ID: `YYYY-MM-DD-HHmm`（JSTの定時枠、分は `00`）
- コミット: `digest: <号ID>`
- 1号につき1コミット
- `main` へのfast-forward更新のみ

## 運用監視

初回数回はScheduledの実行履歴と公開サイトを確認してください。失敗時は部分更新せず、Scheduledの実行結果に失敗段階が記録される設計です。
