import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background, OutroCTA, ProgressBar} from './Chrome';
import {Colors, FONT} from './theme';

// Big-stat reel: a huge number counts up, then supporting lines appear.

export const COUNT_FRAMES = 90;
export const LINE_FRAMES = 55;
export const OUTRO_FRAMES = 75;

export type BigStatProps = {
  stat: number;
  suffix: string;
  label: string;
  lines: string[];
  handle: string;
  colors: Colors;
};

export const BigStat: React.FC<BigStatProps> = ({stat, suffix, label, lines, handle, colors}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const count = spring({frame, fps, config: {damping: 30}, durationInFrames: COUNT_FRAMES});
  const shown = Math.round(count * stat);
  const labelIn = interpolate(frame, [25, 45], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      <Background colors={colors} />
      <div
        style={{
          position: 'absolute',
          top: 300,
          width: '100%',
          padding: '0 90px',
          fontFamily: FONT,
          textAlign: 'center',
        }}
      >
        <div style={{fontSize: 260, fontWeight: 700, color: colors.accent, lineHeight: 1}}>
          {shown.toLocaleString('en-US')}
          {suffix}
        </div>
        <div style={{fontSize: 62, fontWeight: 700, color: colors.text, marginTop: 30, opacity: labelIn}}>
          {label}
        </div>
        <div style={{marginTop: 110, textAlign: 'left'}}>
          {lines.map((line, i) => {
            const start = COUNT_FRAMES + i * LINE_FRAMES;
            const pop = spring({frame: frame - start, fps, config: {damping: 14}});
            if (frame < start) return null;
            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  gap: 30,
                  alignItems: 'flex-start',
                  marginBottom: 48,
                  opacity: pop,
                  transform: `translateX(${(1 - pop) * 70}px)`,
                }}
              >
                <div style={{width: 14, alignSelf: 'stretch', borderRadius: 7, background: colors.accent}} />
                <div style={{fontSize: 50, fontWeight: 400, color: colors.text2, lineHeight: 1.25}}>{line}</div>
              </div>
            );
          })}
        </div>
      </div>
      <OutroCTA colors={colors} handle={handle} startFrame={durationInFrames - OUTRO_FRAMES} />
      <ProgressBar colors={colors} />
    </AbsoluteFill>
  );
};
