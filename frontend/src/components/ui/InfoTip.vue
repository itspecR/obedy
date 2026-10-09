<script setup lang="ts">
import { ref, useId } from "vue";
import { usePopover } from "../../composables/usePopover";

const PANEL_WIDTH = 280;
const SCREEN_MARGIN = 16;
const CLIPPING_OVERFLOW = ["auto", "scroll", "hidden", "clip"];

const props = defineProps<{ text: string; label?: string }>();

const root = ref<HTMLElement | null>(null);
const { open, close, show, closeOnEscape } = usePopover(root);
const id = useId();
const place = ref({ left: "0px", width: `${PANEL_WIDTH}px` });

function clipsContent(element: HTMLElement): boolean {
  return CLIPPING_OVERFLOW.includes(getComputedStyle(element).overflowX);
}

function boundsOf(element: HTMLElement): { left: number; right: number } {
  let parent = element.parentElement;
  while (parent && parent !== document.body && !clipsContent(parent)) {
    parent = parent.parentElement;
  }
  const box = parent && parent !== document.body ? parent.getBoundingClientRect() : null;
  return { left: Math.max(box?.left ?? 0, 0), right: Math.min(box?.right ?? window.innerWidth, window.innerWidth) };
}

function measure(): void {
  const element = root.value;
  if (!element) {
    return;
  }
  const rect = element.getBoundingClientRect();
  const bounds = boundsOf(element);
  const width = Math.min(PANEL_WIDTH, bounds.right - bounds.left - SCREEN_MARGIN * 2);
  const centered = rect.left + rect.width / 2 - width / 2;
  const left = Math.min(Math.max(centered, bounds.left + SCREEN_MARGIN), bounds.right - SCREEN_MARGIN - width);
  place.value = { left: `${left - rect.left}px`, width: `${width}px` };
}

function toggle(): void {
  if (open.value) {
    close();
    return;
  }
  measure();
  show();
}
</script>

<template>
  <span ref="root" class="info" @keydown="closeOnEscape">
    <button
      type="button"
      class="info__button"
      :aria-label="props.label ? `Подсказка: ${props.label}` : 'Подсказка'"
      :aria-expanded="open"
      :aria-controls="`${id}-tip`"
      @click.stop.prevent="toggle"
    >
      i
    </button>
    <span v-if="open" :id="`${id}-tip`" class="popover info__panel" role="note" :style="place">{{ text }}</span>
  </span>
</template>

<style scoped>
.info {
  position: relative;
  display: inline-flex;
  flex: none;
  vertical-align: middle;
}

.info__button {
  display: inline-grid;
  place-content: center;
  width: 18px;
  height: 18px;
  padding: 0;
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  background: transparent;
  color: var(--muted);
  font: 600 11px / 1 var(--font-sans);
  font-style: italic;
  cursor: pointer;
  transition: color var(--motion), border-color var(--motion), background var(--motion);
}

.info__button:hover,
.info__button[aria-expanded="true"] {
  border-color: var(--blue);
  background: var(--blue-tint);
  color: var(--ink);
}

.info__button:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

.info__panel {
  font-size: var(--text-small);
  font-weight: 400;
  line-height: 1.45;
  color: var(--ink);
  text-align: left;
  text-transform: none;
  letter-spacing: normal;
  white-space: normal;
}
</style>
