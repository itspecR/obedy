import { onBeforeUnmount, watch, type Ref } from "vue";
import {
  boxOf,
  centerOf,
  clamp,
  DROP_MOTION,
  edgeScrollSpeed,
  FOLLOW_MOTION,
  liftOf,
  nearestIndex,
  projectLanding,
  releaseVelocity,
  REST_SCALE,
  shiftBox,
  smoothVelocity,
  type Axis,
  type GlassBox,
  type Motion,
  type Scale,
} from "../components/ui/glass";
import type { GlassPill } from "./useGlassPill";

const DRAG_THRESHOLD = 5;
const HOLD_MS = 120;
const MOUSE_HOLD_MS = 80;
const SWALLOW_MS = 400;
const HOLD_SLOP = 8;
const GRAB_BUZZ_MS = 8;

interface Controls {
  pill: GlassPill;
  moveTo: (box: GlassBox, motion: Motion) => void;
  shimmer: () => void;
}

export interface DragOptions {
  items: () => HTMLElement[];
  grabNow: (item: HTMLElement, event: PointerEvent) => boolean;
  select: (item: HTMLElement) => void;
  settle: () => void;
}

interface Grab {
  id: number;
  axis: Axis;
  base: GlassBox;
  origin: number;
  point: number;
  time: number;
  velocity: number;
  moved: boolean;
  lift: Scale;
  touch: boolean;
  held: boolean;
  item: HTMLElement;
  centers: number[];
}

interface Hold {
  id: number;
  item: HTMLElement;
  x: number;
  y: number;
  time: number;
  timer: number;
}

