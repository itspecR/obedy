<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { errorMessage } from "../api/http";
import { exportStats, fetchStats, type Stats, type StatsQuery } from "../api/stats";
import { PERIOD_PRESETS, samePeriod, thisMonth, type Period, type PeriodPreset } from "../components/stats/period";
import StatsTable from "../components/stats/StatsTable.vue";
import AppButton from "../components/ui/AppButton.vue";
import PageHeader from "../components/ui/PageHeader.vue";
import TextField from "../components/ui/TextField.vue";
import { saveFile } from "../composables/saveFile";
import { useToasts } from "../composables/useToasts";
import { isoDay } from "../format/dateTime";
import { matchesQuery } from "../format/search";

const today = isoDay(new Date());
const period = ref<Period>(thisMonth(today));
const search = ref("");
const stats = ref<Stats | null>(null);
const loadError = ref("");
const loading = ref(false);
const exporting = ref(false);
const { fail } = useToasts();

const query = computed<StatsQuery>(() => ({ date_from: period.value.from, date_to: period.value.to }));
const people = computed(() =>
  (stats.value?.people ?? []).filter((person) => matchesQuery(search.value, [person.name, person.login])),
);
const overview = computed(() => stats.value?.overview);

const minutes = (value: number | null) => (value === null ? "—" : `${value} мин`);
const percent = (value: number | null) => (value === null ? "—" : `${value}%`);

async function load(): Promise<void> {
  if (!period.value.from || !period.value.to) {
    return;
  }
  loading.value = true;
  try {
    stats.value = await fetchStats(query.value);
    loadError.value = "";
  } catch (error) {
    const message = errorMessage(error, "Не удалось загрузить статистику");
    if (stats.value) {
      fail(message);
    } else {
      loadError.value = message;
    }
  } finally {
    loading.value = false;
  }
}

async function download(): Promise<void> {
  exporting.value = true;
  try {
    saveFile(await exportStats(query.value));
  } catch (error) {
    fail(errorMessage(error, "Не удалось выгрузить Excel. Попробуйте ещё раз"));
  } finally {
    exporting.value = false;
  }
}

function choose(preset: PeriodPreset): void {
  period.value = preset.period(today);
}

watch(query, load);
onMounted(load);
</script>

<template>
  <section class="stats">
    <PageHeader title="Статистика" subtitle="Обеды и нарушения за период">
      <AppButton variant="primary" :disabled="exporting || !stats" @click="download">{{ exporting ? "Готовим файл…" : "Скачать Excel" }}</AppButton>
    </PageHeader>

    <div class="panel stats__filters">
      <div class="stats__presets" role="group" aria-label="Быстрый выбор периода">
        <AppButton v-for="preset in PERIOD_PRESETS" :key="preset.key" size="small" :pressed="samePeriod(period, preset.period(today))" @click="choose(preset)">
          {{ preset.label }}
        </AppButton>
      </div>
      <div class="stats__fields">
        <TextField v-model="period.from" label="С" type="date" :max="today" plain />
        <TextField v-model="period.to" label="По" type="date" :max="today" plain />
        <TextField v-model="search" label="Поиск" icon="search" placeholder="например: Иванов" plain />
      </div>
      <p class="stats__note">Период — не больше года. Нарушения — превышение лимита и неотмеченный возврат.</p>
    </div>

    <div v-if="loadError" class="panel stats__message" role="alert">
      <p class="stats__error">{{ loadError }}</p>
      <AppButton @click="load">Повторить</AppButton>
    </div>
    <div v-else-if="!stats" class="panel stats__message" aria-busy="true">Загружаем…</div>
    <template v-else>
      <dl v-if="overview" class="stats__overview" :aria-busy="loading">
        <div class="panel stats__tile">
          <dt>Обедов</dt>
          <dd class="numeric">{{ overview.count }}</dd>
        </div>
        <div class="panel stats__tile" :class="{ 'stats__tile--alarm': overview.violations > 0 }">
          <dt>Нарушений</dt>
          <dd class="numeric">{{ overview.violations }}</dd>
        </div>
        <div class="panel stats__tile">
          <dt>В среднем</dt>
          <dd class="numeric">{{ minutes(overview.average_minutes) }}</dd>
        </div>
        <div class="panel stats__tile">
          <dt>Вовремя</dt>
          <dd class="numeric">{{ percent(overview.on_time_percent) }}</dd>
        </div>
        <div class="panel stats__tile">
          <dt>Сотрудников</dt>
          <dd class="numeric">{{ overview.people }}</dd>
        </div>
      </dl>
      <StatsTable :people="people" />
    </template>
  </section>
</template>

<style scoped>
.stats {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats__filters {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 20px;
}

.stats__presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stats__fields {
  display: grid;
  grid-template-columns: 180px 180px minmax(0, 1fr);
  gap: 12px;
}

.stats__note {
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.stats__overview {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin: 0;
}

.stats__tile {
  padding: 14px 18px;
}

.stats__tile dt {
  font-size: var(--text-small);
  color: var(--muted);
}

.stats__tile dd {
  margin: 4px 0 0;
  font-size: var(--text-h2);
  font-weight: 600;
}

.stats__tile--alarm {
  border-color: var(--red-line);
  background: var(--red-bg);
}

.stats__tile--alarm dd {
  color: var(--red);
}

.stats__message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 32px 24px;
  color: var(--muted);
}

.stats__message p {
  margin: 0;
}

.stats__error {
  color: var(--red);
}

@media (max-width: 1100px) {
  .stats__fields {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .stats__overview {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 650px) {
  .stats__filters {
    padding: 16px;
  }

  .stats__fields {
    grid-template-columns: minmax(0, 1fr);
  }

  .stats__overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
