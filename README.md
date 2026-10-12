# rgallery

[公開サイト](https://reki2000.github.io/rgallery/)

# 開発向け

デモ・Webゲーム・テキスト作品を紹介する、日本語／英語対応の静的ギャラリーテンプレートです。
作品ごとの YAML と画像から `docs/` に HTML を生成します。ローカルでビルドし、生成物を GitHub Pages に公開します。

## セットアップとローカル確認

Python 3.12 以降を使用します。

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/preview.py
```

- 日本語：<http://localhost:4173/>
- 英語：<http://localhost:4173/en/>

ポートは `python3 scripts/preview.py --port 8080` で変更できます。編集後はプレビューを終了して再起動してください。
生成済みの `docs/index.html` と `docs/en/index.html` はブラウザで直接開くこともできます。

## サイトの設定

`site.yaml` にサイト名、GitHubアカウント名、公開URL、リポジトリURLを設定します。

```yaml
name: My Gallery
author: YOUR_GITHUB_USERNAME
url: https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPOSITORY/
repository: https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY
```

`author` はフッターに、`repository` はヘッダーのGitHubリンクに、`url` は canonical と sitemap に使います。
スタイルは `static/style.css`、検索と画像拡大の処理は `static/site.js` で変更できます。

## 作品の追加

`projects/<作品ID>/` に `project.yaml` と画像を置きます。中央の一覧ファイルへの登録は不要です。
作品IDには英小文字・数字・ハイフンを使います。

```text
projects/
  my-project/
    project.yaml
    overview.png
    closeup.png
```

```yaml
order: 100  # 任意。小さい順。同値は作品ID順。省略時は100。
title:
  ja: 作品の名前
  en: Project name
summary:
  ja: 作品の簡単な紹介。
  en: A short introduction to the project.
tags: [demo]  # game / demo / text。複数指定可。
technology: [JavaScript, WebGL]  # 任意
url: https://example.com/demo/  # 任意
repository: https://github.com/owner/project  # 任意
note:  # 任意。対象年齢や対応言語など
  ja: 対象年齢：4歳～
  en: Ages 4+
screenshots:
  - src: overview.png  # 作品ディレクトリからの相対パス
    caption:
      ja: 全体の画面
      en: Overview
  - src: closeup.png
    caption:
      ja: 拡大表示
      en: Close-up
```

タイトル・紹介文・画像キャプションは日英の両方が必要です。`note` を指定する場合も両方を記載します。
公開URLとリポジトリは省略できます。画像なしの作品は `screenshots: []` とします。
外部リンクには HTTPS を使います。

画像は `.png` / `.jpg` / `.jpeg` / `.webp` / `.avif` に対応します。外部HTTPS画像も指定できますが、軽量化するにはローカル画像を使ってください。
最初の画像がメイン、次の4枚がサブです。それ以降の画像も拡大表示で閲覧できます。詳細ページは生成しません。

## 画像の切り出しと軽量化

ローカル画像は、ビルド時に縦横比を保って最大1280×1280pxへ縮小し、品質82のプログレッシブJPEGとして出力します。
一覧と拡大表示は同じJPEGを使います。元画像は変更せず、小さな画像は拡大しません。

画像を切り出す場合は、元画像のピクセル座標を `crop` に指定します。切り出しはローカルPNGに対応しています。

```yaml
screenshots:
  - src: overview.png
    caption: {ja: ゲーム画面, en: Gameplay}
    crop: {x: 60, y: 300, width: 960, height: 520}
```

メインをゲーム画面の切り出しにし、サブに画面全体を置くなど、YAMLの並び順で構成できます。

## 撮影と取り込み

撮影には Playwright と Chromium を使用します。

```sh
python3 -m pip install -r requirements-capture.txt
python3 -m playwright install chromium
python3 scripts/capture.py projects/*
```

引数は basename で作品を判定します。`projects/*` はクォートせず指定してください。
個別の作品を指定した順に開くこともできます。

```sh
python3 scripts/capture.py projects/my-project projects/another-project
python3 scripts/capture.py --list
```

各作品をブラウザで操作し、端末で Enter を押して撮影します。
PC5枚・スマホ用2枚を撮影すると、自動で次の作品へ進みます。
初期表示の目安はPC 1440×900、スマホ用390×844です。スマホ用はタッチ操作を有効にした狭いウィンドウで、固定サイズの端末エミュレーションではありません。

| 端末での入力 | 動作 |
| --- | --- |
| Enter | 現在の画面を撮影 |
| `r 1200x800` | 表示サイズを指定 |
| `r +10%` / `r -10%` | 現在の幅・高さを拡大／縮小 |
| `r +w10%` / `r -h10%` | 幅だけ拡大／高さだけ縮小 |
| `s` | 撮影済み画像を保存して次の作品へ |
| `q` / Ctrl+C | 撮影済み画像を保存して終了 |

リサイズでは小数も使えます。符号なしの `r 90%` は現在の幅・高さを90%にします。
OSの制約で指定サイズにならない場合は、端末に表示される実際のサイズを確認してください。

公開URLのない作品や読み込みに失敗した作品はスキップします。未登録の公開URLを指定する場合は、作品を1つだけ選びます。

```sh
python3 scripts/capture.py projects/my-project --url https://example.com/demo/
```

画像と manifest は `.captures/<作品ID>/<撮影日時>/` に保存します。撮影だけでは公開用の画像リストを変更しません。
画像を確認してから、終了時に表示される取り込みコマンドを実行してください。

```sh
python3 scripts/import_captures.py .captures/my-project/<撮影日時>
```

取り込みは既存画像の末尾へ追加します。撮影回ごとに保存先を分け、上書きや同じ撮影結果の重複登録を防ぎます。
欠損画像はスキップし、画像が全欠損の場合や manifest がない場合は登録を変更しません。ハッシュ不一致はエラーになります。
7枚未満で撮影を終了しても取り込めます。取り込み後はキャプションと画像の並び順を `project.yaml` で調整してください。

## ビルドと検証

```sh
python3 scripts/build.py --check  # YAMLと画像パスを検証
python3 scripts/build.py          # HTMLとJPEGを生成
python3 scripts/check.py          # 生成物のリンク・画像・構造を検証
```

`docs/` はビルドで置き換わります。編集は `projects/`、`static/`、`site.yaml`、`scripts/` で行ってください。
日本語はルート、英語は `en/` に生成します。タグ別の一覧も静的HTMLで閲覧できます。
検索・画像拡大にはJavaScriptを使用します。言語切り替えはギャラリーの表示言語を変更し、作品本体を翻訳するものではありません。

## GitHub Pagesへの公開

ローカルでビルド・検証した `docs/` を、ソースと一緒にコミットします。

```sh
python3 scripts/build.py
python3 scripts/check.py
git add docs projects static scripts site.yaml README.md requirements*.txt .gitignore
git commit -m "Update gallery"
git push
```

リポジトリの Settings → Pages で以下を選択します。

- Source：**Deploy from a branch**
- Branch：**main**
- Folder：**/docs**

CIでのビルドは不要です。GitHub Pagesがコミット済みの `docs/` を公開します。
