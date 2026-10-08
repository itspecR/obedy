import { nextTick, onBeforeUnmount, onMounted, watch, type Ref, type WatchSource } from "vue";
import { leanOf, nextIndex, NO_LEAN, revealScroll, type Axis, type Lean } from "../components/ui/glass";
import { useGlassDrag } from "./useGlassDrag";
import { useGlassPill } from "./useGlassPill";

export interface GlassNavOptions {
  items: string;
  isActive: (item: HTMLElement) => boolean;
  select: (item: HTMLElement) => void;
  changes: WatchSource;
  area?: Ref<HTMLElement | null>;
}

export function useGlassNav(nav: Ref<HTMLElement | null>, options: GlassNavOptions) {
  const active = useGlassPill(nav);
  const hovered = useGlassPill(nav);
  const drag = useGlassDrag(nav, active, {
    items: links,
    grabNow: (item) => options.isActive(item),
    select: options.select,
    settle: () => placeActive(),
  });
  let resize: ResizeObserver | null = null;
  let frame = 0;
  let pending: PointerEvent | null = null;

  function links(): HTMLElement[] {
    return Array.from(nav.value?.querySelectorAll<HTMLElement>(options.items) ?? []);
  }

  function itemAt(target: EventTarget | null): HTMLElement | null {
    return links().find((item) => item.contains(target as Node)) ?? null;
  }

  function placeActive(instant = false): void {
    const item = links().find(options.isActive) ?? null;
    active.place(item, instant);
    reveal(item, instant);
  }

  function reveal(item: HTMLElement | null, instant: boolean): void {
    const host = nav.value;
    if (!host || !item || axisOf(host) !== "x" || host.scrollWidth <= host.clientWidth) {
      return;
    }
    const left = revealScroll(item.offsetLeft, item.offsetWidth, host.scrollLeft, host.clientWidth, host.scrollWidth);
    if (left !== null) {
      host.scrollTo({ left, behavior: instant ? "auto" : "smooth" });
    }
  }

  function measure(): void {
    const host = nav.value;
    if (host) {
      host.style.setProperty("--nav-w", `${host.clientWidth}px`);
      host.style.setProperty("--nav-h", `${host.clientHeight}px`);
    }
    placeActive(!active.pill.shown);
  }

  function applyLean(lean: Lean): void {
    active.pill.offset = lean.offset;
    active.pill.scale = lean.scale;
    active.pill.angle = lean.angle;
  }

  function over(event: PointerEvent): void {
    if (!active.pill.lifted) {
      hovered.place(itemAt(event.target));
    }
  }

  function track(event: PointerEvent): void {
    if (event.pointerType !== "mouse") {
      return;
    }
    pending = event;
    if (!frame) {
      frame = requestAnimationFrame(light);
    }
  }

  function light(): void {
    frame = 0;
    const host = nav.value;
    const event = pending;
    if (!host || !event) {
      return;
    }
    const rect = host.getBoundingClientRect();
    const point = { x: event.clientX - rect.left + host.scrollLeft, y: event.clientY - rect.top + host.scrollTop };
    host.style.setProperty("--mx", `${point.x}px`);
    host.style.setProperty("--my", `${point.y}px`);
    if (!active.pill.lifted && active.pill.box) {
      applyLean(leanOf(point, active.pill.box, host));
    }
  }

  function move(event: PointerEvent): void {
    if (!options.area) {
      track(event);
    }
    drag.move(event);
  }

  function leave(): void {
    hovered.place(null);
    if (!options.area) {
      rest();
    }
  }

  function rest(): void {
    pending = null;
    if (!active.pill.lifted) {
      applyLean(NO_LEAN);
    }
  }

  function axisOf(host: HTMLElement): Axis {
    return getComputedStyle(host).flexDirection.startsWith("row") ? "x" : "y";
  }

  function keydown(event: KeyboardEvent): void {
    const host = nav.value;
    const all = links();
    const current = all.indexOf(document.activeElement as HTMLElement);
    if (!host || current < 0) {
      return;
    }
    const next = nextIndex(current, event.key, axisOf(host), all.length);
    if (next !== null) {
      event.preventDefault();
      all[next].focus();
    }
  }

  function focusin(event: FocusEvent): void {
    const item = event.target as HTMLElement;
    if (links().includes(item) && item.matches(":focus-visible")) {
      hovered.place(item);
    }
  }

  function focusout(): void {
    hovered.place(null);
  }

  function down(event: PointerEvent): void {
    active.pill.offset = NO_LEAN.offset;
    const grabbed = drag.down(event);
    hovered.place(grabbed ? null : itemAt(event.target));
  }

  function up(event: PointerEvent): void {
    drag.up(event);
    if (event.pointerType !== "mouse") {
      hovered.place(null);
    }
  }

  watch(options.changes, () => nextTick(() => placeActive()), { flush: "post" });

  onMounted(() => {
    options.area?.value?.addEventListener("pointermove", track);
    options.area?.value?.addEventListener("pointerleave", rest);
    measure();
    if (nav.value && typeof ResizeObserver !== "undefined") {
      resize = new ResizeObserver(measure);
      resize.observe(nav.value);
    }
  });

  onBeforeUnmount(() => {
    resize?.disconnect();
    cancelAnimationFrame(frame);
    options.area?.value?.removeEventListener("pointermove", track);
    options.area?.value?.removeEventListener("pointerleave", rest);
  });

  return {
    active,
    hovered,
    on: { over, move, leave, down, up, click: drag.click, contextMenu: drag.contextMenu, keydown, focusin, focusout },
  };
}
