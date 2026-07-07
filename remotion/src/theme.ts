import {continueRender, delayRender} from 'remotion';
import './fonts.css'; // Inter as base64 @font-face — no network fetch (see fonts.css)

// Palette shape mirrors agents/design_agent.py PALETTES (passed in via props).
export type Colors = {
  bgTop: string;
  bgBottom: string;
  accent: string;
  text: string;
  text2: string;
};

// The font bytes are inlined in fonts.css, so this "load" only parses in-memory
// data — it can't stall behind CI video decoding the way a network fetch did.
// (A stalled fetch previously hung delayRender and failed the whole render, and
// Remotion mocks setTimeout during pre-render so a timeout race never fired.)
const ready = delayRender('loading Inter');
Promise.all([document.fonts.load('700 100px Inter'), document.fonts.load('400 100px Inter')])
  .catch(() => undefined) // fall back to sans-serif, never hang
  .then(() => continueRender(ready));

export const FONT = 'Inter, Helvetica, Arial, sans-serif';
