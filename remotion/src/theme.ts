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
// Raced against a 10s timer: on a saturated CI runner the font fetch can stall
// behind video-asset streaming — a missed font must never fail the render.
const ready = delayRender('loading Inter', {timeoutInMs: 120000});
const loads = Promise.all(
  [
    new FontFace('Inter', `url('${staticFile('fonts/Inter-Bold.ttf')}')`, {weight: '700'}),
    new FontFace('Inter', `url('${staticFile('fonts/Inter-Regular.ttf')}')`, {weight: '400'}),
  ].map((f) => f.load()),
).then((fonts) => fonts.forEach((f) => document.fonts.add(f)));
Promise.race([loads, new Promise((res) => setTimeout(res, 10000))])
  .catch(() => undefined) // fall back to sans-serif
  .then(() => continueRender(ready));

export const FONT = 'Inter, Helvetica, Arial, sans-serif';
