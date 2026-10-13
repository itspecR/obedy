<script setup lang="ts">
import { KIND_LABELS, rangeText } from "../absences/absences";
import MoreMenu, { type MenuItem } from "../ui/MoreMenu.vue";
import StatusBadge from "../ui/StatusBadge.vue";
import type { RosterRow } from "./groups";

defineProps<{ title: string; rows: RosterRow[]; badge: string }>();
const emit = defineEmits<{ select: [row: RosterRow, key: string] }>();

const PRESENT_ACTIONS: MenuItem[] = [
  { key: "lunch", label: "Добавить обед" },
  { key: "absence", label: "Отметить отсутствие" },
];
const ABSENT_ACTIONS: MenuItem[] = [{ key: "edit-absence", label: "Изменить отсутствие" }];
</script>

<template>
  <section class="panel roster" :aria-label="title">
    <h2 class="roster__title">
      {{ title }} <span class="roster__count numeric">{{ rows.length }}</span>
    </h2>
    <ul class="roster__rows">
      <li v-for="row in rows" :key="row.person.id" class="roster__row">
        <div class="roster__who">
          <span class="roster__name">{{ row.person.name }}</span>
          <span class="roster__details">{{ row.absence ? rangeText(row.absence.first, row.absence.last) : row.person.login }}</span>
        </div>
        <StatusBadge tone="neutral" :label="row.absence ? KIND_LABELS[row.absence.kind] : badge" />
        <MoreMenu :label="`Действия: ${row.person.name}`" :items="row.absence ? ABSENT_ACTIONS : PRESENT_ACTIONS" @select="emit('select', row, $event)" />
      </li>
    </ul>
  </section>
</template>

<style scoped>
.roster {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  padding: 20px 22px;
}

.roster__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-h3);
}

.roster__count {
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--gray-bg);
  color: var(--muted);
  font-size: var(--text-small);
}

.roster__rows {
  margin: 0;
  padding: 0;
  list-style: none;
}

.roster__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 36px;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-top: 1px solid var(--line);
}

.roster__who {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.roster__name {
  font-weight: 600;
}

.roster__details {
  font-size: var(--text-small);
  color: var(--muted);
}
</style>
