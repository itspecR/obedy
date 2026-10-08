<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiError } from "../../api/http";
import { useSession } from "../../stores/session";
import AppButton from "../ui/AppButton.vue";
import TextField from "../ui/TextField.vue";
import { firstProblem, passwordRules } from "./passwordRules";

const emit = defineEmits<{ changed: []; cancel: [] }>();
const props = withDefaults(defineProps<{ cancellable?: boolean; askCurrent?: boolean }>(), { cancellable: false, askCurrent: false });

const session = useSession();
const current = ref("");
const next = ref("");
const repeat = ref("");
const error = ref("");
const busy = ref(false);
const rules = computed(() => passwordRules(next.value, repeat.value, session.me?.login ?? ""));

function validate(): string {
  if ((props.askCurrent && !current.value) || !next.value || !repeat.value) {
    return "Заполните все поля";
  }
  return firstProblem(rules.value);
}

async function submit(): Promise<void> {
  error.value = validate();
  if (error.value) {
    return;
  }
  busy.value = true;
  try {
    await session.changePassword(next.value, props.askCurrent ? current.value : undefined);
    emit("changed");
  } catch (failure) {
    error.value = failure instanceof ApiError ? failure.message : "Не удалось сменить пароль. Попробуйте ещё раз";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <form class="password-form" novalidate @submit.prevent="submit">
    <TextField
      v-if="askCurrent"
      v-model="current"
      label="Текущий пароль"
      type="password"
      autocomplete="current-password"
      :disabled="busy"
    />
    <TextField v-model="next" label="Новый пароль" type="password" autocomplete="new-password" :disabled="busy" />
    <TextField v-model="repeat" label="Повторите новый пароль" type="password" autocomplete="new-password" :disabled="busy" />
    <ul class="password-form__rules" aria-label="Требования к паролю">
      <li v-for="rule in rules" :key="rule.key" class="password-form__rule" :class="{ 'password-form__rule--met': rule.met }">
        <span class="password-form__mark" aria-hidden="true">{{ rule.met ? "✓" : "•" }}</span>
        {{ rule.text }}<span class="visually-hidden">{{ rule.met ? " – выполнено" : " – не выполнено" }}</span>
      </li>
    </ul>
    <p class="password-form__note">
      Слишком простые и распространённые пароли, а также пароли с логином, именем или фамилией система не примет.
      После смены вход закроется на остальных ваших устройствах.
    </p>
    <p v-if="error" class="password-form__error" role="alert">{{ error }}</p>
    <div class="password-form__actions">
      <AppButton v-if="cancellable" :disabled="busy" @click="emit('cancel')">Отмена</AppButton>
      <AppButton type="submit" variant="primary" :block="!cancellable" :disabled="busy">
        {{ busy ? "Сохраняем…" : "Сменить пароль" }}
      </AppButton>
    </div>
  </form>
</template>

<style scoped>
.password-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.password-form__rules {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--text-small);
  color: var(--muted);
}

.password-form__rule {
  display: flex;
  gap: 8px;
  transition: color var(--motion);
}

.password-form__rule--met {
  color: var(--green);
}

.password-form__mark {
  width: 12px;
  text-align: center;
}

.password-form__note {
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.password-form__error {
  margin: 0;
  padding: 10px 12px;
  border-radius: var(--radius-button);
  background: var(--red-bg);
  color: var(--red);
}

.password-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
