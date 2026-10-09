<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { checkDirectory, fetchDirectory, saveDirectory, type CheckResult, type DirectorySettings } from "../api/directory";
import { errorMessage } from "../api/http";
import { DEFAULT_PORTS, MODE_OPTIONS, draftFrom, formFrom, sameDraft, type DirectoryDraft } from "../components/directory/draft";
import SyncPanel from "../components/directory/SyncPanel.vue";
import AppButton from "../components/ui/AppButton.vue";
import BlockTitle from "../components/ui/BlockTitle.vue";
import ChoiceField from "../components/ui/ChoiceField.vue";
import PageHeader from "../components/ui/PageHeader.vue";
import SwitchField from "../components/ui/SwitchField.vue";
import TextAreaField from "../components/ui/TextAreaField.vue";
import TextField from "../components/ui/TextField.vue";
import { useToasts } from "../composables/useToasts";

const settings = ref<DirectorySettings | null>(null);
const draft = ref<DirectoryDraft | null>(null);
const loadError = ref("");
const busy = ref(false);
const check = ref<CheckResult | null>(null);
const { notify, fail } = useToasts();

const dirty = computed(() => Boolean(settings.value && draft.value && !sameDraft(draftFrom(settings.value), draft.value)));
const portHint = computed(() => (draft.value ? `Пусто — стандартный порт ${DEFAULT_PORTS[draft.value.mode]}` : ""));
const syncBlocked = computed(() => {
  if (dirty.value) {
    return "Сохраните изменения, чтобы синхронизировать сотрудников";
  }
  return settings.value?.enabled ? "" : "Включите вход через домен и сохраните, чтобы синхронизировать сотрудников";
});
const passwordHint = computed(() => (settings.value?.has_bind_password ? "Пароль сохранён. Оставьте поле пустым, чтобы не менять его" : "Пароль ещё не задан"));

function accept(next: DirectorySettings): void {
  settings.value = next;
  draft.value = draftFrom(next);
}

async function load(): Promise<void> {
  loadError.value = "";
  try {
    accept(await fetchDirectory());
  } catch (error) {
    loadError.value = errorMessage(error, "Не удалось загрузить настройки домена");
  }
}

async function save(): Promise<void> {
  if (!draft.value) {
    return;
  }
  busy.value = true;
  check.value = null;
  try {
    accept(await saveDirectory(formFrom(draft.value)));
    notify("Настройки домена сохранены");
  } catch (error) {
    fail(errorMessage(error, "Не удалось сохранить. Проверьте поля и попробуйте ещё раз"));
  } finally {
    busy.value = false;
  }
}

