# ショート動画半自動作成スキル（my-short-maker）

台本を入れるだけで、**顔出しなしの縦型ショート動画**を半自動で作る Claude Code スキルです。
AI音声ナレーション・シーンごとのAI背景・字幕・冒頭サムネまで自動。**追加課金ゼロ・APIキー不要**。

🎬 **解説ページ:** https://ryoya9595.github.io/my-short-maker/

---

## 仕組み（Claudeは絵を描かない。発注する）

Claude 自身は画像も音声も生成しません。台本と指示文を書き、**無料の外部サービス**と**ローカルツール**に“発注”するだけ。だから $0 で回ります。

```
① 台本づくり（Claude）  … 字幕・強調ワード・背景プロンプト・サムネ
② AI音声  gTTS         … セリフを自然なナレーションに（無料・キー不要）
③ AI背景  Pollinations … シーンに合ったAI画像を生成（無料・キー不要）
④ 合成    FFmpeg+Remotion … 背景+字幕+音声+ズームを縦型9:16のMP4に
```

## 必要なもの
Node.js / Python 3 / FFmpeg ＋ インターネット接続

## セットアップ（初回だけ）
```bash
pip3 install gtts
cd app && npm install && cd ..
```

## 使い方（1本つくる）
```bash
# 1) script.json に台本を書く（テーマとセリフだけでOK）
# 2) 音声と背景を生成
python3 scripts/generate.py
# 3) 動画を書き出す
cd app && npx remotion render src/index.ts FacelessShort ../output/short.mp4
# → output/ に完成動画
```

## 自分好みに育てる
`settings.json` を書き換えると、**声・BGM・文字色・フォント・背景トーン・話速**を全動画にまとめて反映できます。1本ごとに設定し直す必要はありません。使うほど自分仕様に。

## 品質を上げたいとき（任意・有料）
- 音声：ElevenLabs 等（より自然）
- 背景：Midjourney / Flux Pro 等（高品質・安定）
- `scripts/generate.py` の発注先（`synth` / `fetch_bg`）を差し替えるだけ。

> ⚠️ Pollinations・gTTS は無料の公共サービスです（混雑で遅い/たまに崩れる/保証なし）。クライアント納品では有料の音声・画像への差し替えを推奨します。

くわしくは [`SETUP.md`](SETUP.md) / [`SKILL.md`](SKILL.md) を参照。
