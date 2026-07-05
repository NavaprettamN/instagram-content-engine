import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Colors, FONT} from './theme';

// Shared frame: animated gradient bg + drifting accent blob, bottom progress
// bar, and an outro CTA — the same brand chrome on every motion reel.

export const Background: React.FC<{colors: Colors}> = ({colors}) => {
  const frame = useCurrentFrame();
  const x = Math.sin(frame / 55) * 90;
  const y = Math.cos(frame / 70) * 70;
  return (
    <AbsoluteFill style={{background: `linear-gradient(160deg, ${colors.bgTop} 20%, ${colors.bgBottom})`}}>
      <div
        style={{
          position: 'absolute',
          width: 900,
          height: 900,
          left: 400 + x,
          top: 1100 + y,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${colors.accent}33, transparent 70%)`,
        }}
      />
    </AbsoluteFill>
  );
};

export const ProgressBar: React.FC<{colors: Colors}> = ({colors}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, width} = useVideoConfig();
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        height: 14,
        width: (frame / durationInFrames) * width,
        background: colors.accent,
        opacity: 0.9,
      }}
    />
  );
};

export const OutroCTA: React.FC<{colors: Colors; handle: string; startFrame: number}> = ({
  colors,
  handle,
  startFrame,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 120,
        width: '100%',
        textAlign: 'center',
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: 44,
        color: colors.text2,
        opacity,
      }}
    >
      Save this 📌 · follow {handle}
    </div>
  );
};