async function runCheck(): Promise<void> {
  busy.value = true;
  try {
    check.value = await checkDirectory();
  } catch (error) {
    check.value = { ok: false, message: errorMessage(error, "Не удалось выполнить проверку") };
  } finally {
    busy.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section class="directory">
    <PageHeader title="Домен" subtitle="Вход сотрудников под учётными записями Windows (Active Directory)" />
    <div v-if="loadError" class="panel directory__card directory__error" role="alert">
      <p>{{ loadError }}</p>
      <AppButton @click="load">Повторить</AppButton>
    </div>
    <div v-else-if="draft" class="directory__layout">
      <form class="directory__form" novalidate @submit.prevent="save">
        <div class="panel directory__card">
          <SwitchField
            label="Вход через домен"
            hint="Сотрудники входят своим логином и паролем Windows. Локальный администратор входит всегда"
            :checked="draft.enabled"
            :disabled="busy"
            @change="draft.enabled = $event"
          />
        </div>

        <div class="panel directory__card">
          <h2 class="directory__title">Подключение</h2>
          <TextField v-model="draft.servers" label="Контроллеры домена" placeholder="например: dc1.company.local dc2.company.local" hint="Полные имена через пробел, как в сертификатах контроллеров (для LDAPS не IP). Второй используется, если первый не отвечает" plain :disabled="busy" />
          <div class="directory__row">
            <ChoiceField v-model="draft.mode" label="Защита соединения" :options="MODE_OPTIONS" :disabled="busy" />
            <TextField v-model="draft.port" class="directory__port" label="Порт" type="number" :hint="portHint" plain :disabled="busy" />
          </div>
          <p v-if="draft.mode === 'plain'" class="directory__warning" role="note">
            Без шифрования пароли сотрудников передаются по сети открытым текстом. Используйте только для проверки.
          </p>
          <TextAreaField
            v-model="draft.ca_certificate"
            label="Корневой сертификат домена (PEM)"
            placeholder="Вставьте текст сертификата: -----BEGIN CERTIFICATE----- …"
            hint="Нужен, если сертификат контроллера выдан внутренним центром сертификации"
            :disabled="busy"
          />
        </div>

        <div class="panel directory__card">
          <BlockTitle title="Сервисная учётная запись" info="Учётная запись только на чтение: через неё сайт ищет сотрудников в домене." />
          <div class="directory__row directory__row--even">
            <TextField v-model="draft.bind_user" label="Логин" placeholder="например: svc-obedy@company.local" plain :disabled="busy" />
            <TextField v-model="draft.bind_password" label="Пароль" type="password" autocomplete="new-password" :hint="passwordHint" :disabled="busy" />
          </div>
        </div>

        <div class="panel directory__card">
          <h2 class="directory__title">Кто может входить</h2>
          <TextField v-model="draft.base_dn" label="База поиска" placeholder="например: DC=company,DC=local" hint="Где искать сотрудников: весь домен (DC=…) или подразделение (OU=…,DC=…)" plain :disabled="busy" />
          <TextField v-model="draft.group_dn" label="Группа доступа" placeholder="например: CN=Obedy,CN=Users,DC=company,DC=local" hint="Входить смогут только члены этой группы, в том числе через вложенные группы. Пусто — все из базы поиска" plain :disabled="busy" />
          <TextField v-model="draft.session_days" class="directory__days" label="Срок входа, дней" type="number" hint="От 1 до 90. Потом сотрудник вводит пароль заново" plain :disabled="busy" />
        </div>

        <div class="directory__actions">
          <AppButton type="submit" variant="primary" :disabled="busy || !dirty">Сохранить</AppButton>
          <AppButton :disabled="busy || dirty" @click="runCheck">Проверить подключение</AppButton>
          <span v-if="dirty" class="directory__note">Сохраните изменения, чтобы проверить подключение</span>
        </div>
        <p v-if="check" class="directory__check" :class="check.ok ? 'directory__check--ok' : 'directory__check--fail'" role="status">{{ check.message }}</p>
      </form>
      <aside class="directory__side">
        <SyncPanel :blocked-reason="syncBlocked" />
      </aside>
    </div>
    <div v-if="!draft && !loadError" class="panel directory__card directory__loading" aria-busy="true">Загружаем…</div>
  </section>
</template>

<style scoped>
.directory,
.directory__form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.directory__form,
.directory__error,
.directory__loading {
  min-width: 0;
  max-width: 880px;
}

.directory__layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
  gap: 20px;
}

@media (min-width: 1200px) {
  .directory__layout {
    grid-template-columns: minmax(0, 880px) minmax(300px, 400px);
  }

  .directory__side {
    position: sticky;
    top: 24px;
  }
}

.directory__card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px 24px;
}

.directory__title {
  font-size: var(--text-h3);
}

.directory__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 160px;
  align-items: start;
  gap: 12px;
}

.directory__row--even {
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
}

.directory__days {
  max-width: 220px;
}

.directory__note {
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.directory__warning {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid var(--red-line);
  border-radius: var(--radius-button);
  background: var(--red-bg);
  color: var(--red);
}

.directory__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.directory__check {
  margin: 0;
  padding: 12px 14px;
  border-radius: var(--radius-button);
}

.directory__check--ok {
  border: 1px solid var(--green-line);
  background: var(--green-bg);
  color: var(--green);
}

.directory__check--fail {
  border: 1px solid var(--red-line);
  background: var(--red-bg);
  color: var(--red);
}

.directory__error {
  align-items: flex-start;
}

.directory__error p {
  margin: 0;
  color: var(--red);
}

.directory__loading {
  color: var(--muted);
}

@media (max-width: 650px) {
  .directory__card {
    padding: 18px 16px;
  }

  .directory__row,
  .directory__row--even {
    grid-template-columns: minmax(0, 1fr);
  }

  .directory__days {
    max-width: none;
  }
}
</style>
