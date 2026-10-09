<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { errorMessage } from "../api/http";
import { checkDatabase, createFirstAdmin, fetchSetupStatus, saveDatabase, type DatabaseForm, type FirstAdmin, type ProbeResult } from "../api/setup";
import AuthLayout from "../components/login/AuthLayout.vue";
import AppButton from "../components/ui/AppButton.vue";
import SwitchField from "../components/ui/SwitchField.vue";
import TextField from "../components/ui/TextField.vue";

const RESTART_POLL_MS = 2000;
const RESTART_ATTEMPTS = 60;
const CODE_HINT = "Код показывает install.sh. Новый код: sudo ./scripts/setup-code.sh на сервере сайта.";
const HOST_HINT = "IP или имя сервера SQL. Для именованного экземпляра: 192.168.1.10\\SQLEXPRESS.";
const PORT_HINT = "Пусто — порт по умолчанию или через SQL Server Browser для именованного экземпляра.";
const TRUST_HINT = "Включите, если у SQL Server свой (самоподписанный) сертификат — так обычно у SQL Server Express.";

type Step = "connect" | "restarting" | "admin" | "done";

const form = reactive<DatabaseForm>({ code: "", host: "", port: "", name: "obedy", user: "obedy", password: "", trust_certificate: true });
const step = ref<Step>("connect");
const busy = ref(false);
const result = ref<Pick<ProbeResult, "ok" | "message"> | null>(null);
const admin = ref<FirstAdmin | null>(null);

const pause = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

async function attempt(action: () => Promise<void>): Promise<void> {
  busy.value = true;
  result.value = null;
  try {
    await action();
  } catch (failure) {
    result.value = { ok: false, message: errorMessage(failure, "Не удалось выполнить. Попробуйте ещё раз") };
  } finally {
    busy.value = false;
  }
}

async function waitForRestart(): Promise<boolean> {
  for (let left = RESTART_ATTEMPTS; left > 0; left--) {
    await pause(RESTART_POLL_MS);
    try {
      const status = await fetchSetupStatus();
      if (status.configured) {
        return status.needs_admin;
      }
    } catch {
      continue;
    }
  }
  throw new Error("Сайт не перезапустился за 2 минуты. Проверьте сервер: sudo docker compose logs --tail=50 app");
}

const check = () => attempt(async () => {
  result.value = await checkDatabase(form);
});

const connect = () => attempt(async () => {
  await saveDatabase(form);
  step.value = "restarting";
  try {
    step.value = (await waitForRestart()) ? "admin" : "done";
  } catch (failure) {
    step.value = "connect";
    throw failure;
  }
});

const makeAdmin = () => attempt(async () => {
  admin.value = await createFirstAdmin(form.code);
  step.value = "done";
});

function toLogin(): void {
  window.location.assign("/login");
}

onMounted(async () => {
  const status = await fetchSetupStatus().catch(() => null);
  if (status?.configured && status.needs_admin) {
    step.value = "admin";
  }
});
</script>

<template>
  <AuthLayout title="Подключение базы">
    <form v-if="step === 'connect'" class="setup" novalidate @submit.prevent="connect">
      <p class="setup__lead">Укажите SQL Server, где будет храниться база сайта. Пустую базу и логин заранее создайте в SSMS.</p>
      <TextField v-model="form.code" label="Код настройки" :hint="CODE_HINT" placeholder="XXXX-XXXX-XXXX" plain :disabled="busy" />
      <div class="setup__row">
        <TextField v-model="form.host" label="Адрес SQL Server" :hint="HOST_HINT" placeholder="192.168.1.10\SQLEXPRESS" plain :disabled="busy" />
        <TextField v-model="form.port" label="Порт" :hint="PORT_HINT" placeholder="1433" plain :disabled="busy" />
      </div>
      <TextField v-model="form.name" label="База данных" plain :disabled="busy" />
      <div class="setup__row">
        <TextField v-model="form.user" label="Логин SQL Server" autocomplete="off" plain :disabled="busy" />
        <TextField v-model="form.password" label="Пароль" type="password" autocomplete="new-password" :disabled="busy" />
      </div>
      <SwitchField label="Доверять сертификату сервера" :hint="TRUST_HINT" :checked="form.trust_certificate" :disabled="busy" @change="form.trust_certificate = $event" />
      <p v-if="result" class="setup__result" :class="result.ok ? 'setup__result--ok' : 'setup__result--fail'" role="alert">{{ result.message }}</p>
      <div class="setup__actions">
        <AppButton :disabled="busy" @click="check">Проверить</AppButton>
        <AppButton type="submit" variant="primary" :disabled="busy">{{ busy ? "Подождите…" : "Подключить" }}</AppButton>
      </div>
    </form>

    <p v-else-if="step === 'restarting'" class="setup__lead" role="status">База подключена. Сайт перезапускается и готовит таблицы — это займёт до минуты…</p>

    <div v-else-if="step === 'admin'" class="setup">
      <p class="setup__lead">База подключена и пока пустая. Создайте первого администратора — сайт покажет его временный пароль.</p>
      <TextField v-model="form.code" label="Код настройки" :hint="CODE_HINT" placeholder="XXXX-XXXX-XXXX" plain :disabled="busy" />
      <p v-if="result" class="setup__result setup__result--fail" role="alert">{{ result.message }}</p>
      <AppButton variant="primary" block :disabled="busy" @click="makeAdmin">Создать администратора</AppButton>
    </div>

    <div v-else class="setup">
      <template v-if="admin">
        <p class="setup__lead">Администратор создан. Запишите временный пароль — он показывается один раз. При первом входе сайт попросит задать свой.</p>
        <dl class="setup__secret">
          <dt>Логин</dt>
          <dd class="code">{{ admin.login }}</dd>
          <dt>Временный пароль</dt>
          <dd class="code">{{ admin.password }}</dd>
        </dl>
      </template>
      <p v-else class="setup__lead">База подключена, в ней уже есть данные. Войдите своей учётной записью.</p>
      <AppButton variant="primary" block @click="toLogin">Перейти ко входу →</AppButton>
    </div>
  </AuthLayout>
</template>

<style scoped>
.setup {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setup__lead {
  margin: 0;
  color: var(--muted);
}

.setup__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 120px);
  gap: 12px;
}

.setup__row:has(input[type="password"]) {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.setup__result {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid;
  border-radius: var(--radius-button);
}

.setup__result--ok {
  border-color: var(--green-line);
  background: var(--green-bg);
  color: var(--green);
}

.setup__result--fail {
  border-color: var(--red-line);
  background: var(--red-bg);
  color: var(--red);
}

.setup__actions {
  display: flex;
  gap: 10px;
}

.setup__secret {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px 14px;
  margin: 0;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-panel);
  background: var(--field);
}

.setup__secret dt {
  color: var(--muted);
}

.setup__secret dd {
  margin: 0;
  font-weight: 600;
  overflow-wrap: anywhere;
}

@media (max-width: 650px) {
  .setup__row,
  .setup__row:has(input[type="password"]) {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
