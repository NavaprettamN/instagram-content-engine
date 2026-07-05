import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background, OutroCTA, ProgressBar} from './Chrome';
import {Colors, FONT} from './theme';

// Kinetic-typography list reel: title springs in, items pop in one by one and
// stack, outro CTA. Duration is computed in Root.tsx's calculateMetadata.

export const TITLE_FRAMES = 60;
export const ITEM_FRAMES = 66; // ~2.2s per item at 30fps
export const OUTRO_FRAMES = 75;

export type KineticListProps = {
  title: string;
  items: string[];
  handle: string;
  colors: Colors;
};

export const KineticList: React.FC<KineticListProps> = ({title, items, handle, colors}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const titlePop = spring({frame, fps, config: {damping: 12}});
  const underline = interpolate(frame, [12, 28], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      <Background colors={colors} />
      <div style={{position: 'absolute', top: 180, width: '100%', padding: '0 90px', fontFamily: FONT}}>
        <div
          style={{
            fontSize: 92,
            fontWeight: 700,
            lineHeight: 1.05,
            color: colors.text,
            transform: `scale(${titlePop})`,
            transformOrigin: 'left bottom',
          }}
        >
          {title}
        </div>
        <div
          style={{
            height: 12,
            width: `${underline * 45}%`,
            background: colors.accent,
            marginTop: 28,
            borderRadius: 6,
          }}
        />
        <div style={{marginTop: 80}}>
          {items.map((item, i) => {
            const start = TITLE_FRAMES + i * ITEM_FRAMES;
            const pop = spring({frame: frame - start, fps, config: {damping: 13}});
            if (frame < start) return null;
            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 34,
                  marginBottom: 54,
                  transform: `translateY(${(1 - pop) * 60}px) scale(${0.7 + pop * 0.3})`,
                  opacity: pop,
                  transformOrigin: 'left center',
                }}
              >
                <div
                  style={{
                    minWidth: 84,
                    height: 84,
                    borderRadius: 24,
                    background: colors.accent,
                    color: colors.bgTop,
                    fontSize: 46,
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {i + 1}
                </div>
                <div style={{fontSize: 54, fontWeight: 700, color: colors.text, lineHeight: 1.15}}>{item}</div>
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
