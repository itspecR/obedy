<script setup lang="ts">
import { ref, useId } from "vue";
import { usePopover } from "../../composables/usePopover";
import { clockNow } from "../../format/dateTime";
import AppIcon from "./AppIcon.vue";
import InfoTip from "./InfoTip.vue";
import TimeWheel from "./TimeWheel.vue";
import { HOURS, MINUTES, WHEEL_ITEM_HEIGHT, clockText, parseClock } from "./timeWheel";

withDefaults(defineProps<{ label: string; hint?: string; disabled?: boolean }>(), { hint: "", disabled: false });
const model = defineModel<string>({ default: "" });

const root = ref<HTMLElement | null>(null);
const { open, alignEnd, show, close, closeOnEscape } = usePopover(root);
const id = useId();
const hours = ref(0);
const minutes = ref(0);

function toggle(): void {
  if (open.value) {
    close();
    return;
  }
  const start = parseClock(model.value) ?? parseClock(clockNow()) ?? { hours: 0, minutes: 0 };
  hours.value = start.hours;
  minutes.value = start.minutes;
  show();
}

function commit(): void {
  model.value = clockText({ hours: hours.value, minutes: minutes.value });
}

function done(): void {
  commit();
  close();
}
</script>

<template>
  <div ref="root" class="time-field" @keydown="closeOnEscape">
    <span class="time-field__head">
      <span :id="`${id}-label`" class="field-label">{{ label }}</span>
      <InfoTip v-if="hint" :text="hint" :label="label" />
    </span>
    <button
      type="button"
      class="field-control"
      :class="{ 'field-control--open': open }"
      :aria-labelledby="`${id}-label ${id}-value`"
      aria-haspopup="dialog"
      :aria-expanded="open"
      :disabled="disabled"
      @click="toggle"
    >
      <span :id="`${id}-value`" class="numeric" :class="{ 'field-placeholder': !model }">{{ model || "--:--" }}</span>
      <AppIcon name="clock" class="time-field__icon" />
    </button>
    <div v-if="open" class="popover time-field__panel" :class="{ 'popover--end': alignEnd }" role="dialog" :aria-label="label">
      <div class="time-field__wheels" :style="{ '--wheel-item': `${WHEEL_ITEM_HEIGHT}px` }">
        <span class="time-field__band" aria-hidden="true" />
        <TimeWheel v-model="hours" :values="HOURS" label="Часы" @update:model-value="commit" />
        <span class="time-field__colon" aria-hidden="true">:</span>
        <TimeWheel v-model="minutes" :values="MINUTES" label="Минуты" @update:model-value="commit" />
      </div>
      <button type="button" class="time-field__done" @click="done">Готово</button>
    </div>
  </div>
</template>

<style scoped>
.time-field {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.time-field__icon {
  color: var(--muted);
}

.time-field__head {
  display: flex;
  align-items: center;
  gap: 6px;
}

.time-field__panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 200px;
}

.time-field__wheels {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
}

.time-field__band {
  position: absolute;
  top: 50%;
  right: 0;
  left: 0;
  height: var(--wheel-item);
  border-radius: var(--radius-button);
  background: var(--blue-tint);
  transform: translateY(-50%);
}

.time-field__colon {
  position: relative;
  z-index: 1;
  font-size: 22px;
  font-weight: 600;
}

.time-field__done {
  padding: 8px;
  border: 0;
  border-radius: var(--radius-button);
  background: transparent;
  color: var(--blue);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.time-field__done:hover {
  background: var(--hover);
}
</style>