export function useGlassDrag(track: Ref<HTMLElement | null>, controls: Controls, options: DragOptions) {
  let grab: Grab | null = null;
  let hold: Hold | null = null;
  let swallowUntil = 0;
  let scrolling = 0;
  let frame = 0;
  let pending: PointerEvent | null = null;
  let lastClient = { x: 0, y: 0 };

  function axisOf(host: HTMLElement): Axis {
    return getComputedStyle(host).flexDirection.startsWith("row") ? "x" : "y";
  }

  function pointOf(client: { x: number; y: number }, host: HTMLElement, axis: Axis): number {
    const rect = host.getBoundingClientRect();
    return axis === "x" ? client.x - rect.left + host.scrollLeft : client.y - rect.top + host.scrollTop;
  }

  function centers(host: HTMLElement, axis: Axis): number[] {
    return options.items().map((item) => centerOf(boxOf(item, host), host, axis));
  }

  function itemOf(event: PointerEvent): HTMLElement | null {
    const target = event.target as Node;
    return options.items().find((item) => item.contains(target)) ?? null;
  }

  function down(event: PointerEvent): boolean {
    const item = itemOf(event);
    if (!track.value || !item || event.button !== 0) {
      return false;
    }
    lastClient = { x: event.clientX, y: event.clientY };
    swallowUntil = 0;
    if (options.grabNow(item, event)) {
      begin(item, event.pointerId, event.timeStamp, event.pointerType !== "mouse", false);
      return true;
    }
    startHold(item, event);
    return false;
  }

  function startHold(item: HTMLElement, event: PointerEvent): void {
    cancelHold();
    const touch = event.pointerType !== "mouse";
    const pending: Hold = { id: event.pointerId, item, x: event.clientX, y: event.clientY, time: event.timeStamp, timer: 0 };
    pending.timer = window.setTimeout(
      () => {
        hold = null;
        begin(pending.item, pending.id, pending.time, touch, true);
        if (touch) {
          navigator.vibrate?.(GRAB_BUZZ_MS);
        }
      },
      touch ? HOLD_MS : MOUSE_HOLD_MS,
    );
    hold = pending;
  }

  function cancelHold(): void {
    if (hold) {
      window.clearTimeout(hold.timer);
      hold = null;
    }
  }

  function begin(item: HTMLElement, id: number, time: number, touch: boolean, held: boolean): void {
    const host = track.value;
    if (!host) {
      return;
    }
    const axis = axisOf(host);
    const base = boxOf(item, host);
    const lift = liftOf(item.offsetWidth, item.offsetHeight);
    const point = pointOf(lastClient, host, axis);
    grab = { id, axis, base, origin: centerOf(base, host, axis), point, time, velocity: 0, moved: false, lift, touch, held, item, centers: centers(host, axis) };
    controls.pill.lifted = true;
    controls.pill.scale = lift;
    controls.moveTo(base, FOLLOW_MOTION);
  }

  function move(event: PointerEvent): void {
    if (hold && event.pointerId === hold.id && Math.hypot(event.clientX - hold.x, event.clientY - hold.y) > HOLD_SLOP) {
      cancelHold();
    }
    if (!grab || event.pointerId !== grab.id) {
      return;
    }
    if (!grab.moved) {
      track.value?.setPointerCapture?.(event.pointerId);
    }
    pending = event;
    if (!frame) {
      frame = requestAnimationFrame(flush);
    }
  }

  function flush(): void {
    frame = 0;
    const event = pending;
    pending = null;
    if (event) {
      apply(event);
    }
  }

  function apply(event: PointerEvent): void {
    const host = track.value;
    if (!grab || !host) {
      return;
    }
    lastClient = { x: event.clientX, y: event.clientY };
    const point = pointOf(lastClient, host, grab.axis);
    if (!grab.moved && Math.abs(point - grab.point) < DRAG_THRESHOLD) {
      return;
    }
    const elapsed = Math.max(event.timeStamp - grab.time, 1);
    grab.velocity = smoothVelocity(grab.velocity, (point - grab.point) / elapsed);
    grab.moved = true;
    grab.point = point;
    grab.time = event.timeStamp;
    follow(grab);
    autoScroll(host, grab);
  }

  function follow(current: Grab): void {
    const all = current.centers;
    const target = clamp(current.point, all[0], all[all.length - 1]);
    controls.moveTo(shiftBox(current.base, current.axis, target - current.origin), FOLLOW_MOTION);
  }

  function autoScroll(host: HTMLElement, current: Grab): void {
    cancelAnimationFrame(scrolling);
    if (current.axis !== "x" || host.scrollWidth <= host.clientWidth) {
      return;
    }
    const rect = host.getBoundingClientRect();
    const speed = edgeScrollSpeed(lastClient.x - rect.left, rect.width);
    if (!speed) {
      return;
    }
    const before = host.scrollLeft;
    host.scrollLeft = before + speed;
    if (host.scrollLeft === before || grab !== current) {
      return;
    }
    current.point = pointOf(lastClient, host, current.axis);
    follow(current);
    scrolling = requestAnimationFrame(() => autoScroll(host, current));
  }

  function up(event: PointerEvent): void {
    if (hold && event.pointerId === hold.id) {
      cancelHold();
    }
    const host = track.value;
    if (!grab || !host || event.pointerId !== grab.id) {
      return;
    }
    if (pending) {
      cancelAnimationFrame(frame);
      flush();
    }
    const finished = grab;
    grab = null;
    cancelAnimationFrame(scrolling);
    if (host.hasPointerCapture?.(event.pointerId)) {
      host.releasePointerCapture(event.pointerId);
    }
    controls.pill.lifted = false;
    controls.pill.scale = REST_SCALE;
    if (event.type === "pointercancel") {
      options.settle();
      return;
    }
    if (!finished.moved && finished.held) {
      land(host, finished.item);
      return;
    }
    if (!finished.moved) {
      if (finished.touch || !itemOf(event)) {
        options.settle();
      }
      return;
    }
    const velocity = releaseVelocity(finished.velocity, event.timeStamp - finished.time);
    const landing = projectLanding(finished.point, velocity);
    land(host, options.items()[nearestIndex(finished.centers, landing)]);
  }

  function land(host: HTMLElement, target: HTMLElement): void {
    swallowUntil = performance.now() + SWALLOW_MS;
    controls.moveTo(boxOf(target, host), DROP_MOTION);
    controls.shimmer();
    options.select(target);
    navigator.vibrate?.(GRAB_BUZZ_MS);
  }

  function click(event: MouseEvent): void {
    if (performance.now() < swallowUntil) {
      swallowUntil = 0;
      event.preventDefault();
      event.stopPropagation();
    }
  }

  function blockScroll(event: TouchEvent): void {
    if (grab?.touch && event.cancelable) {
      event.preventDefault();
    }
  }

  function contextMenu(event: Event): void {
    if (grab?.touch || hold) {
      event.preventDefault();
    }
  }

  watch(
    track,
    (host, previous) => {
      previous?.removeEventListener("touchmove", blockScroll);
      host?.addEventListener("touchmove", blockScroll, { passive: false });
    },
    { immediate: true },
  );

  onBeforeUnmount(() => {
    cancelAnimationFrame(frame);
    cancelHold();
    cancelAnimationFrame(scrolling);
    track.value?.removeEventListener("touchmove", blockScroll);
  });

  return { down, move, up, click, contextMenu };
}
