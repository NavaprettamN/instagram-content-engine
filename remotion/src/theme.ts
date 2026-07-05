import {continueRender, delayRender, staticFile} from 'remotion';

// Palette shape mirrors agents/design_agent.py PALETTES (passed in via props).
export type Colors = {
  bgTop: string;
  bgBottom: string;
  accent: string;
  text: string;
  text2: string;
};

// Load the bundled Inter fonts (remotion/public/fonts -> ../../fonts symlink).
const ready = delayRender('loading Inter');
Promise.all(
  [
    new FontFace('Inter', `url('${staticFile('fonts/Inter-Bold.ttf')}')`, {weight: '700'}),
    new FontFace('Inter', `url('${staticFile('fonts/Inter-Regular.ttf')}')`, {weight: '400'}),
  ].map((f) => f.load()),
)
  .then((fonts) => {
    fonts.forEach((f) => document.fonts.add(f));
    continueRender(ready);
  })
  .catch(() => continueRender(ready)); // fall back to sans-serif, never hang the render

export const FONT = 'Inter, Helvetica, Arial, sans-serif';
