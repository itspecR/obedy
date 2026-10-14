import { nextTick, onBeforeUnmount, ref, type CSSProperties, type Ref } from "vue";

export type PopoverAlign = "start" | "end" | "stretch";

const POPOVER_WIDTH_GUESS = 320;
const POPOVER_HEIGHT_GUESS = 340;
const POPOVER_GAP_PX = 6;

function viewport(): { width: number; height: number } {
  const page = document.documentElement;
  return { width: page.clientWidth || window.innerWidth, height: page.clientHeight || window.innerHeight };
}

function vertical(rect: DOMRect, height: number, panelHeight: number): CSSProperties {
  const below = height - rect.bottom;
  if (below < panelHeight + POPOVER_GAP_PX && rect.top > below) {
    return { top: "auto", bottom: `${height - rect.top + POPOVER_GAP_PX}px` };
  }
  return { top: `${rect.bottom + POPOVER_GAP_PX}px`, bottom: "auto" };
}

function horizontal(rect: DOMRect, align: PopoverAlign, width: number): CSSProperties {
  if (align === "stretch") {
    return { left: `${rect.left}px`, right: "auto", width: `${rect.width}px` };
  }
  const atEnd = align === "end" || rect.left + POPOVER_WIDTH_GUESS > width;
  return atEnd ? { left: "auto", right: `${width - rect.right}px` } : { left: `${rect.left}px`, right: "auto" };
}

export function placementFor(rect: DOMRect, align: PopoverAlign, panelHeight = POPOVER_HEIGHT_GUESS): CSSProperties {
  const { width, height } = viewport();
  return { position: "fixed", ...vertical(rect, height, panelHeight), ...horizontal(rect, align, width) };
}

export function usePopover(root: Ref<HTMLElement | null>, align: PopoverAlign = "start") {
  const open = ref(false);
  const place = ref<CSSProperties>({});

  function panelHeight(): number {
    return root.value?.querySelector<HTMLElement>(".popover")?.offsetHeight || POPOVER_HEIGHT_GUESS;
  }

  function measure(): void {
    const rect = root.value?.getBoundingClientRect();
    if (rect) {
      place.value = placementFor(rect, align, panelHeight());
    }
  }

  function onOutside(event: Event): void {
    if (root.value && !root.value.contains(event.target as Node)) {
      close();
    }
  }

  function show(): void {
    measure();
    open.value = true;
    void nextTick(measure);
    document.addEventListener("pointerdown", onOutside);
    document.addEventListener("scroll", measure, true);
    window.addEventListener("resize", measure);
  }

  function close(): void {
    open.value = false;
    document.removeEventListener("pointerdown", onOutside);
    document.removeEventListener("scroll", measure, true);
    window.removeEventListener("resize", measure);
  }

  function toggle(): void {
    if (open.value) {
      close();
    } else {
      show();
    }
  }

  function closeOnEscape(event: KeyboardEvent): void {
    if (event.key === "Escape" && open.value) {
      event.stopPropagation();
      close();
    }
  }

  onBeforeUnmount(close);

  return { open, place, show, close, toggle, closeOnEscape };
}
