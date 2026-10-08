<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { errorMessage } from "../api/http";
import { fetchLunchState, finishLunch, startLunch, undoLunch, type LunchState } from "../api/lunch";
import LunchControl from "../components/lunch/LunchControl.vue";
import LunchHistory from "../components/lunch/LunchHistory.vue";
import AppButton from "../components/ui/AppButton.vue";
import PageHeader from "../components/ui/PageHeader.vue";
import { useServerClock } from "../composables/useServerClock";
import { useToasts } from "../composables/useToasts";
import { shortName } from "../navigation";
import { useSession } from "../stores/session";

const REFRESH_MS = 60_000;

const session = useSession();
const greeting = computed(() => `Здравствуйте, ${shortName(session.me?.display_name ?? "")}`);

const state = ref<LunchState | null>(null);
const failed = ref(false);
const busy = ref(false);
const revision = ref(0);
const { now, sync } = useServerClock();
const { fail, notify } = useToasts();
let refresher: number | undefined;

function apply(next: LunchState): void {
  state.value = next;
  failed.value = false;
  sync(next.server_time);
}

async function load(): Promise<void> {
  try {
    apply(await fetchLunchState());
  } catch (error) {
    failed.value = state.value === null;
    if (!failed.value) {
      fail(errorMessage(error, "Не удалось обновить состояние обеда"));
    }
  }
}

async function act(action: () => Promise<LunchState>, done: string): Promise<void> {
  busy.value = true;
  try {
    apply(await action());
    revision.value += 1;
    notify(done);
  } catch (error) {
    fail(errorMessage(error, "Не удалось сохранить отметку. Попробуйте ещё раз"));
    await load();
  } finally {
    busy.value = false;
  }
}

function refreshWhenVisible(): void {
  if (document.visibilityState === "visible") {
    void load();
  }
}

onMounted(() => {
  void load();
  refresher = window.setInterval(refreshWhenVisible, REFRESH_MS);
  document.addEventListener("visibilitychange", refreshWhenVisible);
});

onUnmounted(() => {
  window.clearInterval(refresher);
  document.removeEventListener("visibilitychange", refreshWhenVisible);
});
</script>

<template>
  <section class="lunch">
    <PageHeader title="Обед" :subtitle="greeting" />
    <LunchControl
      v-if="state"
      :state="state"
      :now="now"
      :busy="busy"
      @start="act(startLunch, 'Приятного аппетита! Время пошло')"
      @finish="act(finishLunch, 'С возвращением! Обед отмечен')"
      @undo="act(undoLunch, 'Отметка отменена')"
    />
    <div v-else-if="failed" class="panel lunch__problem" role="alert">
      <p class="lunch__problem-title">Не удалось загрузить обед</p>
      <p class="lunch__problem-text">Проверьте подключение и попробуйте ещё раз.</p>
      <AppButton @click="load">Повторить</AppButton>
    </div>
    <div v-else class="panel lunch__loading" aria-busy="true">Загружаем…</div>
    <LunchHistory :revision="revision" />
  </section>
</template>

<style scoped>
.lunch {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.lunch__problem,
.lunch__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 32px 24px;
  text-align: center;
  color: var(--muted);
}

.lunch__problem-title {
  margin: 0;
  font-size: var(--text-h3);
  font-weight: 600;
  color: var(--ink);
}

.lunch__problem-text {
  margin: 0;
}
</style>
