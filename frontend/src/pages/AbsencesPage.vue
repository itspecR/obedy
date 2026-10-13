<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { fetchAbsences, removeAbsence, type Absence } from "../api/absences";
import { errorMessage } from "../api/http";
import AbsenceDialog from "../components/absences/AbsenceDialog.vue";
import { KIND_LABELS, rangeText, wholeMonth } from "../components/absences/absences";
import type { Period } from "../components/stats/period";
import AppButton from "../components/ui/AppButton.vue";
import DateField from "../components/ui/DateField.vue";
import MoreMenu, { type MenuItem } from "../components/ui/MoreMenu.vue";
import PageHeader from "../components/ui/PageHeader.vue";
import StatusBadge from "../components/ui/StatusBadge.vue";
import { useConfirm } from "../composables/useConfirm";
import { useToasts } from "../composables/useToasts";
import { todayIso } from "../format/dateTime";

const ACTIONS: MenuItem[] = [
  { key: "edit", label: "Изменить" },
  { key: "delete", label: "Удалить", danger: true },
];

const today = todayIso();
const period = ref<Period>(wholeMonth(today));
const absences = ref<Absence[] | null>(null);
const loadError = ref("");
const dialog = ref<{ absence: Absence | null } | null>(null);
const { ask } = useConfirm();
const { notify, fail } = useToasts();

const periodReady = computed(() => Boolean(period.value.from && period.value.to && period.value.from <= period.value.to));

async function load(): Promise<void> {
  if (!periodReady.value) {
    return;
  }
  loadError.value = "";
  try {
    absences.value = await fetchAbsences(period.value.from, period.value.to);
  } catch (error) {
    loadError.value = errorMessage(error, "Не удалось загрузить отсутствия");
  }
}

async function remove(absence: Absence): Promise<void> {
  const accepted = await ask({
    title: "Удалить отсутствие?",
    text: `${absence.name}: ${KIND_LABELS[absence.kind]}, ${rangeText(absence.first, absence.last)}. Эти дни снова будут считаться обычными рабочими.`,
    action: "Удалить",
    danger: true,
  });
  if (!accepted) {
    return;
  }
  try {
    await removeAbsence(absence.id);
    notify("Отсутствие удалено");
    await load();
  } catch (error) {
    fail(errorMessage(error, "Не удалось удалить. Попробуйте ещё раз"));
  }
}

function choose(absence: Absence, key: string): void {
  if (key === "edit") {
    dialog.value = { absence };
    return;
  }
  void remove(absence);
}

async function saved(): Promise<void> {
  dialog.value = null;
  await load();
}

onMounted(load);
</script>

<template>
  <section class="absences">
    <PageHeader title="Отсутствия" subtitle="Отпуска, больничные и другие дни, когда сотрудник не обедает на работе">
      <AppButton variant="primary" @click="dialog = { absence: null }">Отметить отсутствие</AppButton>
    </PageHeader>

    <div class="panel absences__filters">
      <DateField v-model="period.from" label="С" @change="load" />
      <DateField v-model="period.to" label="По" @change="load" />
    </div>

    <div v-if="loadError" class="panel absences__message" role="alert">
      <p class="absences__error">{{ loadError }}</p>
      <AppButton @click="load">Повторить</AppButton>
    </div>
    <div v-else-if="!absences" class="panel absences__message" aria-busy="true">Загружаем…</div>
    <div v-else-if="!absences.length" class="panel absences__message">
      <p class="absences__empty-title">В этот период отсутствий нет</p>
      <p>Отметьте отпуск или больничный — в эти дни сотрудник не попадёт в «Без обеда».</p>
    </div>
    <ul v-else class="panel absences__list">
      <li v-for="absence in absences" :key="absence.id" class="absences__row">
        <div class="absences__person">
          <span class="absences__name">{{ absence.name }}</span>
          <span class="absences__dates">{{ rangeText(absence.first, absence.last) }}</span>
        </div>
        <StatusBadge tone="neutral" :label="KIND_LABELS[absence.kind]" />
        <span class="absences__note">{{ absence.note }}</span>
        <MoreMenu :label="`Действия: ${absence.name}`" :items="ACTIONS" @select="choose(absence, $event)" />
      </li>
    </ul>

    <AbsenceDialog v-if="dialog" :absence="dialog.absence" :day="today" @close="dialog = null" @saved="saved" />
  </section>
</template>

<style scoped>
.absences {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.absences__filters {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 220px));
  gap: 12px;
  padding: 18px 20px;
}

.absences__message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px 24px;
  text-align: center;
}

.absences__message p {
  margin: 0;
  color: var(--muted);
}

.absences__empty-title {
  color: var(--ink) !important;
  font-weight: 600;
}

.absences__error {
  color: var(--red) !important;
}

.absences__list {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 6px 20px;
  list-style: none;
}

.absences__row {
  display: grid;
  grid-template-columns: minmax(200px, 1.2fr) auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-top: 1px solid var(--line);
}

.absences__row:first-child {
  border-top: 0;
}

.absences__person {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.absences__name {
  font-weight: 600;
}

.absences__dates {
  color: var(--muted);
  font-size: var(--text-small);
  font-variant-numeric: tabular-nums;
}

.absences__row :deep(.badge) {
  justify-self: start;
}

.absences__note {
  min-width: 0;
  overflow: hidden;
  color: var(--muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 650px) {
  .absences__filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding: 16px;
  }

  .absences__list {
    padding: 4px 16px;
  }

  .absences__row {
    grid-template-columns: minmax(0, 1fr) auto auto;
    gap: 6px 12px;
  }

  .absences__note {
    grid-column: 1 / -1;
    grid-row: 2;
  }

  .absences__note:empty {
    display: none;
  }
}
</style>
