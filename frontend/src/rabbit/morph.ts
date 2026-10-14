export interface Box {
  left: number;
  top: number;
  width: number;
  height: number;
}

export const NO_BOX: Box = { left: 0, top: 0, width: 0, height: 0 };
export const MORPH_MS = 650;
export const SWAP_IN = 0.6;
export const SWAP_OUT = 0.4;

const BODY_WIDTH = 0.34;
const BODY_HEIGHT = 0.76;
const BODY_TOP = 0.12;

export function boxOf(element: Element): Box {
  const { left, top, width, height } = element.getBoundingClientRect();
  return { left, top, width, height };
}

export function bodyOf(frame: Box): Box {
  const width = frame.width * BODY_WIDTH;
  return { left: frame.left + (frame.width - width) / 2, top: frame.top + frame.height * BODY_TOP, width, height: frame.height * BODY_HEIGHT };
}
