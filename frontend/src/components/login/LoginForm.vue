<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { fetchDirectoryStatus } from "../../api/directory";
import { ApiError } from "../../api/http";
import { useSession } from "../../stores/session";
import AppButton from "../ui/AppButton.vue";
import TextField from "../ui/TextField.vue";

const emit = defineEmits<{ success: [] }>();
const session = useSession();

const login = ref("");
const password = ref("");
const error = ref("");
const busy = ref(false);
const showHelp = ref(false);
const domainLogin = ref(false);

const loginPlaceholder = computed(() => (domainLogin.value ? "Логин Windows" : "Введите логин"));
const helpText = computed(() =>
  domainLogin.value
    ? "Используйте тот же логин и пароль, что и для входа в Windows. Если не получается — обратитесь к администратору системы."
    : "Обратитесь к администратору системы – он поможет восстановить доступ.",
);

onMounted(async () => {
  try {
    domainLogin.value = (await fetchDirectoryStatus()).enabled;
  } catch {
    domainLogin.value = false;
  }
});

async function submit(): Promise<void> {
  error.value = "";
  if (!login.value.trim() || !password.value) {
    error.value = "Введите логин и пароль";
    return;
  }
  busy.value = true;
  try {
    await session.signIn({ login: login.value, password: password.value });
    password.value = "";
    emit("success");
  } catch (failure) {
    error.value = failure instanceof ApiError ? failure.message : "Не удалось войти. Попробуйте ещё раз";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <form class="login-form" novalidate @submit.prevent="submit">
    <TextField v-model="login" label="Логин" icon="user" :placeholder="loginPlaceholder" autocomplete="username" plain :disabled="busy" />
    <TextField v-model="password" label="Пароль" icon="lock" placeholder="Введите пароль" type="password" autocomplete="current-password" :disabled="busy" />
    <p v-if="error" class="login-form__error" role="alert">{{ error }}</p>
    <AppButton type="submit" variant="primary" block :disabled="busy">{{ busy ? "Входим…" : "Войти →" }}</AppButton>
    <div class="login-form__help-box">
      <button type="button" class="login-form__link" :aria-expanded="showHelp" @click="showHelp = !showHelp">Не получается войти?</button>
      <p v-if="showHelp" class="login-form__help">{{ helpText }}</p>
    </div>
  </form>
</template>

<style scoped>
.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.login-form__error {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid var(--red-line);
  border-radius: var(--radius-button);
  background: var(--red-bg);
  color: var(--red);
}

.login-form__link {
  align-self: center;
  padding: 0;
  border: 0;
  background: none;
  color: var(--blue);
  font: inherit;
  cursor: pointer;
}

.login-form__help-box {
  text-align: center;
}

.login-form__help {
  margin: 8px 0 0;
  color: var(--muted);
}
</style>
