<script setup lang="ts">
import type { BoardEntry } from "../../api/board";
import { countdownText, countdownTone, remainingSeconds } from "../lunch/countdown";
import { LUNCH_STATUS, correctionLabel, lunchDuration, lunchRange } from "../lunch/lunchStatus";
import MoreMenu, { type MenuItem } from "../ui/MoreMenu.vue";
import StatusBadge from "../ui/StatusBadge.vue";

const props = defineProps<{ title: string; entries: BoardEntry[]; now: number; warningMinutes: number; empty: string }>();
const emit = defineEmits<{ correct: [entry: BoardEntry]; delete: [entry: BoardEntry] }>();

const LUNCH_ACTIONS: MenuItem[] = [
  { key: "correct", label: "Исправить время" },
  { key: "delete", label: "Удалить", danger: true },
];

function choose(entry: BoardEntry, key: string): void {
  if (key === "delete") {
    emit("delete", entry);
  } else {
    emit("correct", entry);
  }
}

const remaining = (entry: BoardEntry) => remainingSeconds(entry.lunch.started_at, entry.lunch.limit_minutes, props.now);
</script>

<template>
  <section class="panel board-list" :aria-label="title">
    <h2 class="board-list__title">
      {{ title }} <span class="board-list__count numeric">{{ entries.length }}</span>
    </h2>
    <ul v-if="entries.length" class="board-list__rows">
      <li v-for="entry in entries" :key="entry.lunch.id" class="board-list__row">
        <div class="board-list__who">
          <span class="board-list__name">{{ entry.person.name }}</span>
          <span class="board-list__details">{{ entry.person.login }}</span>
        </div>
        <span class="board-list__range numeric">{{ lunchRange(entry.lunch) }}</span>
        <span
          v-if="entry.lunch.status === 'ongoing'"
          class="board-list__timer numeric"
          :class="`board-list__timer--${countdownTone(remaining(entry), warningMinutes)}`"
        >
          {{ countdownText(remaining(entry)) }}
        </span>
        <span v-else class="board-list__duration numeric">{{ lunchDuration(entry.lunch) }}</span>
        <StatusBadge class="board-list__status" :tone="LUNCH_STATUS[entry.lunch.status].tone" :label="LUNCH_STATUS[entry.lunch.status].label" />
        <MoreMenu class="board-list__more" :label="`Действия: ${entry.person.name}`" :items="LUNCH_ACTIONS" @select="choose(entry, $event)" />
        <p v-if="entry.lunch.correction" class="board-list__correction">
          {{ correctionLabel(entry.lunch.correction) }}: {{ entry.lunch.correction.by }}. Причина: {{ entry.lunch.correction.reason }}
        </p>
      </li>
    </ul>
    <p v-else class="board-list__empty">{{ empty }}</p>
  </section>
</template>

<style scoped>
.board-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  padding: 20px 22px;
}

.board-list__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-h3);
}

.board-list__count {
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--gray-bg);
  color: var(--muted);
  font-size: var(--text-small);
}

.board-list__rows {
  margin: 0;
  padding: 0;
  list-style: none;
}

.board-list__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto 36px;
  align-items: center;
  gap: 4px 12px;
  padding: 10px 0;
  border-top: 1px solid var(--line);
}

.board-list__who {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.board-list__name {
  font-weight: 600;
}

.board-list__details {
  font-size: var(--text-small);
  color: var(--muted);
}

.board-list__range {
  grid-row: 2;
  grid-column: 1 / 2;
  color: var(--muted);
}

.board-list__timer,
.board-list__duration {
  grid-row: 1;
  grid-column: 2 / 3;
  text-align: right;
}

.board-list__timer {
  font-weight: 600;
  white-space: nowrap;
}

.board-list__timer--ok {
  color: var(--green);
}

.board-list__timer--attention {
  color: var(--amber);
}

.board-list__timer--alarm {
  color: var(--red);
}

.board-list__status {
  grid-row: 2;
  grid-column: 2 / 3;
  justify-self: end;
}

.board-list__more {
  grid-row: 1 / 3;
  grid-column: 3 / 4;
}

.board-list__correction {
  grid-column: 1 / -1;
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.board-list__empty {
  margin: 0;
  padding: 6px 0 2px;
  color: var(--muted);
}

@media (max-width: 650px) {
  .board-list {
    padding: 18px 16px;
  }
}
</style>
