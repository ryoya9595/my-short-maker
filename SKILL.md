---
name: my-short-maker
description: 台本を入れるだけで、顔出しなしの縦型ショート動画（金運・風水・雑学・スピ・占いなど）を全自動生成する。AI音声ナレーション＋シーンごとのAI背景画像＋文節ごとの字幕＋冒頭サムネ（タイトルコール音声つき）を、Vrew不要・追加課金ゼロで作る。「ショート作って」「台本から動画」「faceless動画」「〇〇のショート量産」で発動。
---

# my-short-maker（台本→facelessショート動画 自動生成）

台本を渡すだけで、megさん型（台本→AI音声→背景ビジュアル）の縦型ショートを全自動で1本つくる。
**Claude自身は画像も音声も生成しない。** Claudeは①台本と指示文を書き、②無料の外部サービス（AI音声=gTTS／AI画像=Pollinations）とローカルツール（FFmpeg／Remotion）を呼び出すコードを実行するだけ。

## 作業工程
```
① Claudeが script.json を書く（字幕・強調ワード・背景プロンプト・カバー）
② generate.py が gTTS に発注 → AI音声(mp3)
   〃           Pollinations に発注 → AI背景画像(jpg)
③ ffprobe で尺測定 → 字幕タイミング算出 → app/public/faceless-plan.json
④ Remotion が背景+字幕+音声+ズームを合成 → MP4
```

## 前提（初回のみセットアップ / SETUP.md 参照）
- Node.js + npm（Remotion用。`app/` で `npm install`）
- Python 3 + gTTS（`pip3 install gtts`）
- FFmpeg（`ffmpeg`/`ffprobe` がPATHに）
- インターネット接続（gTTS・Pollinationsは外部サービス）

## 手順

### STEP 1: ヒアリング（台本が無ければ）
- テーマ／タイトル（例「〇〇すると運気が下がる習慣」）
- 各シーンのセリフ（数行）。無ければ「テーマだけくれれば台本を書く」
- ジャンルの雰囲気（金運・風水／占い／雑学 等）→ 背景トーンに反映
→ 台本が無ければ、この型で6〜8シーンの台本を作って提案する。

### STEP 2: 台本を script.json に書く（パッケージ直下）
- `text` = 画面字幕（＝音声にもなる。1シーン1〜2文）
- `emph` = 金色ハイライトする強調ワード（textに含まれる部分文字列）
- `img` = そのシーンのAI背景プロンプト（英語・内容一致・人物/文字なし）
- `img_style` = 全シーン共通の背景トーン（ジャンルで変える）
- `cover` = 冒頭サムネ（`img`明るい画／`lines`色分けタイトル／`say`タイトルコール音声／`stroke`濃い外フチ）
- `speed` = 話速（gTTSは1.5前後推奨）／`engine` = gtts（自然）or say（macオフライン）

### STEP 3: 生成（音声＋背景＋尺）
```bash
python3 scripts/generate.py
```
背景生成は1枚10〜30秒。シーン数が多いと2分超→バックグラウンド実行で完了を待つ。

### STEP 4: レンダリング
```bash
cd app && npx remotion render src/index.ts FacelessShort ../output/<出力名>.mp4
```

### STEP 5: 目視チェック（必ず）
```bash
ffmpeg -y -ss 2 -i output/<出力名>.mp4 -frames:v 1 output/_check.png
```
→ 画像を確認。①字幕が読める（背景と被って潰れてない）②強調ワードが金色③タイトルバナー等の余計なUIが無い④背景がシーン内容と合ってる⑤総尺~60秒以内。

### STEP 6: 完了報告
- 完成パス `output/<出力名>.mp4`・尺・シーン数を報告。
- 次アクション: 🔁台本/背景微調整 / 🔊音声を有料TTSに格上げ / 🎬別テーマで量産。

## 育成：使う人の「理想の型」に寄せていく（settings.json）⭐
2層構造。今回の動画形式は"土台"で、フィードバックで各人の理想に育てる。
- **`settings.json`** = その人の理想の土台（声・BGM・フォント・色・背景トーン・話速）。**全動画に効く**。
- **`script.json`** = 1本ごとの台本。settingsより優先で個別上書き可。

**フィードバック運用**：要望が来たら `settings.json` の該当項目を書き換える → 次から全動画に反映。
- 話速→`speed` ／ 強調色→`style.emph_color` ／ フォント→`style.caption_font` ／ 字幕・カバーのフチ→`style.caption_stroke`/`style.cover_stroke` ／ 背景トーン→`img_style`
- BGM→mp3を `app/public/bgm/` に置き `bgm.file`(例 `bgm/calm.mp3`)＋`bgm.volume`(0.05〜0.12)
- 声色→`voice`（gTTSは日本語1声。本当に変えるなら有料TTSにengine差し替え）

## デザイン規約（このスキルの完成形＝土台。崩さない）
- **字幕の改行**: 文節（意味のまとまり）ごとに1行。**理想2行・最大3行**。長い行はフォント自動縮小で画面幅に収める。
- **画面上に「、」「。」を出さない**（台本には書いてOK＝音声のTTSには残す。テロップから消す）。「！？」は残す。
- 強調語・【】括弧は改行で割らない。字幕＝白文字＋黒フチ＋強調ワード金色。
- **常時タイトルバナー（ピル）・進捗バーは付けない**。
- 冒頭カバー＝明るい画＋でっかい2色タイトル＋タイトルコール音声。文字の外フチは濃い色（白フチNG＝見づらい）。

## 品質アップ（必要に応じて提案）
- 音声: gTTS(無料) → VOICEVOX(無料/要アプリ:port50021) → ElevenLabs等(有料・より自然)。
- 背景: Pollinations(無料) → Midjourney/Flux Pro/DALL-E等(有料・高品質/安定)。発注先を差し替えるだけ。
- BGM/効果音: Remotionで重ねられる（`app/src/FacelessShort.tsx`に追加）。

## 注意
- Pollinationsは無料公共サービス。混雑で遅い/たまに変な絵→seed変更で再生成。クライアント納品は有料画像推奨。
- gTTSはネット必須。オフライン時は engine=say（macのみ・棒読み）。
- 量産は `title`/`scenes` を変えて STEP2〜6 を繰り返すだけ。
