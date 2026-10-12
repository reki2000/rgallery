# rgallery

デモ、Webゲーム、「やる夫で学ぶ」を紹介する日英の静的ギャラリー。
各作品のディレクトリに置いた YAML と画像から `docs/` を生成します。
CI、サーバー側処理、フロントエンドフレームワークは不要です。

## ローカル確認

生成済みの **[docs/index.html](docs/index.html)** をブラウザで直接開けます。
英語版は **[docs/en/index.html](docs/en/index.html)** です。
リンク、言語切り替え、検索、画像拡大は `file://` でも動きます。
作品本体の外部リンクの閲覧にはネットワーク接続が必要です。登録した画像は作品ディレクトリからローカルにコピーされます。

Python 3.12 以降を使用します。

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/preview.py
```

日本語: <http://localhost:4173/> / 英語: <http://localhost:4173/en/>

ポートを変える場合は `python3 scripts/preview.py --port 8080`。
編集後は Ctrl+C で終了して再実行してください。
この制作環境ではソケットと Chrome 起動が制限されているため、実ブラウザでの見た目の検証は未実施です。

## 作品追加

`projects/<作品ID>/` を追加します。作品IDは英小文字・数字・ハイフンです。
その中に `project.yaml` と画像を置きます。中央の作品リストへの登録は不要です。

```text
projects/
  my-project/
    project.yaml
    overview.webp
    closeup.webp
```

```yaml
order: 150  # 任意。小さい順。同値はディレクトリ名順。省略時は100。
title:
  ja: 作品の名前
  en: Project name
summary:
  ja: 作品の簡単な紹介。
  en: A short introduction to the project.
tags: [demo]  # game / demo / text。複数指定も可。
technology: [JavaScript, WebGL]  # 任意
url: https://example.com/  # 任意。未公開作品は省略可
repository: https://github.com/owner/repo  # 任意
note:  # 任意。注意や作品の対応言語など
  ja: ブラウザで動きます。
  en: Runs in your browser.
screenshots:
  - src: overview.webp  # このディレクトリからの相対パス
    caption:
      ja: 全体の画面
      en: Overview
  - src: closeup.webp
    caption:
      ja: 拡大表示
      en: Close-up
