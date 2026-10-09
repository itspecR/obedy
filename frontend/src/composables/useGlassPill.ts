import { onBeforeUnmount, reactive, type Ref } from "vue";
import {
  boxOf,
  CLICK_MOTION,
  MAX_POUR,
  neckOf,
  REST_SCALE,
  sameBox,
  springSettled,
  springStep,
  type Axis,
  type GlassBox,
  type Motion,
  type Scale,
  type SpringState,
} from "../components/ui/glass";
import { lightModeOn } from "./useLightMode";

const SHIMMER_MS = 700;
const MAX_FRAME_S = 1 / 30;

export interface GlassMotion {
  dx: number;
  dy: number;
  sx: number;
  sy: number;
}

export const STILL: GlassMotion = { dx: 0, dy: 0, sx: 1, sy: 1 };

export interface GlassPill {
  box: GlassBox | null;
  motion: GlassMotion;
  shown: boolean;
  moving: boolean;
  lifted: boolean;
  scale: Scale;
  offset: { x: number; y: number };
  angle: number;
}

interface Edges {
  axis: Axis;
  size: number;
  near: SpringState;
  far: SpringState;
  anchorNear: number;
  anchorFar: number;
}

export function useGlassPill(track: Ref<HTMLElement | null>) {
  const pill = reactive<GlassPill>({ box: null, motion: STILL, shown: false, moving: false, lifted: false, scale: REST_SCALE, offset: { x: 0, y: 0 }, angle: 0 });
  let settle = 0;
  let frame = 0;
  let last = 0;
  let edges: Edges | null = null;
  let target: GlassBox | null = null;
  let motion: Motion = CLICK_MOTION;

  function place(item: HTMLElement | null, instant = false): void {
    const host = track.value;
    if (!item || !host) {
      pill.shown = false;
      return;
    }
    const box = boxOf(item, host);
    if (instant || !pill.shown || !pill.box) {
      show(box);
      return;
    }
    moveTo(box, CLICK_MOTION);
    shimmer();
  }

  function show(box: GlassBox): void {
    stop();
    target = box;
    pill.box = box;
    pill.motion = STILL;
    pill.shown = true;
  }

  function moveTo(box: GlassBox, next: Motion): void {
    const host = track.value;
    if (!host || !pill.box || stillMotion()) {
      show(box);
      return;
    }
    motion = next;
    if (target && sameBox(target, box) && frame) {
      return;
    }
    target = box;
    if (!edges) {
      edges = edgesOf(pill.box, host);
    }
    if (!frame) {
      last = performance.now();
      frame = requestAnimationFrame(tick);
    }
  }

  function tick(now: number): void {
    frame = 0;
    if (!edges || !target) {
      return;
    }
    const seconds = Math.min(Math.max((now - last) / 1000, 0), MAX_FRAME_S);
    last = now;
    const goal = edgesOf(target, edges);
    const forward = goal.near.value >= edges.near.value;
    const [nearTune, farTune] = forward ? [motion.trail, motion.lead] : [motion.lead, motion.trail];
    edges.near = springStep(edges.near, goal.near.value, nearTune, seconds);
    edges.far = springStep(edges.far, goal.far.value, farTune, seconds);
    if (springSettled(edges.near, goal.near.value) && springSettled(edges.far, goal.far.value)) {
      pill.box = target;
      pill.motion = STILL;
      edges = null;
      return;
    }
    pill.motion = motionOf(edges, goal);
    frame = requestAnimationFrame(tick);
  }

  function stop(): void {
    cancelAnimationFrame(frame);
    frame = 0;
    edges = null;
  }

  function shimmer(): void {
    pill.moving = true;
    window.clearTimeout(settle);
    settle = window.setTimeout(() => (pill.moving = false), SHIMMER_MS);
  }

  onBeforeUnmount(() => {
    window.clearTimeout(settle);
    stop();
  });

  return { pill, place, show, moveTo, shimmer };
}

function edgesOf(box: GlassBox, host: HTMLElement | Edges): Edges {
  const axis: Axis = "axis" in host ? host.axis : getComputedStyle(host).flexDirection.startsWith("row") ? "x" : "y";
  const size = "axis" in host ? host.size : axis === "x" ? host.clientWidth : host.clientHeight;
  const near = axis === "x" ? box.left : box.top;
  const far = size - (axis === "x" ? box.right : box.bottom);
  return { axis, size, near: { value: near, velocity: 0 }, far: { value: far, velocity: 0 }, anchorNear: near, anchorFar: far };
}

function motionOf(edges: Edges, goal: Edges): GlassMotion {
  const shift = (edges.near.value + edges.far.value - edges.anchorNear - edges.anchorFar) / 2;
  const stretch = Math.min(Math.max(edges.far.value - edges.near.value, 1) / Math.max(edges.anchorFar - edges.anchorNear, 1), MAX_POUR);
  const neck = neckOf(
    { near: edges.near.value, far: edges.far.value },
    { near: edges.anchorNear, far: edges.anchorFar },
    { near: goal.near.value, far: goal.far.value },
  );
  return edges.axis === "x" ? { dx: shift, dy: 0, sx: stretch, sy: neck } : { dx: 0, dy: shift, sx: neck, sy: stretch };
}

function stillMotion(): boolean {
  return lightModeOn() || (typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches);
}
