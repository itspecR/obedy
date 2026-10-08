export interface GlassBox {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface GlassItem {
  offsetTop: number;
  offsetLeft: number;
  offsetWidth: number;
  offsetHeight: number;
}

export interface GlassTrack {
  clientWidth: number;
  clientHeight: number;
}

export function boxOf(item: GlassItem, track: GlassTrack): GlassBox {
  return {
    top: item.offsetTop,
    left: item.offsetLeft,
    right: track.clientWidth - item.offsetLeft - item.offsetWidth,
    bottom: track.clientHeight - item.offsetTop - item.offsetHeight,
  };
}

export function isForward(from: GlassBox | null, to: GlassBox): boolean {
  return !from || to.top > from.top || to.left > from.left;
}

export function sameBox(a: GlassBox | null, b: GlassBox): boolean {
  return a !== null && a.top === b.top && a.left === b.left && a.right === b.right && a.bottom === b.bottom;
}

export type Axis = "x" | "y";

export interface Scale {
  x: number;
  y: number;
}

export const REST_SCALE: Scale = { x: 1, y: 1 };
export const LIFT = 1.14;
const LIFT_PX = 14;
const LIFT_PX_HEIGHT = 8;

export function liftOf(width: number, height: number): Scale {
  return { x: Math.min(1 + LIFT_PX / Math.max(width, 1), LIFT), y: Math.min(1 + LIFT_PX_HEIGHT / Math.max(height, 1), LIFT) };
}
const MAX_STRETCH = 0.4;
const STRETCH_PER_SPEED = 0.35;

export function stretchOf(vx: number, vy: number, lift: Scale = { x: LIFT, y: LIFT }): Scale {
  const along = Math.min(Math.hypot(vx, vy) * STRETCH_PER_SPEED, MAX_STRETCH);
  const grow = 1 + along;
  const shrink = 1 / (1 + along * 0.7);
  return Math.abs(vx) >= Math.abs(vy) ? { x: lift.x * grow, y: lift.y * shrink } : { x: lift.x * shrink, y: lift.y * grow };
}

export function centerOf(box: GlassBox, track: GlassTrack, axis: Axis): number {
  return axis === "x" ? (box.left + track.clientWidth - box.right) / 2 : (box.top + track.clientHeight - box.bottom) / 2;
}

export function shiftBox(box: GlassBox, axis: Axis, shift: number): GlassBox {
  return axis === "x"
    ? { ...box, left: box.left + shift, right: box.right - shift }
    : { ...box, top: box.top + shift, bottom: box.bottom - shift };
}

export function nearestIndex(centers: number[], point: number): number {
  return centers.reduce((best, center, index) => (Math.abs(center - point) < Math.abs(centers[best] - point) ? index : best), 0);
}

export function clamp(value: number, low: number, high: number): number {
  return Math.min(Math.max(value, low), high);
}

export interface Lean {
  offset: { x: number; y: number };
  scale: Scale;
  angle: number;
}

const LEAN_ZONE = 180;
const LEAN_PULL = 0.06;
const LEAN_MAX_PX = 6;
const LEAN_ELASTICITY = 0.35;

export const NO_LEAN: Lean = { offset: { x: 0, y: 0 }, scale: REST_SCALE, angle: 0 };

export function leanOf(pointer: { x: number; y: number }, box: GlassBox, track: GlassTrack): Lean {
  const width = track.clientWidth - box.left - box.right;
  const height = track.clientHeight - box.top - box.bottom;
  const dx = pointer.x - (box.left + width / 2);
  const dy = pointer.y - (box.top + height / 2);
  const outside = Math.hypot(Math.max(0, Math.abs(dx) - width / 2), Math.max(0, Math.abs(dy) - height / 2));
  const distance = Math.hypot(dx, dy);
  if (outside > LEAN_ZONE || distance === 0) {
    return NO_LEAN;
  }
  const fade = 1 - outside / LEAN_ZONE;
  const [nx, ny] = [Math.abs(dx) / distance, Math.abs(dy) / distance];
  const stretch = Math.min(distance / 300, 1) * LEAN_ELASTICITY * fade;
  return {
    offset: { x: clamp(dx * LEAN_PULL * fade, -LEAN_MAX_PX, LEAN_MAX_PX), y: clamp(dy * LEAN_PULL * fade, -LEAN_MAX_PX, LEAN_MAX_PX) },
    scale: { x: Math.max(0.8, 1 + nx * stretch * 0.3 - ny * stretch * 0.15), y: Math.max(0.8, 1 + ny * stretch * 0.3 - nx * stretch * 0.15) },
    angle: clamp((dx / Math.max(width, 1)) * 100 * 1.2, -60, 60),
  };
}

const THROW_MS = 170;
const MAX_THROW_SPEED = 3;
const THROW_PAUSE_MS = 90;

export function projectLanding(point: number, velocity: number): number {
  return point + clamp(velocity, -MAX_THROW_SPEED, MAX_THROW_SPEED) * THROW_MS;
}

export function releaseVelocity(velocity: number, pauseMs: number): number {
  return pauseMs > THROW_PAUSE_MS ? 0 : velocity;
}

const EDGE_ZONE = 44;
const EDGE_MAX_SPEED = 14;

export function edgeScrollSpeed(position: number, size: number): number {
  if (position < EDGE_ZONE) {
    return -EDGE_MAX_SPEED * (1 - Math.max(position, 0) / EDGE_ZONE);
  }
  if (position > size - EDGE_ZONE) {
    return EDGE_MAX_SPEED * (1 - Math.max(size - position, 0) / EDGE_ZONE);
  }
  return 0;
}

export interface SpringState {
  value: number;
  velocity: number;
}

export interface SpringTune {
  stiffness: number;
  damping: number;
}

function tune(stiffness: number, ratio: number): SpringTune {
  return { stiffness, damping: 2 * ratio * Math.sqrt(stiffness) };
}

export interface Motion {
  lead: SpringTune;
  trail: SpringTune;
}

export const CLICK_MOTION: Motion = { lead: tune(240, 0.76), trail: tune(120, 0.88) };
export const MAX_POUR = 2.6;
export const FOLLOW_MOTION: Motion = { lead: tune(1300, 0.92), trail: tune(800, 0.95) };
export const DROP_MOTION: Motion = { lead: tune(330, 0.62), trail: tune(210, 0.68) };
export const LEAD_SPRING = DROP_MOTION.lead;
export const TRAIL_SPRING = DROP_MOTION.trail;

export function springStep(state: SpringState, target: number, tune: SpringTune, seconds: number): SpringState {
  const force = -tune.stiffness * (state.value - target) - tune.damping * state.velocity;
  const velocity = state.velocity + force * seconds;
  return { value: state.value + velocity * seconds, velocity };
}

export function springSettled(state: SpringState, target: number): boolean {
  return Math.abs(state.value - target) < 0.25 && Math.abs(state.velocity) < 4;
}

export function smoothVelocity(previous: number, sample: number): number {
  return previous * 0.6 + sample * 0.4;
}

const KEY_STEPS: Record<Axis, Record<string, number>> = {
  y: { ArrowDown: 1, ArrowUp: -1 },
  x: { ArrowRight: 1, ArrowLeft: -1 },
};

export function nextIndex(current: number, key: string, axis: Axis, count: number): number | null {
  if (count === 0) {
    return null;
  }
  if (key === "Home") {
    return 0;
  }
  if (key === "End") {
    return count - 1;
  }
  const step = KEY_STEPS[axis][key];
  return step ? (current + step + count) % count : null;
}

const REVEAL_MARGIN = 12;

export function revealScroll(itemStart: number, itemSize: number, scroll: number, view: number, content: number): number | null {
  const fits = itemStart - REVEAL_MARGIN >= scroll && itemStart + itemSize + REVEAL_MARGIN <= scroll + view;
  if (fits) {
    return null;
  }
  return clamp(itemStart + itemSize / 2 - view / 2, 0, Math.max(content - view, 0));
}

export interface Span {
  near: number;
  far: number;
}

const NECK_FLOOR = 0.72;

export function neckOf(current: Span, from: Span, to: Span): number {
  const center = (current.near + current.far) / 2;
  const start = (from.near + from.far) / 2;
  const end = (to.near + to.far) / 2;
  const progress = end === start ? 1 : clamp((center - start) / (end - start), 0, 1);
  const natural = from.far - from.near + (to.far - to.near - (from.far - from.near)) * progress;
  const elongation = (current.far - current.near) / Math.max(natural, 1);
  return elongation <= 1 ? 1 : Math.max(1 / Math.sqrt(elongation), NECK_FLOOR);
}
