<script setup lang="ts">
import { onMounted, ref } from "vue";
import { changeDatabase, checkDatabaseChange, fetchDatabase, type CurrentDatabase } from "../api/database";
import { errorMessage, request } from "../api/http";
import type { ConnectionForm, ProbeResult } from "../api/setup";
import ConnectionFields from "../components/setup/ConnectionFields.vue";
import { waitUntil } from "../components/setup/waitUntil";
import AppButton from "../components/ui/AppButton.vue";
import BlockTitle from "../components/ui/BlockTitle.vue";
import PageHeader from "../components/ui/PageHeader.vue";
import { useConfirm } from "../composables/useConfirm";

const PAGE_INFO = "Данные подключения хранятся на сервере сайта в зашифрованном виде. Копии базы делает SQL Server.";
const EMPTY_NOTE = "Если новая база пустая, сайт попросит код настройки с сервера (sudo ./scripts/setup-code.sh), чтобы создать администратора.";

const current = ref<CurrentDatabase | null>(null);
const loadError = ref("");
const form = ref<ConnectionForm | null>(null);
const busy = ref(false);
const restarting = ref(false);
const result = ref<Pick<ProbeResult, "ok" | "message"> | null>(null);
const { ask } = useConfirm();

async function load(): Promise<void> {
  loadError.value = "";
  try {
    current.value = await fetchDatabase();
  } catch (error) {
    loadError.value = errorMessage(error, "Не удалось загрузить подключение к базе");
  }
}

function startEditing(): void {
  if (current.value) {
    form.value = { ...current.value, password: "" };
    result.value = null;
  }
}

function stopEditing(): void {
  form.value = null;
  result.value = null;
}

async function attempt(action: (draft: ConnectionForm) => Promise<void>): Promise<void> {
  if (!form.value) {
    return;
  }
  busy.value = true;
  result.value = null;
  try {
    await action(form.value);
  } catch (error) {
    result.value = { ok: false, message: errorMessage(error, "Не удалось выполнить. Попробуйте ещё раз") };
  } finally {
    busy.value = false;
  }
}

async function siteIsBack(): Promise<true | null> {
  const health = await request<{ database: string }>("GET", "/health");
  return health.database === "ok" ? true : null;
}

const check = () => attempt(async (draft) => {
  result.value = await checkDatabaseChange(draft);
});

const save = () => attempt(async (draft) => {
  const accepted = await ask({
    title: "Переключить сайт на другую базу?",
    text: "Сайт перезапустится и начнёт работать с указанной базой. Текущая база останется на SQL Server без изменений.",
    action: "Переключить",
    danger: true,
  });
  if (!accepted) {
    return;
  }
  await changeDatabase(draft);
  restarting.value = true;
  await waitUntil(siteIsBack);
  window.location.reload();
});

onMounted(load);
</script>

<template>
  <section class="database">
    <PageHeader title="База данных" subtitle="SQL Server, где хранятся данные сайта" :info="PAGE_INFO" />

    <div v-if="loadError" class="panel database__message" role="alert">
      <p class="database__error">{{ loadError }}</p>
      <AppButton @click="load">Повторить</AppButton>
    </div>
    <div v-else-if="!current" class="panel database__message" aria-busy="true">Загружаем…</div>
    <p v-else-if="restarting" class="panel database__message" role="status">Сайт перезапускается и переходит на новую базу — страница обновится сама…</p>

    <section v-else-if="!form" class="panel database__block" aria-labelledby="database-current">
      <BlockTitle title="Подключение" title-id="database-current" />
      <dl class="database__rows">
        <dt>Сервер</dt>
        <dd class="code">{{ current.host }}</dd>
        <dt>Порт</dt>
        <dd>{{ current.port || "по умолчанию" }}</dd>
        <dt>База</dt>
        <dd class="code">{{ current.name }}</dd>
        <dt>Логин SQL Server</dt>
        <dd class="code">{{ current.user }}</dd>
        <dt>Доверять сертификату</dt>
        <dd>{{ current.trust_certificate ? "да" : "нет" }}</dd>
      </dl>
      <div>
        <AppButton @click="startEditing">Изменить подключение</AppButton>
      </div>
    </section>

    <form v-else class="panel database__block" novalidate @submit.prevent="save">
      <BlockTitle title="Новое подключение" title-id="database-new" :info="EMPTY_NOTE" />
      <ConnectionFields v-model="form" :disabled="busy" />
      <p v-if="result" class="database__result" :class="result.ok ? 'database__result--ok' : 'database__result--fail'" role="alert">{{ result.message }}</p>
      <div class="database__actions">
        <AppButton :disabled="busy" @click="check">Проверить</AppButton>
        <AppButton type="submit" variant="primary" :disabled="busy">Сохранить и перезапустить</AppButton>
        <AppButton variant="ghost" :disabled="busy" @click="stopEditing">Отмена</AppButton>
      </div>
    </form>
  </section>
</template>

<style scoped>
.database {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 640px;
}

.database__block {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px 20px;
}

.database__message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin: 0;
  padding: 32px 24px;
  color: var(--muted);
}

.database__error {
  margin: 0;
  color: var(--red);
}

.database__rows {
  display: grid;
  grid-template-columns: minmax(0, auto) minmax(0, 1fr);
  gap: 8px 16px;
  margin: 0;
}

.database__rows dt {
  color: var(--muted);
}

.database__rows dd {
  margin: 0;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.database__result {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid;
  border-radius: var(--radius-button);
}

.database__result--ok {
  border-color: var(--green-line);
  background: var(--green-bg);
  color: var(--green);
}

.database__result--fail {
  border-color: var(--red-line);
  background: var(--red-bg);
  color: var(--red);
}

.database__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 650px) {
  .database__block {
    padding: 16px;
  }
}
</style>
