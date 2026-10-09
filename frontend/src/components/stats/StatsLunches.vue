<script setup lang="ts">
import type { PersonLunch } from "../../api/stats";
import { formatDay } from "../../format/dateTime";
import { LUNCH_STATUS, correctionLabel, lunchDuration, lunchRange } from "../lunch/lunchStatus";
import StatusBadge from "../ui/StatusBadge.vue";

defineProps<{ lunches: PersonLunch[] }>();
</script>

<template>
  <section class="panel stats-lunches" aria-labelledby="stats-lunches-title">
    <h2 id="stats-lunches-title" class="stats-lunches__title">Обеды по дням</h2>
    <ul v-if="lunches.length" class="stats-lunches__rows">
      <li v-for="item in lunches" :key="item.lunch.id" class="stats-lunches__row">
        <span class="stats-lunches__day">{{ formatDay(item.lunch.day) }}</span>
        <span class="stats-lunches__name">{{ item.name }}</span>
        <span class="stats-lunches__range numeric">{{ lunchRange(item.lunch) }}</span>
        <span class="stats-lunches__duration numeric">{{ lunchDuration(item.lunch) }}</span>
        <StatusBadge class="stats-lunches__status" :tone="LUNCH_STATUS[item.lunch.status].tone" :label="LUNCH_STATUS[item.lunch.status].label" />
        <p v-if="item.lunch.correction" class="stats-lunches__correction">
          {{ correctionLabel(item.lunch.correction) }}: {{ item.lunch.correction.by }}. Причина: {{ item.lunch.correction.reason }}
        </p>
      </li>
    </ul>
    <p v-else class="stats-lunches__empty">У выбранных сотрудников за этот период обедов нет.</p>
  </section>
</template>

<style scoped>
.stats-lunches {
  padding: 18px 24px 12px;
}

.stats-lunches__title {
  margin-bottom: 6px;
  font-size: var(--text-h3);
}

.stats-lunches__rows {
  margin: 0;
  padding: 0;
  list-style: none;
}

.stats-lunches__row {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr) 120px 72px 170px;
  align-items: center;
  gap: 4px 12px;
  padding: 10px 0;
  border-top: 1px solid var(--line);
}

.stats-lunches__day {
  color: var(--muted);
}

.stats-lunches__name {
  min-width: 0;
  overflow: hidden;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stats-lunches__duration {
  text-align: right;
}

.stats-lunches__status {
  justify-self: end;
}

.stats-lunches__correction {
  grid-column: 1 / -1;
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.stats-lunches__empty {
  margin: 0;
  padding: 16px 0;
  text-align: center;
  color: var(--muted);
}

@media (max-width: 900px) {
  .stats-lunches {
    padding: 16px 16px 8px;
  }

  .stats-lunches__row {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .stats-lunches__day {
    grid-column: 1 / -1;
  }

  .stats-lunches__duration,
  .stats-lunches__status {
    justify-self: end;
  }
}
</style>
