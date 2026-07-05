import React from 'react';
import {Composition} from 'remotion';
import {BigStat, BigStatProps, COUNT_FRAMES, LINE_FRAMES} from './BigStat';
import {ITEM_FRAMES, KineticList, KineticListProps, OUTRO_FRAMES, TITLE_FRAMES} from './KineticList';
import {Scenes, ScenesProps} from './Scenes';

const COLORS = {bgTop: '#1a1a2e', bgBottom: '#16213e', accent: '#e94560', text: '#ffffff', text2: '#cfd3e0'};
const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Scenes"
        component={Scenes}
        fps={FPS}
        width={1080}
        height={1920}
        durationInFrames={300}
        defaultProps={
          {
            scenes: [
              {src: '', kind: 'none', headline: 'You waste 2 hours daily', from: 0, dur: 75},
              {src: '', kind: 'none', headline: 'AI fixes that today', from: 75, dur: 75},
            ],
            handle: '@contentengine2',
            colors: COLORS,
          } satisfies ScenesProps
        }
        calculateMetadata={({props}) => {
          const last = props.scenes[props.scenes.length - 1];
          return {durationInFrames: last ? last.from + last.dur : 300};
        }}
      />
      <Composition
        id="KineticList"
        component={KineticList}
        fps={FPS}
        width={1080}
        height={1920}
        durationInFrames={300}
        defaultProps={
          {
            title: '5 AI tools that save hours',
            items: ['Draft emails in seconds', 'Summarize any meeting', 'Auto-organize your notes', 'Fix code while you sleep', 'Plan your week in 1 tap'],
            handle: '@contentengine2',
            colors: COLORS,
          } satisfies KineticListProps
        }
        calculateMetadata={({props}) => ({
          durationInFrames: TITLE_FRAMES + props.items.length * ITEM_FRAMES + OUTRO_FRAMES,
        })}
      />
      <Composition
        id="BigStat"
        component={BigStat}
        fps={FPS}
        width={1080}
        height={1920}
        durationInFrames={300}
        defaultProps={
          {
            stat: 87,
            suffix: '%',
            label: 'of tasks can be automated',
            lines: ['Most people automate none of them', 'Start with your inbox — 40 min back a day', 'The tools are free. The excuse is gone.'],
            handle: '@contentengine2',
            colors: COLORS,
          } satisfies BigStatProps
        }
        calculateMetadata={({props}) => ({
          durationInFrames: COUNT_FRAMES + props.lines.length * LINE_FRAMES + OUTRO_FRAMES,
        })}
      />
    </>
  );
};
