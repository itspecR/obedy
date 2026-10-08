<script setup lang="ts">
import { computed } from "vue";
import type { LunchState } from "../../api/lunch";
import { formatTime } from "../../format/dateTime";
import AppButton from "../ui/AppButton.vue";
import StatusBadge from "../ui/StatusBadge.vue";
import { countdownText, countdownTone, formatClock, formatMinutes, remainingSeconds, returnBy, secondsUntil } from "./countdown";
import { LUNCH_STATUS, MEASURED_STATUSES } from "./lunchStatus";

const props = defineProps<{ state: LunchState; now: number; busy: boolean }>();
const emit = defineEmits<{ start: []; finish: []; undo: [] }>();

const today = computed(() => props.state.today);
const ongoing = computed(() => today.value?.status === "ongoing");
const remaining = computed(() => (today.value ? remainingSeconds(today.value.started_at, today.value.limit_minutes, props.now) : 0));
const tone = computed(() => countdownTone(remaining.value, props.state.warning_minutes));
const undoLeft = computed(() => (props.state.undo_until ? secondsUntil(props.state.undo_until, props.now) : 0));
const deadline = computed(() => (today.value ? formatTime(returnBy(today.value.started_at, today.value.limit_minutes)) : ""));
const finishedRange = computed(() => (today.value?.ended_at ? `${formatTime(today.value.started_at)}–${formatTime(today.value.ended_at)}` : ""));
const finishedDuration = computed(() => (today.value && MEASURED_STATUSES.includes(today.value.status) ? ` · ${formatMinutes(today.value.duration_seconds)}` : ""));
</script>

<template>
  <section class="panel control" aria-label="Отметка обеда">
    <template v-if="!state.tracked">
      <p class="control__title">{{ state.refusal }}</p>
      <p class="control__note">Если это ошибка — обратитесь к администратору.</p>
    </template>

    <template v-else-if="today && ongoing">
      <p class="control__label">{{ remaining < 0 ? "Время обеда вышло" : "До конца обеда" }}</p>
      <p class="control__clock numeric" :class="`control__clock--${tone}`" role="timer">{{ countdownText(remaining) }}</p>
      <p class="control__note">Ушли в {{ formatTime(today.started_at) }} · вернуться до {{ deadline }}</p>
      <AppButton class="control__main" variant="primary" block :disabled="busy" @click="emit('finish')">Вернулся</AppButton>
      <AppButton v-if="undoLeft > 0" variant="ghost" size="small" :disabled="busy" @click="emit('undo')">
        Ушли по ошибке? Отменить · <span class="numeric">{{ formatClock(undoLeft) }}</span>
      </AppButton>
    </template>

    <template v-else-if="today">
      <p class="control__title">Сегодня обед уже отмечен</p>
      <p class="control__note numeric">{{ finishedRange }}{{ finishedDuration }}</p>
      <StatusBadge :tone="LUNCH_STATUS[today.status].tone" :label="LUNCH_STATUS[today.status].label" />
    </template>

    <template v-else-if="state.can_start">
      <AppButton class="control__main" variant="primary" block :disabled="busy" @click="emit('start')">Ушёл на обед</AppButton>
      <p class="control__note">Лимит — {{ state.limit_minutes }} мин. Отменить отметку можно в первые {{ formatMinutes(state.undo_seconds) }}.</p>
    </template>

    <template v-else>
      <p class="control__title">{{ state.refusal }}</p>
      <p class="control__note">Сейчас отметить обед нельзя.</p>
    </template>
  </section>
</template>

<style scoped>
.control {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 24px;
  text-align: center;
}

.control__title {
  margin: 0;
  font-size: var(--text-h3);
  font-weight: 600;
}

.control__label {
  margin: 0;
  font-size: var(--text-small);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}

.control__clock {
  margin: 0;
  font-family: var(--font-display);
  font-size: 56px;
  font-weight: 600;
  line-height: 1.1;
}

.control__clock--ok {
  color: var(--green);
}

.control__clock--attention {
  color: var(--amber);
}

.control__clock--alarm {
  font-size: 36px;
  color: var(--red);
}

.control__note {
  margin: 0;
  color: var(--muted);
}

.control__main {
  max-width: 320px;
  min-height: 52px;
  font-size: var(--text-h3);
}

@media (max-width: 560px) {
  .control {
    padding: 28px 16px;
  }

  .control__clock--alarm {
    font-size: 26px;
  }
}
</style>
