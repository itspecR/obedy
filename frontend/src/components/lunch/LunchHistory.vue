<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { errorMessage } from "../../api/http";
import { fetchLunchHistory, type LunchHistory } from "../../api/lunch";
import { useToasts } from "../../composables/useToasts";
import { formatDateTime, formatDay, formatMonth } from "../../format/dateTime";
import AppButton from "../ui/AppButton.vue";
import StatusBadge from "../ui/StatusBadge.vue";
import { LUNCH_STATUS, correctionLabel, lunchDuration, lunchRange } from "./lunchStatus";
import { shiftMonth } from "../../format/calendar";

const props = defineProps<{ revision: number }>();

const history = ref<LunchHistory | null>(null);
const latest = ref("");
const loading = ref(false);
const { fail } = useToasts();

const month = computed(() => history.value?.month ?? "");
const isLatest = computed(() => month.value === latest.value);
const summary = computed(() => history.value?.summary);

async function load(target: string): Promise<void> {
  loading.value = true;
  try {
    history.value = await fetchLunchHistory(target);
    latest.value ||= history.value.month;
  } catch (error) {
    fail(errorMessage(error, "Не удалось загрузить историю обедов. Обновите страницу"));
  } finally {
    loading.value = false;
  }
}


onMounted(() => load(""));
watch(
  () => props.revision,
  () => load(month.value),
);
</script>

<template>
  <section class="panel history" aria-labelledby="history-title">
    <header class="history__head">
      <h2 id="history-title" class="history__title">История</h2>
      <div v-if="history" class="history__months">
        <AppButton variant="ghost" size="small" aria-label="Предыдущий месяц" :disabled="loading" @click="load(shiftMonth(month, -1))">‹</AppButton>
        <span class="history__month">{{ formatMonth(month) }}</span>
        <AppButton variant="ghost" size="small" aria-label="Следующий месяц" :disabled="loading || isLatest" @click="load(shiftMonth(month, 1))">›</AppButton>
      </div>
    </header>

    <dl v-if="summary" class="history__summary">
      <div class="history__tile">
        <dt>Обедов</dt>
        <dd class="numeric">{{ summary.count }}</dd>
      </div>
      <div class="history__tile" :class="{ 'history__tile--alarm': summary.violations > 0 }">
        <dt>Нарушений</dt>
        <dd class="numeric">{{ summary.violations }}</dd>
      </div>
      <div class="history__tile">
        <dt>В среднем</dt>
        <dd class="numeric">{{ summary.average_minutes === null ? "—" : `${summary.average_minutes} мин` }}</dd>
      </div>
    </dl>

    <ul v-if="history && history.lunches.length" class="history__list">
      <li v-for="lunch in history.lunches" :key="lunch.id" class="history__row">
        <span class="history__day">{{ formatDay(lunch.day) }}</span>
        <span class="history__range numeric">{{ lunchRange(lunch) }}</span>
        <span class="history__duration numeric">{{ lunchDuration(lunch) }}</span>
        <StatusBadge class="history__status" :tone="LUNCH_STATUS[lunch.status].tone" :label="LUNCH_STATUS[lunch.status].label" />
        <p v-if="lunch.correction" class="history__correction">
          {{ correctionLabel(lunch.correction) }}: {{ lunch.correction.by }}, {{ formatDateTime(lunch.correction.at) }}. Причина: {{ lunch.correction.reason }}
        </p>
      </li>
    </ul>
    <p v-else-if="history" class="history__empty">В этом месяце обедов не отмечено.</p>
  </section>
</template>

<style scoped>
.history {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px 24px;
}

.history__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.history__title {
  font-size: var(--text-h3);
}

.history__months {
  display: flex;
  align-items: center;
  gap: 4px;
}

.history__month {
  min-width: 128px;
  text-align: center;
  font-weight: 600;
}

.history__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 0;
}

.history__tile {
  padding: 12px 14px;
  border: 1px solid var(--gray-line);
  border-radius: var(--radius-button);
  background: var(--gray-bg);
}

.history__tile dt {
  font-size: var(--text-small);
  color: var(--muted);
}

.history__tile dd {
  margin: 4px 0 0;
  font-size: var(--text-h2);
  font-weight: 600;
}

.history__tile--alarm {
  border-color: var(--red-line);
  background: var(--red-bg);
}

.history__tile--alarm dd {
  color: var(--red);
}

.history__list {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  list-style: none;
}

.history__row {
  display: grid;
  grid-template-columns: 96px 1fr 72px 168px;
  align-items: center;
  gap: 4px 12px;
  padding: 10px 0;
  border-top: 1px solid var(--line);
}

.history__day {
  color: var(--muted);
}

.history__duration {
  text-align: right;
}

.history__status {
  justify-self: end;
}

.history__correction {
  grid-column: 1 / -1;
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.history__empty {
  margin: 0;
  padding: 16px 0 4px;
  text-align: center;
  color: var(--muted);
}

@media (max-width: 560px) {
  .history {
    padding: 18px 16px;
  }

  .history__row {
    grid-template-columns: 1fr auto;
  }

  .history__duration {
    text-align: left;
  }
}
</style>
