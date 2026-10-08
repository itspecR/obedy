<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { fetchSyncReport, runSync, type SyncReport } from "../../api/directory";
import { errorMessage } from "../../api/http";
import { useToasts } from "../../composables/useToasts";
import AppButton from "../ui/AppButton.vue";
import { describeSync } from "./syncReport";

const props = defineProps<{ blockedReason: string }>();

const report = ref<SyncReport | null>(null);
const busy = ref(false);
const { fail } = useToasts();

const view = computed(() => describeSync(report.value));

async function load(): Promise<void> {
  try {
    report.value = await fetchSyncReport();
  } catch (error) {
    fail(errorMessage(error, "Не удалось узнать итог последней синхронизации"));
  }
}

async function run(): Promise<void> {
  busy.value = true;
  try {
    report.value = await runSync();
  } catch (error) {
    fail(errorMessage(error, "Не удалось запустить синхронизацию. Попробуйте ещё раз"));
  } finally {
    busy.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section class="panel sync" aria-labelledby="sync-title">
    <h2 id="sync-title" class="sync__title">Синхронизация</h2>
    <p class="sync__note">
      Раз в час сайт сверяется с доменом: добавляет сотрудников из группы, обновляет ФИО, отдел и должность, а уволенных и
      убранных из группы отключает и сразу завершает их входы.
    </p>
    <p class="sync__result" :class="`sync__result--${view.tone}`" role="status">{{ view.text }}</p>
    <div class="sync__actions">
      <AppButton :disabled="busy || Boolean(props.blockedReason)" @click="run">
        {{ busy ? "Синхронизируем…" : "Синхронизировать сейчас" }}
      </AppButton>
      <span v-if="props.blockedReason" class="sync__note">{{ props.blockedReason }}</span>
    </div>
  </section>
</template>

<style scoped>
.sync {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 22px 24px;
}

.sync__title {
  font-size: var(--text-h3);
}

.sync__note {
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.sync__result {
  margin: 0;
  padding: 12px 14px;
  border: 1px solid var(--gray-line);
  border-radius: var(--radius-button);
  background: var(--gray-bg);
}

.sync__result--ok {
  border-color: var(--green-line);
  background: var(--green-bg);
  color: var(--green);
}

.sync__result--attention {
  border-color: var(--amber-line);
  background: var(--amber-bg);
  color: var(--amber);
}

.sync__result--alarm {
  border-color: var(--red-line);
  background: var(--red-bg);
  color: var(--red);
}

.sync__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

@media (max-width: 650px) {
  .sync {
    padding: 18px 16px;
  }
}
</style>
