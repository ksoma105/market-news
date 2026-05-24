# 経済ニュースダイジェスト

個人投資家向けの経済ニュースダイジェスト（日本・米国・世界）を、1日3回（JST 6:00 / 12:00 / 22:00）自動更新する静的Webサイトです。

## 公開URL

`https://<your-github-username>.github.io/<repo-name>/`

## セットアップ手順

### 1. リポジトリのpush

```bash
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

### 2. GitHub Pages の有効化

1. GitHub リポジトリの **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / Folder: `/docs` を選択して保存
4. 数十秒〜数分で公開される

### 3. Claude Code Routine の登録

1. Claude Code の Routine 作成画面を開く
2. このリポジトリを対象に指定し、書き込み（push）権限を付与
3. スケジュール設定:
   - Asia/Tokyo タイムゾーン: `0 6,12,22 * * *`
   - UTC指定の場合: `0 3,13,21 * * *`
4. プロンプト: `ROUTINE.md の手順に従って1号を発行してください`

> **注意**: Routineには1日あたりの実行回数上限があります（Pro: 5回/日、Max: 15回/日）。本件は3回/日のためPro枠でも収まりますが、他のRoutineと合算した上限に注意してください。

## ディレクトリ構成

```
market_news/
├── CLAUDE.md              # Claude Codeが起動時に自動で読むプロジェクト規約
├── ROUTINE.md             # Routineに渡すタスク本文（編集者への指示書）
├── README.md              # このファイル
├── docs/                  # GitHub Pages 公開ルート
│   ├── index.html         # 最新号
│   ├── archive/           # 過去号（<号ID>.html）
│   └── assets/
│       └── style.css      # 共通スタイル
└── data/
    ├── seen.json          # 重複排除の台帳（直近3日分）
    └── history.json       # 各号のメタ情報
```

## 号IDの形式

`YYYY-MM-DD-HHmm`（JST、24時間表記）  
例: `2026-05-24-0600`

## コミット規約

1号の発行ごとに1コミット。メッセージ形式: `digest: <号ID>`
