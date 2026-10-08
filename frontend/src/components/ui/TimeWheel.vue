<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { WHEEL_ITEM_HEIGHT, WHEEL_VISIBLE_ITEMS, indexAt, twoDigits } from "./timeWheel";

const SETTLE_MS = 90;

const props = defineProps<{ values: number[]; label: string }>();
const model = defineModel<number>({ required: true });

const list = ref<HTMLElement | null>(null);
let settle: number | undefined;

function scrollToValue(value: number, behavior: ScrollBehavior): void {
  list.value?.scrollTo({ top: props.values.indexOf(value) * WHEEL_ITEM_HEIGHT, behavior });
}

function choose(value: number): void {
  model.value = value;
  scrollToValue(value, "smooth");
}

function onScroll(): void {
  window.clearTimeout(settle);
  settle = window.setTimeout(() => {
    const value = props.values[indexAt(list.value?.scrollTop ?? 0, props.values.length)];
    if (value !== model.value) {
      model.value = value;
    }
  }, SETTLE_MS);
}

function step(delta: number): void {
  const index = props.values.indexOf(model.value) + delta;
  if (index >= 0 && index < props.values.length) {
    choose(props.values[index]);
  }
}

function onKey(event: KeyboardEvent): void {
  const deltas: Record<string, number> = { ArrowUp: -1, ArrowDown: 1 };
  if (event.key in deltas) {
    event.preventDefault();
    step(deltas[event.key]);
  }
}

watch(model, (value) => {
  if (list.value && props.values[indexAt(list.value.scrollTop, props.values.length)] !== value) {
    scrollToValue(value, "smooth");
  }
});

onMounted(() => scrollToValue(model.value, "instant"));
onBeforeUnmount(() => window.clearTimeout(settle));
</script>

<template>
  <div
    ref="list"
    class="wheel"
    role="spinbutton"
    tabindex="0"
    :aria-label="label"
    :aria-valuenow="model"
    :aria-valuemin="values[0]"
    :aria-valuemax="values[values.length - 1]"
    :aria-valuetext="twoDigits(model)"
    :style="{ '--wheel-item': `${WHEEL_ITEM_HEIGHT}px`, '--wheel-visible': WHEEL_VISIBLE_ITEMS }"
    @scroll="onScroll"
    @keydown="onKey"
  >
    <div class="wheel__pad" />
    <div v-for="value in values" :key="value" class="wheel__item numeric" :class="{ 'wheel__item--chosen': value === model }" @click="choose(value)">
      {{ twoDigits(value) }}
    </div>
    <div class="wheel__pad" />
  </div>
</template>

<style scoped>
.wheel {
  position: relative;
  z-index: 1;
  height: calc(var(--wheel-item) * var(--wheel-visible));
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  scrollbar-width: none;
  outline: none;
  mask-image: linear-gradient(to bottom, transparent, black 30%, black 70%, transparent);
  -webkit-mask-image: linear-gradient(to bottom, transparent, black 30%, black 70%, transparent);
}

.wheel::-webkit-scrollbar {
  display: none;
}

.wheel:focus-visible {
  border-radius: var(--radius-button);
  box-shadow: inset 0 0 0 2px var(--focus);
}

.wheel__pad {
  height: calc(var(--wheel-item) * (var(--wheel-visible) - 1) / 2);
}

.wheel__item {
  display: grid;
  place-items: center;
  height: var(--wheel-item);
  scroll-snap-align: center;
  color: var(--muted);
  font-size: 20px;
  cursor: pointer;
  transition: color var(--motion), font-size var(--motion);
}

.wheel__item--chosen {
  color: var(--ink);
  font-size: 24px;
  font-weight: 600;
}
</style>
