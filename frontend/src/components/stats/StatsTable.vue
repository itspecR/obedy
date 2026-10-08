<script setup lang="ts">
import type { PersonStats } from "../../api/stats";

defineProps<{ people: PersonStats[] }>();

const minutes = (value: number | null) => (value === null ? "—" : `${value} мин`);
</script>

<template>
  <section class="panel stats-table" aria-label="Сотрудники">
    <div class="stats-table__head" aria-hidden="true">
      <span>Сотрудник</span>
      <span>Обедов</span>
      <span>Нарушений</span>
      <span>Превышений</span>
      <span>Без возврата</span>
      <span>В среднем</span>
      <span>Перебор</span>
    </div>
    <ul v-if="people.length" class="stats-table__rows">
      <li v-for="person in people" :key="person.id" class="stats-table__row" :class="{ 'stats-table__row--alarm': person.violations > 0 }">
        <div class="stats-table__who">
          <span class="stats-table__name">{{ person.name }}</span>
          <span class="stats-table__details">{{ person.login }}</span>
        </div>
        <span class="stats-table__cell numeric" data-label="Обедов">{{ person.count }}</span>
        <span class="stats-table__cell stats-table__violations numeric" data-label="Нарушений">{{ person.violations }}</span>
        <span class="stats-table__cell numeric" data-label="Превышений">{{ person.overruns }}</span>
        <span class="stats-table__cell numeric" data-label="Без возврата">{{ person.unreturned }}</span>
        <span class="stats-table__cell numeric" data-label="В среднем">{{ minutes(person.average_minutes) }}</span>
        <span class="stats-table__cell numeric" data-label="Перебор">{{ person.overrun_minutes ? minutes(person.overrun_minutes) : "—" }}</span>
      </li>
    </ul>
    <p v-else class="stats-table__empty">За этот период обедов нет. Выберите другой период или отдел.</p>
  </section>
</template>

<style scoped>
.stats-table {
  padding: 8px 24px 12px;
}

.stats-table__head,
.stats-table__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) repeat(6, 96px);
  align-items: center;
  gap: 4px 12px;
}

.stats-table__head {
  padding: 12px 0;
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--muted);
  text-align: right;
}

.stats-table__head span:first-child {
  text-align: left;
}

.stats-table__rows {
  margin: 0;
  padding: 0;
  list-style: none;
}

.stats-table__row {
  padding: 10px 0;
  border-top: 1px solid var(--line);
}

.stats-table__who {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.stats-table__name {
  font-weight: 600;
}

.stats-table__details {
  font-size: var(--text-small);
  color: var(--muted);
}

.stats-table__cell {
  text-align: right;
}

.stats-table__violations {
  color: var(--muted);
}

.stats-table__row--alarm .stats-table__violations {
  font-weight: 600;
  color: var(--red);
}

.stats-table__empty {
  margin: 0;
  padding: 20px 0;
  text-align: center;
  color: var(--muted);
}

@media (max-width: 900px) {
  .stats-table {
    padding: 4px 16px 8px;
  }

  .stats-table__head {
    display: none;
  }

  .stats-table__row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    padding: 14px 0;
  }

  .stats-table__who {
    grid-column: 1 / -1;
    margin-bottom: 4px;
  }

  .stats-table__cell {
    display: flex;
    flex-direction: column;
    text-align: left;
  }

  .stats-table__cell::before {
    content: attr(data-label);
    font-size: var(--text-small);
    font-weight: 400;
    color: var(--muted);
  }
}
</style>
