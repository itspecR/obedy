<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { fetchBoard, type Board, type BoardEntry } from "../api/board";
import { errorMessage } from "../api/http";
import AddLunchDialog from "../components/board/AddLunchDialog.vue";
import BoardList from "../components/board/BoardList.vue";
import CorrectionDialog from "../components/board/CorrectionDialog.vue";
import DeleteLunchDialog from "../components/board/DeleteLunchDialog.vue";
import { filterEntries, groupEntries } from "../components/board/groups";
import AppButton from "../components/ui/AppButton.vue";
import DateField from "../components/ui/DateField.vue";
import PageHeader from "../components/ui/PageHeader.vue";
import TextField from "../components/ui/TextField.vue";
import { useServerClock } from "../composables/useServerClock";
import { useToasts } from "../composables/useToasts";
import { formatDay } from "../format/dateTime";

const REFRESH_MS = 30_000;

const board = ref<Board | null>(null);
const day = ref("");
const search = ref("");
const loadError = ref("");
const editing = ref<BoardEntry | null>(null);
const deleting = ref<BoardEntry | null>(null);
const adding = ref(false);
const { now, sync } = useServerClock();
const { fail } = useToasts();
let refresher: number | undefined;

const isToday = computed(() => Boolean(board.value && board.value.day === board.value.today));
const groups = computed(() => groupEntries(filterEntries(board.value?.entries ?? [], search.value), now.value));
const subtitle = computed(() => {
  if (!board.value) {
    return "Кто сейчас на обеде и кто вернулся";
  }
  return isToday.value ? `Сегодня, ${formatDay(board.value.day)} · обновляется каждые 30 секунд` : `Архив за ${formatDay(board.value.day)}`;
});

async function load(): Promise<void> {
  try {
    const next = await fetchBoard(day.value);
    board.value = next;
    day.value = next.day;
    loadError.value = "";
    sync(next.server_time);
  } catch (error) {
    const message = errorMessage(error, "Не удалось загрузить табло");
    if (board.value) {
      fail(message);
    } else {
      loadError.value = message;
    }
  }
}

function showToday(): void {
  day.value = board.value?.today ?? "";
  void load();
}

function replace(entry: BoardEntry): void {
  if (board.value) {
    board.value.entries = board.value.entries.map((item) => (item.lunch.id === entry.lunch.id ? entry : item));
  }
  editing.value = null;
}

function forget(lunchId: number): void {
  if (board.value) {
    board.value.entries = board.value.entries.filter((item) => item.lunch.id !== lunchId);
  }
  deleting.value = null;
}

function added(): void {
  adding.value = false;
  void load();
}

function refreshToday(): void {
  if (document.visibilityState === "visible" && isToday.value && !editing.value && !deleting.value && !adding.value) {
    void load();
  }
}

onMounted(() => {
  void load();
  refresher = window.setInterval(refreshToday, REFRESH_MS);
  document.addEventListener("visibilitychange", refreshToday);
});

onUnmounted(() => {
  window.clearInterval(refresher);
  document.removeEventListener("visibilitychange", refreshToday);
});
</script>

<template>
  <section class="board">
    <PageHeader title="Табло" :subtitle="subtitle">
      <div v-if="board" class="board__day">
        <DateField v-model="day" label="День" hide-label :max="board.today" @change="load" />
        <AppButton v-if="!isToday" @click="showToday">Сегодня</AppButton>
        <AppButton @click="adding = true">Добавить обед</AppButton>
      </div>
    </PageHeader>

    <div v-if="loadError" class="panel board__message" role="alert">
      <p class="board__error">{{ loadError }}</p>
      <AppButton @click="load">Повторить</AppButton>
    </div>
    <div v-else-if="!board" class="panel board__message" aria-busy="true">Загружаем…</div>
    <template v-else>
      <div class="panel board__filters">
        <TextField v-model="search" label="Поиск" icon="search" placeholder="например: Иванов" plain />
      </div>
      <div v-if="!board.entries.length" class="panel board__message">
        <p class="board__empty-title">{{ isToday ? "Сегодня ещё никто не уходил на обед" : "В этот день обедов не отмечено" }}</p>
        <p>Здесь появятся сотрудники, как только они нажмут «Ушёл на обед».</p>
      </div>
      <div v-else class="board__columns" :class="{ 'board__columns--archive': !isToday }">
        <BoardList
          v-if="isToday"
          title="На обеде сейчас"
          :entries="groups.away"
          :now="now"
          :warning-minutes="board.warning_minutes"
          empty="Сейчас никто не обедает"
          @correct="editing = $event"
          @delete="deleting = $event"
        />
        <BoardList
          title="С нарушениями"
          :entries="groups.violations"
          :now="now"
          :warning-minutes="board.warning_minutes"
          empty="Нарушений нет"
          @correct="editing = $event"
          @delete="deleting = $event"
        />
        <BoardList
          title="Вернулись вовремя"
          :entries="groups.returned"
          :now="now"
          :warning-minutes="board.warning_minutes"
          empty="Пока никто не вернулся"
          @correct="editing = $event"
          @delete="deleting = $event"
        />
      </div>
    </template>
    <CorrectionDialog v-if="editing" :entry="editing" @close="editing = null" @saved="replace" />
    <DeleteLunchDialog v-if="deleting" :entry="deleting" @close="deleting = null" @deleted="forget" />
    <AddLunchDialog v-if="adding && board" :day="board.day" @close="adding = false" @saved="added" />
  </section>
</template>

<style scoped>
.board {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.board__day {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.board__filters {
  padding: 18px 20px;
}

.board__columns {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
  gap: 20px;
}

@media (min-width: 1100px) {
  .board__columns {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .board__columns--archive {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.board__message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px 24px;
  text-align: center;
  color: var(--muted);
}

.board__message p {
  margin: 0;
}

.board__empty-title {
  font-size: var(--text-h3);
  font-weight: 600;
  color: var(--ink);
}

.board__error {
  color: var(--red);
}

@media (max-width: 650px) {
  .board__filters {
    padding: 16px;
  }
}
</style>
