#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
my2-short-maker generator
台本(script.json) -> AI音声(gTTS) -> AI背景(Pollinations) -> 尺測定(ffprobe) -> app/public/faceless-plan.json
Claude自身は生成しない。無料の外部サービス(gTTS/Pollinations)とローカルツール(FFmpeg/Remotion)を呼び出すだけ。
"""
import json, os, re, subprocess, sys
import urllib.parse, urllib.request

BASE   = os.path.dirname(os.path.abspath(__file__))   # .../my2-short-maker/scripts
PKG    = os.path.dirname(BASE)                          # .../my2-short-maker
APP    = os.path.join(PKG, "app")
PUBLIC = os.path.join(APP, "public")
AUDIO_DIR = os.path.join(PUBLIC, "faceless-audio")
BG_DIR    = os.path.join(PUBLIC, "faceless-bg")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(BG_DIR, exist_ok=True)

FPS = 30
TTS_ENGINE = "gtts"   # "gtts"(無料/自然/要ネット) or "say"(Mac標準/棒読み/オフライン)
VOICE = "Kyoko"       # sayエンジン時の音声
RATE  = 165           # sayエンジン時の読み上げ速度
SPEED = 1.5           # 話速（1.0=等速, 1.5=1.5倍速, 2.0=2倍速。gTTSはもったりするので1.4〜1.6推奨）
TAIL_SEC = 0.30       # 各シーン後の余白

# ---- 見た目・BGMの既定（settings.jsonで「その人の理想」に育てる）----
STYLE = {
    "caption_font": "\"Hiragino Sans\",\"Hiragino Kaku Gothic ProN\",\"Noto Sans JP\",sans-serif",
    "emph_color": "#F5C542",     # 強調ワードの色
    "caption_stroke": "#000000", # 字幕の外フチ色
    "cover_stroke": "#231200",   # カバー文字の外フチ色
}
BGM = {"file": "", "volume": 0.08}  # file=app/public/配下の相対パス(例 'bgm/calm.mp3')

# ---- 読み込み順：settings.json（土台）→ script.json（個別・優先）----
SETTINGS_PATH = os.path.join(PKG, "settings.json")
SCRIPT_PATH   = os.path.join(PKG, "script.json")

# ---- サンプル台本（金運・風水系）----
TITLE = "キッチンにあると貧乏になる絵"
IMG_STYLE = "cinematic, moody dark gold tones, warm light, feng shui wealth atmosphere, high detail, no text, no letters, no people"
COVER = {
    "img": "bright airy sunlit modern kitchen, clean white cabinets and wood, big window with plants, cheerful daylight",
    "img_style": "bright, clean, natural daylight, high detail, no text, no letters, no people",
    "dur_sec": 1.9,
    "say": "キッチンにあると貧乏になる絵",
    "stroke": "#231200",
    "lines": [
        {"t": "キッチン",     "c": "#FFE100"},
        {"t": "にあると",     "c": "#FFE100"},
        {"t": "貧乏になる絵", "c": "#FF5A00"},
    ],
}
SCENES = [
    {"text": "知らないと損する、風水のお話。", "emph": "風水",
     "img": "mystical japanese feng shui still life, gold coins and lucky charm, incense smoke"},
    {"text": "キッチンにこの絵を飾ると、金運がガタ落ちします。", "emph": "金運がガタ落ち",
     "img": "elegant dark traditional japanese kitchen, a framed painting on the wall"},
    {"text": "それは【水の絵】。滝や海など、水を描いた絵です。", "emph": "水の絵",
     "img": "a framed painting of a waterfall and ocean waves hanging on a wall, water art"},
    {"text": "キッチンは火の気。水を持ち込むと気が乱れ、お金が定着しません。", "emph": "お金が定着しません",
     "img": "japanese kitchen stove with gentle flame, fire energy, mystical clashing water ripples"},
    {"text": "もし飾っているなら、今すぐ玄関か寝室へ移動を。", "emph": "今すぐ玄関か寝室へ",
     "img": "serene traditional japanese entrance genkan and calm bedroom interior"},
    {"text": "かわりに黄色い花の絵を飾ると、金運アップ。保存して試してね。", "emph": "金運アップ",
     "img": "bright framed painting of yellow flowers on a wall, prosperity, golden sunlight"},
]

# ① settings.json（その人の理想の型・全動画の土台）を先に読む
if os.path.exists(SETTINGS_PATH):
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        _st = json.load(f)
    SPEED = _st.get("speed", SPEED)
    TTS_ENGINE = _st.get("engine", TTS_ENGINE)
    IMG_STYLE = _st.get("img_style", IMG_STYLE)
    STYLE.update(_st.get("style", {}))
    for k in ("file", "volume"):
        if k in _st.get("bgm", {}):
            BGM[k] = _st["bgm"][k]
    print(f"[settings.json 使用] speed={SPEED} emph={STYLE['emph_color']} bgm={'あり' if BGM['file'] else 'なし'}")

# ② script.json（1本ごとの台本・settingsより優先）を上書き
if os.path.exists(SCRIPT_PATH):
    with open(SCRIPT_PATH, encoding="utf-8") as f:
        _sc = json.load(f)
    TITLE = _sc.get("title", TITLE)
    IMG_STYLE = _sc.get("img_style", IMG_STYLE)
    TTS_ENGINE = _sc.get("engine", TTS_ENGINE)
    SPEED = _sc.get("speed", SPEED)
    COVER = _sc.get("cover", COVER)
    STYLE.update(_sc.get("style", {}))
    for k in ("file", "volume"):
        if k in _sc.get("bgm", {}):
            BGM[k] = _sc["bgm"][k]
    SCENES = _sc["scenes"]
    print(f"[script.json 使用] title='{TITLE}' scenes={len(SCENES)} engine={TTS_ENGINE} speed={SPEED}")
else:
    print("[サンプル台本 使用]（script.json なし）")

# ---- 字幕の改行（文節＝意味のまとまりで1行。理想2行・最大3行。画面上は「、」「。」禁止）----
_SOFT = "はがをにへとでもやのねよかなくら"
_CLOSERS = "】」）"

def _protect_spans(text, emph):
    spans = [(m.start(), m.end()) for m in re.finditer(r"【[^】]*】|「[^」]*」|（[^）]*）", text)]
    if emph:
        s = 0
        while True:
            i = text.find(emph, s)
            if i < 0:
                break
            spans.append((i, i + len(emph))); s = i + len(emph)
    return spans

def _split_long(phrase, emph, max_line):
    if len(phrase) <= max_line:
        return [phrase]
    spans = _protect_spans(phrase, emph)
    def ok(i):
        for a, b in spans:
            if a <= i < b - 1:
                return False
        if any(i == b - 1 for a, b in spans):
            return True
        return phrase[i] in _SOFT or phrase[i] in _CLOSERS
    import math
    need = min(3, math.ceil(len(phrase) / max_line))
    out, start = [], 0
    for k in range(1, need):
        target = round(len(phrase) * k / need)
        best, bd = -1, 999
        for i in range(start, len(phrase) - 1):
            if ok(i):
                d = abs(i + 1 - target)
                if d < bd:
                    bd, best = d, i
        if best < start:
            continue
        out.append(phrase[start:best + 1]); start = best + 1
    out.append(phrase[start:])
    return [o for o in out if o]

def wrap_caption(text, emph, max_line=15):
    phrases, cur = [], ""
    for tok in re.split(r"([、。！？])", text):
        if tok in "、。":
            if cur.strip():
                phrases.append(cur.strip()); cur = ""
        elif tok in "！？":
            cur += tok
            if cur.strip():
                phrases.append(cur.strip()); cur = ""
        else:
            cur += tok
    if cur.strip():
        phrases.append(cur.strip())
    lines = []
    for p in phrases:
        lines.extend(_split_long(p, emph, max_line))
    while len(lines) > 3:
        bi, bl = 0, 999
        for i in range(len(lines) - 1):
            L = len(lines[i]) + len(lines[i + 1])
            if L < bl:
                bl, bi = L, i
        lines[bi:bi + 2] = [lines[bi] + lines[bi + 1]]
    return lines

def dur_seconds(path):
    out = subprocess.check_output([
        "ffprobe","-v","quiet","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1", path
    ]).decode().strip()
    return float(out)

def fetch_bg(prompt, out_path, seed, style=None):
    """Pollinations(無料AI画像)で背景を生成。失敗時はFalse。"""
    full = f"{prompt}, {style or IMG_STYLE}"
    enc = urllib.parse.quote(full)
    url = f"https://image.pollinations.ai/prompt/{enc}?width=1080&height=1920&nologo=true&seed={seed}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if len(data) > 5000:
                with open(out_path, "wb") as f:
                    f.write(data)
                return True
        except Exception as e:
            print(f"  bg retry {attempt+1}: {e}")
    return False

def synth(text, wav):
    """台本1行 -> wav(48k stereo)。エンジンはTTS_ENGINEで切替。"""
    if TTS_ENGINE == "gtts":
        from gtts import gTTS
        raw = wav.replace(".wav", ".mp3")
        gTTS(text, lang="ja").save(raw)
    else:  # say (macOSのみ)
        raw = wav.replace(".wav", ".aiff")
        subprocess.run(["say","-v",VOICE,"-r",str(RATE),"-o",raw,text], check=True)
    cmd = ["ffmpeg","-y","-i",raw,"-ar","48000","-ac","2"]
    if abs(SPEED - 1.0) > 0.01:
        cmd += ["-filter:a", f"atempo={SPEED}"]
    cmd += [wav]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(raw)

scenes_out = []

# --- カバー(サムネ)フレーム ---
cover_out = None
cover_frames = 0
if COVER:
    cf = os.path.join(BG_DIR, "cover.jpg")
    ok = fetch_bg(COVER["img"], cf, seed=77, style=COVER.get("img_style"))
    cwav = os.path.join(AUDIO_DIR, "cover.wav")
    synth(COVER.get("say", TITLE), cwav)
    call_sec = dur_seconds(cwav)
    cover_frames = max(round(COVER.get("dur_sec", 1.9) * FPS), round((call_sec + 0.5) * FPS))
    cover_out = {
        "image": "faceless-bg/cover.jpg" if ok else "",
        "audio": "faceless-audio/cover.wav",
        "durationInFrames": cover_frames,
        "lines": COVER["lines"],
        "stroke": COVER.get("stroke", STYLE["cover_stroke"]),
    }
    print(f"cover: {cover_frames}f  call={call_sec:.2f}s  img={'OK' if ok else '-'}")

cursor = cover_frames
for i, sc in enumerate(SCENES, 1):
    wav = os.path.join(AUDIO_DIR, f"line_{i:02d}.wav")
    synth(sc["text"], wav)
    sec = dur_seconds(wav) + TAIL_SEC
    frames = max(1, round(sec * FPS))
    bg_rel = ""
    if sc.get("img"):
        bg_file = os.path.join(BG_DIR, f"bg_{i:02d}.jpg")
        reuse = os.path.exists(bg_file) and os.path.getsize(bg_file) > 5000
        if reuse or fetch_bg(sc["img"], bg_file, seed=100 + i):
            bg_rel = f"faceless-bg/bg_{i:02d}.jpg"
    scenes_out.append({
        "text": sc["text"],
        "emph": sc.get("emph", ""),
        "lines": wrap_caption(sc["text"], sc.get("emph", "")),
        "audio": f"faceless-audio/line_{i:02d}.wav",
        "bg": bg_rel,
        "startFrame": cursor,
        "durationInFrames": frames,
    })
    cursor += frames
    print(f"scene {i}: {sec:.2f}s -> {frames}f  bg={'OK' if bg_rel else '-'}  '{sc['text'][:16]}...'")

plan = {
    "fps": FPS, "width": 1080, "height": 1920,
    "title": TITLE, "cover": cover_out,
    "style": STYLE, "bgm": BGM,
    "totalDurationInFrames": cursor, "scenes": scenes_out,
}
out_path = os.path.join(PUBLIC, "faceless-plan.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(plan, f, ensure_ascii=False, indent=2)
print("WROTE", out_path, "total frames:", cursor, f"({cursor/FPS:.1f}s)")
