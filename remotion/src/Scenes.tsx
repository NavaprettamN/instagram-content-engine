import React from 'react';
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {Background, OutroCTA, ProgressBar} from './Chrome';
import {Colors, FONT} from './theme';

// Ad-style scene reel: one full-screen scene per spoken sentence (timings come
// from TTS sentence boundaries via props). Each scene = AI image with Ken Burns
// zoom OR muted b-roll video OR brand gradient, dark-graded, with a 3-5 word
// kinetic headline synced to the voice.

export type Scene = {
  src: string; // path under remotion/public (staticFile), '' when kind='none'
  kind: 'image' | 'video' | 'none';
  headline: string;
  from: number; // frames
  dur: number; // frames
};

export type ScenesProps = {
  scenes: Scene[];
  handle: string;
  colors: Colors;
};

const Media: React.FC<{scene: Scene; index: number; colors: Colors}> = ({scene, index, colors}) => {
  const frame = useCurrentFrame(); // local to the Sequence
  // Ken Burns: slow zoom, direction alternating per scene; videos get a gentler push.
  const zoomIn = index % 2 === 0;
  const range = scene.kind === 'video' ? 0.06 : 0.14;
  const z = interpolate(frame, [0, scene.dur], zoomIn ? [1.02, 1.02 + range] : [1.02 + range, 1.02]);
  const style: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    transform: `scale(${z})`,
  };
  if (scene.kind === 'image') {
    return <Img src={staticFile(scene.src)} style={style} />;
  }
  if (scene.kind === 'video') {
    return <OffthreadVideo src={staticFile(scene.src)} muted loop style={style} />;
  }
  return <Background colors={colors} />;
};

const Headline: React.FC<{text: string; colors: Colors}> = ({text, colors}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.split(/\s+/).filter(Boolean);
  return (
    <div
      style={{
        position: 'absolute',
        top: '58%',
        width: '100%',
        padding: '0 70px',
        textAlign: 'center',
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: 84,
        lineHeight: 1.12,
        color: '#ffffff',
        textShadow: '0 4px 30px rgba(0,0,0,0.85)',
      }}
    >
      {words.map((w, i) => {
        const pop = spring({frame: frame - 3 - i * 4, fps, config: {damping: 12}});
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              marginRight: 22,
              opacity: pop,
              transform: `translateY(${(1 - pop) * 40}px) scale(${0.8 + pop * 0.2})`,
              // every other headline word block gets the accent for punch
              color: i === words.length - 1 ? colors.accent : '#ffffff',
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

export const Scenes: React.FC<ScenesProps> = ({scenes, handle, colors}) => {
  const {durationInFrames} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: colors.bgTop}}>
      {scenes.map((s, i) => (
        <Sequence key={i} from={s.from} durationInFrames={s.dur}>
          <SceneShell scene={s} index={i} colors={colors} />
        </Sequence>
      ))}
      <OutroCTA colors={colors} handle={handle} startFrame={durationInFrames - 55} />
      <ProgressBar colors={colors} />
    </AbsoluteFill>
  );
};

const SceneShell: React.FC<{scene: Scene; index: number; colors: Colors}> = ({scene, index, colors}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  // hard-cut energy: quick settle-in from a slight over-zoom + 3-frame fade
  const settle = spring({frame, fps, config: {damping: 16}, durationInFrames: 8});
  const opacity = interpolate(frame, [0, 3], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{opacity, transform: `scale(${1.06 - settle * 0.06})`}}>
      <Media scene={scene} index={index} colors={colors} />
      {/* dark grade + bottom gradient so the headline always reads */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0.15) 45%, rgba(0,0,0,0.72) 100%)',
        }}
      />
      <Headline text={scene.headline} colors={colors} />
    </AbsoluteFill>
  );
};
