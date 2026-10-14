<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import type { JournalEntry } from "../../api/journal";
import { formatDateTime } from "../../format/dateTime";
import AppButton from "../ui/AppButton.vue";
import StatusBadge from "../ui/StatusBadge.vue";
import { ACTIONS, objectOf, rowValue, subjectName } from "./entries";

const props = defineProps<{ entries: JournalEntry[]; hasMore: boolean; loading: boolean }>();
const emit = defineEmits<{ more: [] }>();

const sentinel = ref<HTMLElement | null>(null);
let observer: IntersectionObserver | null = null;

function askForMore(): void {
  if (props.hasMore && !props.loading) {
    emit("more");
  }
}

function watchSentinel(element: HTMLElement | null): void {
  observer?.disconnect();
  if (!element || typeof IntersectionObserver === "undefined") {
    return;
  }
  observer = new IntersectionObserver((seen) => seen.some((item) => item.isIntersecting) && askForMore());
  observer.observe(element);
}

watch(sentinel, watchSentinel);
onBeforeUnmount(() => observer?.disconnect());
</script>

<template>
  <section class="panel journal-list" aria-label="Записи журнала">
    <ul v-if="entries.length" class="journal-list__rows">
      <li v-for="entry in entries" :key="entry.id" class="journal-list__row">
        <div class="journal-list__head">
          <StatusBadge :tone="ACTIONS[entry.action].tone" :label="ACTIONS[entry.action].label" />
          <span class="journal-list__when numeric">{{ formatDateTime(entry.created_at) }}</span>
        </div>
        <p class="journal-list__who">
          <span class="journal-list__name">{{ subjectName(entry) }}</span>
          <template v-if="objectOf(entry)">
            <span class="journal-list__arrow" aria-hidden="true">→</span>
            <span class="journal-list__name">{{ objectOf(entry)?.name }}</span>
          </template>
          <span v-if="entry.address" class="journal-list__address code">{{ entry.address }}</span>
        </p>
        <dl v-if="entry.details.length" class="journal-list__details">
          <div v-for="row in entry.details" :key="row.label" class="journal-list__detail">
            <dt>{{ row.label }}</dt>
            <dd>{{ rowValue(row) }}</dd>
          </div>
        </dl>
      </li>
    </ul>
    <div v-else-if="!loading" class="journal-list__empty">
      <p>За выбранный период записей нет</p>
      <p class="journal-list__hint">Измените период, сотрудника или вид действия</p>
    </div>
    <div ref="sentinel" class="journal-list__footer">
      <AppButton v-if="hasMore" size="small" :disabled="loading" @click="askForMore">{{ loading ? "Загружаем…" : "Показать ещё" }}</AppButton>
    </div>
  </section>
</template>

<style scoped>
.journal-list {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 8px 22px 16px;
}

.journal-list__rows {
  margin: 0;
  padding: 0;
  list-style: none;
}

.journal-list__row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}

.journal-list__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.journal-list__when {
  font-size: var(--text-small);
  color: var(--muted);
}

.journal-list__who {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 8px;
  margin: 0;
  min-width: 0;
}

.journal-list__name {
  font-weight: 600;
  overflow-wrap: anywhere;
}

.journal-list__arrow {
  color: var(--muted);
}

.journal-list__address {
  font-size: var(--text-small);
  color: var(--muted);
}

.journal-list__details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 0;
  font-size: var(--text-small);
}

.journal-list__detail {
  display: grid;
  grid-template-columns: minmax(120px, 200px) minmax(0, 1fr);
  gap: 12px;
}

.journal-list__detail dt {
  color: var(--muted);
}

.journal-list__detail dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.journal-list__empty {
  padding: 28px 0 12px;
  text-align: center;
  color: var(--muted);
}

.journal-list__empty p {
  margin: 0;
}

.journal-list__hint {
  margin-top: 4px;
  font-size: var(--text-small);
}

.journal-list__footer {
  display: flex;
  justify-content: center;
  padding-top: 12px;
}

@media (max-width: 650px) {
  .journal-list {
    padding: 4px 16px 14px;
  }

  .journal-list__detail {
    grid-template-columns: minmax(0, 1fr);
    gap: 0;
  }
}
</style>
