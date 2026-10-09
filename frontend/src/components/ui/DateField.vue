<script setup lang="ts">
import { computed, ref, useId } from "vue";
import { usePopover } from "../../composables/usePopover";
import { WEEKDAY_SHORT, monthGrid, monthOf, shiftMonth } from "../../format/calendar";
import { formatFullDay, formatMonth, todayIso } from "../../format/dateTime";
import AppIcon from "./AppIcon.vue";

const props = withDefaults(defineProps<{ label: string; max?: string; hideLabel?: boolean; disabled?: boolean }>(), {
  max: undefined,
  hideLabel: false,
  disabled: false,
});
const model = defineModel<string>({ default: "" });
const emit = defineEmits<{ change: [day: string] }>();

const root = ref<HTMLElement | null>(null);
const { open, place, show, close, closeOnEscape } = usePopover(root);
const id = useId();
const today = todayIso();
const viewMonth = ref(monthOf(model.value || props.max || today));

const days = computed(() => monthGrid(viewMonth.value));
const isLatestMonth = computed(() => Boolean(props.max && viewMonth.value >= monthOf(props.max)));
const isTooLate = (day: string) => Boolean(props.max && day > props.max);

function toggle(): void {
  if (open.value) {
    close();
    return;
  }
  viewMonth.value = monthOf(model.value || props.max || today);
  show();
}

function pick(day: string): void {
  if (isTooLate(day)) {
    return;
  }
  model.value = day;
  emit("change", day);
  close();
}
</script>

<template>
  <div ref="root" class="date-field" @keydown="closeOnEscape">
    <span :id="`${id}-label`" class="field-label" :class="{ 'visually-hidden': hideLabel }">{{ label }}</span>
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
      <span :id="`${id}-value`" class="numeric" :class="{ 'field-placeholder': !model }">{{ model ? formatFullDay(model) : "дд.мм.гггг" }}</span>
      <AppIcon name="calendar" class="date-field__icon" />
    </button>
    <div v-if="open" class="popover date-field__panel" :style="place" role="dialog" :aria-label="label">
      <div class="date-field__head">
        <button type="button" class="date-field__nav" aria-label="Предыдущий месяц" @click="viewMonth = shiftMonth(viewMonth, -1)">‹</button>
        <span class="date-field__month">{{ formatMonth(viewMonth) }}</span>
        <button type="button" class="date-field__nav" aria-label="Следующий месяц" :disabled="isLatestMonth" @click="viewMonth = shiftMonth(viewMonth, 1)">›</button>
      </div>
      <div class="date-field__grid">
        <span v-for="weekday in WEEKDAY_SHORT" :key="weekday" class="date-field__weekday">{{ weekday }}</span>
        <button
          v-for="cell in days"
          :key="cell.day"
          type="button"
          class="date-field__day numeric"
          :class="{ 'date-field__day--other': !cell.inMonth, 'date-field__day--today': cell.day === today, 'date-field__day--chosen': cell.day === model }"
          :aria-label="formatFullDay(cell.day)"
          :aria-pressed="cell.day === model"
          :disabled="isTooLate(cell.day)"
          @click="pick(cell.day)"
        >
          {{ Number(cell.day.slice(8)) }}
        </button>
      </div>
      <div class="date-field__foot">
        <button type="button" class="date-field__today" :disabled="isTooLate(today)" @click="pick(today)">Сегодня</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.date-field {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.date-field__icon {
  color: var(--muted);
}

.date-field__panel {
  width: 300px;
}

.date-field__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.date-field__month {
  font-weight: 600;
}

.date-field__nav,
.date-field__day,
.date-field__today {
  border: 1px solid transparent;
  background: transparent;
  color: var(--ink);
  font: inherit;
  cursor: pointer;
  transition: background var(--motion), color var(--motion), border-color var(--motion);
}

.date-field__nav {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-button);
  color: var(--blue);
  font-size: 20px;
}

.date-field__grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 2px;
}

.date-field__weekday {
  padding: 4px 0;
  font-size: var(--text-small);
  text-align: center;
  color: var(--muted);
}

.date-field__day {
  height: 36px;
  border-radius: var(--radius-button);
}

.date-field__nav:hover:not(:disabled),
.date-field__day:hover:not(:disabled),
.date-field__today:hover:not(:disabled) {
  background: var(--hover);
}

.date-field__day--other {
  color: var(--muted);
}

.date-field__day--today {
  border-color: var(--line-strong);
}

.date-field__day--chosen,
.date-field__day--chosen:hover:not(:disabled) {
  border-color: var(--blue);
  background: var(--blue-tint);
  color: var(--blue-hover);
  font-weight: 600;
}

.date-field__nav:disabled,
.date-field__day:disabled,
.date-field__today:disabled {
  opacity: 0.3;
  cursor: default;
}

.date-field__foot {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.date-field__today {
  padding: 6px 10px;
  border-radius: var(--radius-button);
  color: var(--blue);
}
</style>