```

画像は `.png` / `.jpg` / `.jpeg` / `.webp` / `.avif`。
縦長のスマホ画面にも対応します。画像なしは `screenshots: []`。
外部 HTTPS 画像も使えますが、作品ディレクトリに画像を保存する運用を推奨します。
外部 URL は HTTPS が必要です。公開URLとリポジトリがない作品も紹介として登録できます。紹介文とキャプションは日英両方を必須にしています。
一覧ではメイン1枚とサブ最大4枚を表示します。画像を押すと同じページで拡大でき、同じ作品の全画像を順に閲覧できます。詳細ページは生成しません。

```sh
python3 scripts/build.py --check  # YAMLと画像パスの検証
python3 scripts/build.py          # docs/を全生成
python3 scripts/check.py          # 生成物の内部リンクと構造の検証
```

`docs/` はビルドで置き換わる生成物です。編集は `projects/`、`static/`、`site.yaml` で行います。
`site.yaml` の `url` を変更すれば canonical と sitemap に反映されます。

## GitHub Pages

ローカルでビルドした **`docs/` をソースと一緒にコミット**します。
GitHub の Settings → Pages で次を選びます。

- Source: **Deploy from a branch**
- Branch: **main**
- Folder: **/docs**

GitHub Actions のビルド設定は追加していません。
Pages 自体の公開処理は GitHub が行います。
想定URL: <https://reki2000.github.io/rgallery/>

## レイアウト

- **PC:** 幅1120pxの中央配置。左にタグ・タイトル・短い紹介・リンク、右に主画像と補助画像。余白と細い罫線で作品を区切ります。
- **スマホ（640px以下）:** 画像を先に、その下に紹介。左右20pxの余白。タグと検索欄は縦に並びます。各作品にメイン画像と最大4枚のサムネイルを表示します。
- 日本語はルート、英語は `en/`。言語切り替えは同じカテゴリへ移動します。作品本体の言語を翻訳する機能ではありません。
- タグ別の一覧は静的HTML。JavaScriptなしでも閲覧できます。検索と拡大ダイアログだけを JavaScript で追加します。

## 作品の調査と残作業

GitHub接続から `reki2000` の公開リポジトリを調査し、READMEの作品説明・公開URL・スクリーンショットを基に登録しました。
`rgames` はREADMEとライセンスのみ、`reversi` は端末用なので現時点では含めていません。
Aquarium と FetLoom は、最新リポジトリの公開設定とREADMEから公開URL・スクリーンショットを登録しています。
シマエナガは提供された Claude Artifact のリンクを登録しました。内容の取得が制限されているため、詳細な説明と画像は未登録です。

以前取り込んだ作業用画像はすべて除外しました。公開サイトを実際にブラウザで表示して撮影し、確認した画像を登録しています。fnesemu、battle-sim、skating はギャラリー対象から除外しています。

参考: <https://jsgroth.dev/blog/> と提供された英語・日本語のスクリーンショット。暗い背景、えんじ色から青緑へのヘッダー、明るい文字と青いリンク、英語本文のセリフ体を反映しています。ヘッダーは `rgallery`、GitHub リンク、モノトーンの `En / Jp` 言語切り替え。キャッチコピーと導入部分はありません。


## 公開サイトから7枚のスクリーンショットを撮影

手元の通常の端末で実行してください。この制作環境からのブラウザ起動はできません。
[Playwright](https://playwright.dev/docs/screenshots)で実際のChromiumを開きます。
作業ファイルや既存のPNGは流用しません。

初回の準備:

```sh
python3 -m pip install -r requirements-capture.txt
python3 -m playwright install chromium
```

全作品をまとめて撮影する場合（シェルが `projects/*` を展開した順）:

```sh
python3 scripts/capture.py projects/*
```

引数は basename（末尾のディレクトリ名）だけで作品を判定します。`projects/kinkakuji`、絶対パス、`kinkakuji` は同じ作品を選びます。`projects/*` はクォートせず指定してください。

ブラウザが開いたら、実際に操作し、撮影する場面で端末の Enter を押してください。
各作品は **PC 5枚 → スマホ 2枚**。7枚終わると、余計な確認なしで次の作品を自動で開きます。
初期表示の目安はPC 1440×900、スマホ用390×844。ウィンドウの端をドラッグして自由にリサイズでき、実際の表示サイズで撮影・記録します。OS・ブラウザの最小ウィンドウ幅によって初期サイズは変わる場合があります。スマホ用は狭い幅とタッチ操作を使うレスポンシブ表示で、固定サイズの端末エミュレーションではありません。各サイズの中では同じブラウザ状態を保ち、視点・操作・ページを変えて撮影できます。
作品に再生ボタンがある場合は再生してください。テキストサイトでは本文のページを開いたりスクロールしたりできます。

- **Enter**: 今の画面を撮影して次の1枚へ。
- **r 1200x800 → Enter**: ウィンドウのサイズを変更（幅×高さ）。ドラッグで枠を変更できない環境でも使えます。サイズ変更だけでは撮影せず、続けてEnterで撮影します。OSの制限で指定サイズにできない場合があるため、端末に実際の表示サイズも表示します。
- **r +10% / r -10% → Enter**: 現在の表示サイズを基準に、幅と高さを10%拡大／縮小。
- **r +w10% / r -w10% → Enter**: 幅だけを10%拡大／縮小。
- **r +h10% / r -h10% → Enter**: 高さだけを10%拡大／縮小。小数の割合も指定できます（例: `r +w2.5%`）。符号なしの `r 90%` は現在の幅と高さを90%にします。
- **s → Enter**: 撮影済みの画像を完了として保存し、次の作品へ。7枚未満でも取り込めます。
- **q → Enter / Ctrl+C**: 終了。途中の作品も1枚以上撮影していれば完了として保存し、取り込みコマンドを表示します。撮影0枚の作品は登録しません。

公開URL未登録の作品はスキップします。HTTPエラーやナビゲーション失敗も次の作品へ進みます。
Claude Artifactのアクセス制限やローディング画面が見えたら、その画面は撮らず `s` でスキップしてください。

指定した作品だけを、指定順で撮影することもできます:

```sh
python3 scripts/capture.py projects/kinkakuji projects/pianist projects/shift
python3 scripts/capture.py --list
```

撮影済みの画像と取得元URL・表示サイズ・ハッシュは `.captures/<作品ID>/<撮影日時>/` に保存します。各撮影直後に `manifest.json` も更新するため、7枚未満で終了しても取り込めます。
撮影段階では公開用画像に登録しません。画像を確認してから、終了時に表示される取り込みコマンドを実行します。

```sh
python3 scripts/import_captures.py .captures/kinkakuji/<撮影日時>
python3 scripts/build.py
python3 scripts/check.py
```

取り込み先は `projects/kinkakuji/screenshots/<撮影結果の識別子>/`。撮影回ごとに別のフォルダへ保存し、既存の画像を上書きしません。
画像ファイルが欠損していればその画像をスキップし、存在する画像だけを `project.yaml` の既存画像リストの末尾に追加し、`capture.json` に取得元を記録します。同じ撮影結果を再取り込みしても重複登録しません。
`manifest.json` が欠けている場合、または画像が1枚も残っていない場合は、作品のメタデータを変更せずスキップします。存在する画像のハッシュ不一致などはエラーとして扱います。
一覧には最初の5枚（メイン1枚＋サブ4枚）を表示します。拡大表示では作品ごとの全画像を閲覧できます。
キャプションは取り込み後に `project.yaml` で実際の場面に合わせて調整してください。

公開URL未登録の作品は、実際にホストしたURLを指定できます:

```sh
python3 scripts/capture.py aquarium --url https://example.com/aquarium/
```

CI用の撮影・ビルド設定は追加していません。

文字サイズは、現在のサイズを基準に約1.5倍へ拡大し、補助文字21.6px・本文27px・見出し41.4pxの3種類に統一しています。GitHubへのリンクはヘッダー・各作品ともアイコンで表示します。


## 画像の切り出しと軽量化

元のスクリーンショットは作品ディレクトリに保存し、ビルド時に表示用JPEGを生成します。
縦横比を保ったまま最大1280×1280pxに縮小し、品質82のプログレッシブJPEGで圧縮します。拡大はしません。
切り出す場合は、その画像の項目に元画像のピクセル座標を指定します。

```yaml
screenshots:
  - src: screenshots/session/desktop-1.png
    caption: {ja: ゲーム画面, en: Gameplay}
    crop: {x: 62, y: 302, width: 956, height: 520}
```

`crop` はローカルPNGに対応します。最初の画像がメイン、その後の4枚がサブです。
切り出しのない画像をサブに置けば画面全体も掲載できます。
元画像はそのまま残り、公開用 `docs/` には軽量化した表示用画像だけを出力します。
