# Web版・経済ニュースダイジェスト自動発行手順

この手順は、PCやローカルファイルを使用しないChatGPT WebのScheduled task向けである。GitHubプラグインとWeb検索だけを使い、`ksoma105/market-news` の `main` を更新する。

## 成功条件

- JSTの対象スケジュール枠について1号だけ発行する。
- `docs/index.html`、旧号アーカイブ、`data/seen.json`、`data/history.json` を整合させる。
- 全変更を `digest: <号ID>` という1コミットで `main` にfast-forward反映する。
- 掲載したすべての情報を、実際に開いた出典で確認する。

## 1. 対象号を決める

1. 現在時刻をAsia/Tokyoで判断する。
2. 現在以前で最も新しい定時枠（06:00 / 12:00 / 22:00）を対象にする。00:00〜05:59は前日の22:00枠とする。
3. 号IDを `YYYY-MM-DD-HHmm` とし、分は必ず `00` にする。
4. `docs/index.html` がすでに同じ号IDなら、成功済みとして何も変更せず終了する。

## 2. GitHubの一貫したスナップショットを読む

GitHubプラグインで次を行う。

1. `GET https://api.github.com/repos/ksoma105/market-news/branches/main` 相当の読取で、`main` の先端コミットSHAを取得し、`parent_sha` とする。
2. `GET https://api.github.com/repos/ksoma105/market-news/git/commits/<parent_sha>` 相当の読取で、親コミットのtree SHAを取得し、`base_tree_sha` とする。
3. 必ず `ref=parent_sha` を指定して次のファイルを読む。途中でデフォルトブランチを読み直してスナップショットを混在させない。
   - `AGENTS.md`
   - `AUTOMATION.md`
   - `docs/index.html`
   - `data/seen.json`
   - `data/history.json`
4. JSONが解析できない、indexから旧号IDを一意に取得できない、または必要ファイルがない場合は更新せず終了し、エラーを報告する。

## 3. 掲載候補を調査する

発行時刻から遡って72時間以内に公開された記事を調べる。主な調査対象はWSJ、CNN、The Economist、Financial Times、Reuters、Bloomberg、BBC、Newsweek、日本経済新聞とし、加えて中央銀行、政府統計、規制当局、取引所、企業IRなどの一次情報を優先する。

各候補について以下を満たすこと。

- 検索結果ページではなく記事URLまたは一次情報ページを実際に開く。
- ページ上で公開日時、出来事、主要数値を確認する。
- URLが開けない記事、公開日時を確認できない記事、72時間より古い記事は採用しない。
- URLパスや記事タイトルを推測して作らない。
- 市場価格や指数値は、その値の基準日時と出典を確認する。
- 重要な政策、企業業績、相場変動は一次情報または独立した2出典以上で照合する。
- 有料記事で本文を確認できない場合、スニペットにない事実を補完しない。

## 4. 重複を除き記事を選ぶ

1. `seen.json` から発行時刻より72時間以上前の項目を取り除く。
2. URL一致だけでなく、実質的に同じ出来事や軽微な続報も重複として除外する。
3. 株式、為替、コモディティ、マクロ政策、地政学、産業トレンドから重要な5〜7件を選ぶ。
4. 新規の重要ニュースが少ない場合は、無理に埋めず2〜3件にする。
5. 各記事について、実在URLからscheme、`www.`、追跡query、末尾slashだけを除いた `url_normalized` と、短く安定した `topic_key` を作る。存在しないURLパスを追加してはならない。

## 5. ファイル内容を生成する

### 旧号アーカイブ

現在の `docs/index.html` を旧号IDの `docs/archive/<旧号ID>.html` として保存する。ただしアーカイブ階層でリンクが壊れないよう、次を変換する。

- `href="assets/style.css"` → `href="../assets/style.css"`
- `href="archive/<号ID>.html"` → `href="<号ID>.html"`

同名アーカイブがすでに存在する場合は上書きせず、内容が一致しなければ競合として終了する。

### 新しいindex

- 既存HTMLの構造とデザインを維持する。
- タイトル、日時、号ID、リード文、記事を新号に置き換える。
- 各記事は見出し、独自要約、実際に確認した出典リンクを含める。
- 過去号一覧の先頭に旧号への `archive/<旧号ID>.html` を重複なしで追加する。
- CSSは `href="assets/style.css"` のままにする。
- 末尾に既存と同等の投資助言免責を含める。

### seen.json

- 72時間以内の既存項目を残し、新号の掲載項目を追加する。
- 各項目に `url_normalized`、`title`、`topic_key`、`source`、`first_seen`、`issue` を含める。
- `first_seen` は対象枠のJST ISO 8601、`issue` は新号IDとする。
- 有効なJSONとして整形する。

### history.json

- 既存の `issues` 配列を保持する。
- 旧号のレコードが存在する場合、その `html_path` を `docs/archive/<旧号ID>.html` に直す。
- 新号IDがなければ、新号の `issue_id`、`published_at`、`topic_count`、`html_path: docs/index.html`、`topics` を追加する。
- 同じ `issue_id` を重複させない。
- 有効なJSONとして整形する。

## 6. コミット前検証

次をすべて確認する。1つでも失敗したらGitHubへ書き込まない。

- 新indexの号IDが対象号と一致する。
- 記事数が2〜7件である。
- 全記事に少なくとも1つの確認済み出典リンクがある。
- `seen.json` と `history.json` が解析可能で、新号IDを含む。
- indexの全アーカイブリンクに対応するファイルが、既存treeまたは今回の更新後treeに存在する。
- 新アーカイブのCSSと過去号リンクがアーカイブ階層向け相対パスになっている。
- indexとアーカイブの両方に投資助言免責がある。
- 新規URLを推測で生成していない。

## 7. 4ファイルを1コミットで反映する

GitHubのGit data操作を使い、Contents APIでファイルごとの複数コミットを作らない。

1. 次の完成内容からUTF-8 blobを4つ作成する。
   - `docs/archive/<旧号ID>.html`
   - `docs/index.html`
   - `data/seen.json`
   - `data/history.json`
2. `base_tree_sha` を親treeとして、各blobを `mode: 100644`、`type: blob` で配置したtreeを作る。
3. `parent_sha` を唯一の親、作成したtreeをtree、`digest: <新号ID>` をmessageとしてcommitを作る。
4. `main` の先端SHAをもう一度読む。`parent_sha` から変わっていたらrefを更新せず、最新状態から全手順をやり直す。
5. 変わっていなければ、forceを使わず `main` refを新commitへ更新する。
6. PR、別ブランチ、force updateは使用しない。

## 8. 実行結果を報告する

成功時は号ID、記事数、commit SHA、`https://news.butterfalcon.com` を簡潔に報告する。重要ニュース不足で件数を減らした場合はその旨も書く。失敗時はGitHubを部分更新せず、失敗した段階と理由を報告する。
