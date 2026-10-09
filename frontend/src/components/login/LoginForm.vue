<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { fetchDirectoryStatus } from "../../api/directory";
import { ApiError } from "../../api/http";
import { useSession } from "../../stores/session";
import AppButton from "../ui/AppButton.vue";
import TextField from "../ui/TextField.vue";
import { isAutofilled } from "./autofill";

const AUTOFILL_CHECKS_MS = [100, 500, 1500];

const props = defineProps<{ melted?: boolean }>();
const emit = defineEmits<{ attempt: []; success: []; failure: [] }>();
const session = useSession();

const form = ref<HTMLFormElement | null>(null);
const login = ref("");
const password = ref("");
const error = ref("");
const busy = ref(false);
const failed = ref(false);
const autofilled = ref(false);
const showHelp = ref(false);
const domainLogin = ref(false);
const timers: number[] = [];

const ready = computed(() => password.value.length > 0 || autofilled.value || busy.value || props.melted);
const loginPlaceholder = computed(() => (domainLogin.value ? "Логин Windows" : "Введите логин"));
const helpText = computed(() =>
  domainLogin.value
    ? "Используйте тот же логин и пароль, что и для входа в Windows. Если не получается — обратитесь к администратору системы."
    : "Обратитесь к администратору системы – он поможет восстановить доступ.",
);

function input(autocomplete: string): HTMLInputElement | null {
  return form.value?.querySelector<HTMLInputElement>(`input[autocomplete="${autocomplete}"]`) ?? null;
}

function checkAutofill(): void {
  autofilled.value = isAutofilled(input("current-password"));
}

function takeBrowserValues(): void {
  login.value ||= input("username")?.value ?? "";
  password.value ||= input("current-password")?.value ?? "";
}

function typedPassword(value: string): void {
  password.value = value;
  failed.value = false;
}

function reject(message: string): void {
  error.value = message;
  failed.value = true;
  password.value = "";
  autofilled.value = false;
  emit("failure");
}

async function focusPassword(): Promise<void> {
  await nextTick();
  input("current-password")?.focus();
}

onMounted(async () => {
  AUTOFILL_CHECKS_MS.forEach((delay) => timers.push(window.setTimeout(checkAutofill, delay)));
  try {
    domainLogin.value = (await fetchDirectoryStatus()).enabled;
  } catch {
    domainLogin.value = false;
  }
});

onBeforeUnmount(() => timers.forEach((timer) => window.clearTimeout(timer)));

async function submit(): Promise<void> {
  error.value = "";
  takeBrowserValues();
  if (!login.value.trim() || !password.value) {
    error.value = "Введите логин и пароль";
    return;
  }
  busy.value = true;
  emit("attempt");
  try {
    await session.signIn({ login: login.value, password: password.value });
    password.value = "";
    emit("success");
  } catch (failure) {
    reject(failure instanceof ApiError ? failure.message : "Не удалось войти. Попробуйте ещё раз");
  } finally {
    busy.value = false;
  }
  if (failed.value) {
    await focusPassword();
  }
}
</script>

<template>
  <form ref="form" class="login-form" novalidate @submit.prevent="submit">
    <TextField v-model="login" label="Логин" icon="user" :placeholder="loginPlaceholder" autocomplete="username" plain :disabled="busy" />
    <TextField
      :model-value="password"
      label="Пароль"
      icon="lock"
      placeholder="Введите пароль"
      type="password"
      autocomplete="current-password"
      :invalid="failed"
      :disabled="busy"
      @update:model-value="typedPassword"
    />
    <Transition name="login-alert">
      <p v-if="error" class="login-form__error" role="alert">{{ error }}</p>
    </Transition>
    <div class="login-form__submit" :class="{ 'login-form__submit--shown': ready }" :inert="!ready">
      <div class="login-form__submit-inner" :class="{ 'login-form__submit-inner--melted': melted }">
        <AppButton type="submit" variant="primary" block :disabled="busy">{{ busy ? "Входим…" : "Войти →" }}</AppButton>
      </div>
      <div class="login-form__launch"><slot name="launch" /></div>
    </div>
    <div class="login-form__help-box">
      <button type="button" class="login-form__link" :aria-expanded="showHelp" @click="showHelp = !showHelp">Не получается войти?</button>
      <p v-if="showHelp" class="login-form__help">{{ helpText }}</p>
    </div>
  </form>
</template>

<style scoped>
.login-form {
  --reveal: 240ms;
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

.login-form__submit {
  position: relative;
  display: grid;
  grid-template-rows: 0fr;
  margin-top: -16px;
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
  transition:
    grid-template-rows var(--reveal) ease,
    margin-top var(--reveal) ease,
    opacity var(--reveal) ease,
    transform var(--reveal) ease;
}

.login-form__submit--shown {
  grid-template-rows: 1fr;
  margin-top: 0;
  opacity: 1;
  transform: none;
}

.login-form__submit-inner {
  min-height: 0;
  overflow: hidden;
  transition:
    opacity var(--reveal) ease,
    transform var(--reveal) ease,
    filter var(--reveal) ease;
}

.login-form__submit-inner--melted {
  opacity: 0;
  transform: scale(0.6);
  filter: blur(6px);
}

.login-form__launch {
  position: absolute;
  bottom: 0;
  left: 50%;
}

.login-alert-enter-active,
.login-alert-leave-active {
  transition:
    opacity var(--reveal) ease,
    transform var(--reveal) ease;
}

.login-alert-enter-from,
.login-alert-leave-to {
  opacity: 0;
  transform: translateY(-4px);
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
