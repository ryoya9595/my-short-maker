# my-short-maker セットアップ（初回のみ）

台本→顔出しなし縦型ショート動画を全自動生成するスキル。
**追加課金ゼロ・APIキー不要**（AI音声=gTTS／AI画像=Pollinations はどちらも無料の外部サービス）。
インターネット接続が必要。

## 必要なもの
| ツール | 用途 | 確認コマンド | 入れ方 |
|---|---|---|---|
| Node.js + npm | 動画合成(Remotion) | `node -v` / `npm -v` | https://nodejs.org （LTS） |
| Python 3 | 生成スクリプト | `python3 --version` | https://python.org （macは標準搭載） |
| FFmpeg | 音声処理・尺測定 | `ffmpeg -version` | Mac: `brew install ffmpeg` ／ Win: https://ffmpeg.org |
| gTTS | AI音声 | `python3 -c "import gtts"` | `pip3 install gtts` |

## セットアップ手順
```bash
# 1) このフォルダに移動
cd my-short-maker

# 2) Python: AI音声ライブラリ
pip3 install gtts

# 3) Remotion(動画合成)の依存をインストール
cd app && npm install && cd ..
```

## 使い方（1本作る）
```bash
# 1) 台本を書く：script.json を編集（サンプルが入っている）

# 2) 音声＋背景を生成
python3 scripts/generate.py

# 3) 動画を書き出し
cd app && npx remotion render src/index.ts FacelessShort ../output/short.mp4 && cd ..

# 完成： output/short.mp4
```

## トラブル時
- **背景が遅い/失敗**: Pollinationsが混雑中。時間をおく or `script.json` の背景プロンプト/seedを調整。失敗シーンは背景なし（グラデ）でも動く。
- **音声が出ない**: ネット未接続 or gTTS未インストール。`pip3 install gtts`。オフラインでmac なら `script.json` の `"engine": "say"`。
- **`remotion` が無い**: `cd app && npm install` を実行。
- **`ffprobe`/`ffmpeg` not found**: FFmpegをインストールしPATHを通す。

## 品質を上げたいとき（任意・有料）
- 音声をより自然に: VOICEVOX（無料/要アプリ）や ElevenLabs（有料）。
- 背景を高品質・安定に: Midjourney / Flux Pro / DALL-E 等（有料）。
- いずれも `scripts/generate.py` の該当関数（`synth` / `fetch_bg`）の発注先を差し替えるだけ。
