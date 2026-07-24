import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from "remotion";

type Scene = {
  text: string;
  emph: string;
  lines?: string[];
  audio: string;
  bg?: string;
  startFrame: number;
  durationInFrames: number;
};
type Cover = {
  image: string;
  audio?: string;
  durationInFrames: number;
  lines: { t: string; c: string }[];
  stroke?: string;
};
type Style = {
  caption_font?: string;
  emph_color?: string;
  caption_stroke?: string;
  cover_stroke?: string;
};
type Bgm = { file?: string; volume?: number };
type Plan = {
  fps: number;
  width: number;
  height: number;
  title: string;
  cover?: Cover | null;
  style?: Style;
  bgm?: Bgm;
  totalDurationInFrames: number;
  scenes: Scene[];
};

const GOLD = "#F5C542";
const CAPTION_FONT = '"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif';
const DEFAULT_STYLE: Required<Style> = {
  caption_font: CAPTION_FONT,
  emph_color: GOLD,
  caption_stroke: "#000000",
  cover_stroke: "#231200",
};

// ---- 背景：ダーク×ゴールドのアニメ＋光の粒 ----
const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const t = frame / 30;
  const glow = 0.35 + 0.15 * Math.sin(t * 0.8);
  const particles = Array.from({ length: 26 }, (_, i) => {
    const seed = i * 12.9898;
    const baseX = ((Math.sin(seed) + 1) / 2) * width;
    const speed = 12 + (i % 5) * 6;
    const y = (height + 80 - ((frame * speed) / 30 + i * 90) % (height + 160));
    const tw = 0.25 + 0.55 * ((Math.sin(t * 1.5 + i) + 1) / 2);
    const size = 4 + (i % 4) * 3;
    return { x: baseX + Math.sin(t + i) * 25, y, o: tw, size };
  });
  return (
    <AbsoluteFill style={{ backgroundColor: "#0d0b16" }}>
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(160deg,#161029 0%,#241634 40%,#3a2410 100%)",
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(60% 45% at 50% 32%, rgba(245,197,66,${glow}) 0%, rgba(245,197,66,0) 60%)`,
        }}
      />
      {particles.map((p, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: p.x,
            top: p.y,
            width: p.size,
            height: p.size,
            borderRadius: "50%",
            background: GOLD,
            opacity: p.o,
            boxShadow: `0 0 ${p.size * 2}px ${GOLD}`,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

// ---- シーン背景：AI画像 + Ken Burnsズーム + 暗幕 ----
const SceneBg: React.FC<{ src: string; dur: number }> = ({ src, dur }) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, dur], [1.06, 1.18], { extrapolateRight: "clamp" });
  const drift = interpolate(frame, [0, dur], [-14, 14], { extrapolateRight: "clamp" });
  const fade = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: fade, overflow: "hidden" }}>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translateY(${drift}px)`,
        }}
      />
      {/* 文字を読みやすくする暗幕（上下を濃く、中央やや明るく） */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(8,6,16,0.62) 0%, rgba(8,6,16,0.22) 34%, rgba(8,6,16,0.30) 60%, rgba(8,6,16,0.72) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

// ---- カバー（サムネ用の冒頭フックフレーム）----
const CoverCard: React.FC<{ cover: Cover; font: string }> = ({ cover, font }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 16, stiffness: 120 }, durationInFrames: 16 });
  const scale = interpolate(pop, [0, 1], [0.9, 1]);
  const imgZoom = interpolate(frame, [0, cover.durationInFrames], [1.04, 1.12], { extrapolateRight: "clamp" });
  const stroke = cover.stroke || "#231200";
  const maxLen = Math.max(...cover.lines.map((l) => l.t.length), 1);
  const coverFont = Math.min(148, Math.floor((1080 - 2 * 60) / (maxLen * 1.02)));
  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#0d0b16" }}>
      {cover.audio ? <Audio src={staticFile(cover.audio)} /> : null}
      {cover.image ? (
        <Img
          src={staticFile(cover.image)}
          style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${imgZoom})` }}
        />
      ) : null}
      {/* 上下ほんのり締めて文字を安定させる */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.18) 0%, rgba(0,0,0,0.02) 30%, rgba(0,0,0,0.02) 70%, rgba(0,0,0,0.22) 100%)",
        }}
      />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 60px" }}>
        <div style={{ transform: `scale(${scale})`, textAlign: "center" }}>
          {cover.lines.map((ln, i) => (
            <div
              key={i}
              style={{
                fontFamily: font,
                fontWeight: 900,
                fontSize: coverFont,
                lineHeight: 1.12,
                color: ln.c,
                WebkitTextStroke: `14px ${stroke}`,
                paintOrder: "stroke fill",
                textShadow: "0 8px 20px rgba(0,0,0,0.55)",
                letterSpacing: "0.01em",
              }}
            >
              {ln.t}
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---- 字幕（強調ワードをハイライト。色・フォントはstyleで可変）----
const Caption: React.FC<{ scene: Scene; style: Required<Style> }> = ({ scene, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 14, stiffness: 140 }, durationInFrames: 18 });
  const scale = interpolate(pop, [0, 1], [0.8, 1]);
  const opacity = interpolate(pop, [0, 1], [0, 1]);

  const { emph } = scene;
  // 事前計算した自然改行のlinesを使う（無ければtext全体を1行）
  const lines = scene.lines && scene.lines.length ? scene.lines : [scene.text];

  // 最長行が画面幅に収まるようフォントサイズを自動調整
  const SAFE_W = 1080 - 2 * 44;
  const maxLen = Math.max(...lines.map((l) => l.length), 1);
  const fontSize = Math.max(56, Math.min(92, Math.floor(SAFE_W / (maxLen * 1.05))));
  const strokeW = Math.max(6, Math.round(fontSize * 0.1));

  // 1行を強調ワードで分割（黄色ハイライト）
  const splitLine = (line: string): { s: string; hi: boolean }[] => {
    if (emph && line.includes(emph)) {
      const idx = line.indexOf(emph);
      return [
        { s: line.slice(0, idx), hi: false },
        { s: emph, hi: true },
        { s: line.slice(idx + emph.length), hi: false },
      ].filter((p) => p.s.length > 0);
    }
    return [{ s: line, hi: false }];
  };

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "0 44px",
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          opacity,
          fontFamily: style.caption_font,
          fontWeight: 900,
          fontSize,
          lineHeight: 1.32,
          textAlign: "center",
          color: "#ffffff",
          WebkitTextStroke: `${strokeW}px ${style.caption_stroke}`,
          paintOrder: "stroke fill",
          textShadow: "0 8px 24px rgba(0,0,0,0.55)",
          letterSpacing: "0.01em",
        }}
      >
        {lines.map((line, li) => (
          <div key={li} style={{ whiteSpace: "nowrap" }}>
            {splitLine(line).map((p, i) =>
              p.hi ? (
                <span key={i} style={{ color: style.emph_color, WebkitTextStroke: `${strokeW}px ${style.caption_stroke}` }}>
                  {p.s}
                </span>
              ) : (
                <span key={i}>{p.s}</span>
              )
            )}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

export const FacelessShort: React.FC<{ plan: Plan }> = ({ plan }) => {
  const style: Required<Style> = { ...DEFAULT_STYLE, ...(plan.style || {}) };
  const bgm = plan.bgm;
  return (
    <AbsoluteFill>
      <Background />
      {/* BGM（settings.jsonで指定・全編ループ） */}
      {bgm && bgm.file ? (
        <Audio src={staticFile(bgm.file)} volume={bgm.volume ?? 0.08} loop />
      ) : null}
      {/* 背景＋字幕（各シーン） */}
      {plan.scenes.map((scene, i) => (
        <Sequence key={i} from={scene.startFrame} durationInFrames={scene.durationInFrames}>
          <Audio src={staticFile(scene.audio)} />
          {scene.bg ? <SceneBg src={scene.bg} dur={scene.durationInFrames} /> : null}
          <Caption scene={scene} style={style} />
        </Sequence>
      ))}
      {/* カバー（最前面・冒頭のみ） */}
      {plan.cover ? (
        <Sequence from={0} durationInFrames={plan.cover.durationInFrames}>
          <CoverCard cover={plan.cover} font={style.caption_font} />
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};
