<script setup lang="ts">
import { ref } from "vue";
import { useToasts } from "../../composables/useToasts";
import AppButton from "../ui/AppButton.vue";

defineProps<{ login: string; password: string }>();

const field = ref<HTMLInputElement | null>(null);
const { notify } = useToasts();

async function copy(value: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value);
    notify("Пароль скопирован");
  } catch {
    field.value?.select();
    notify("Пароль выделен — нажмите Ctrl+C, чтобы скопировать");
  }
}
</script>

<template>
  <div class="issued">
    <p class="issued__lead">Передайте данные сотруднику лично. При первом входе он задаст свой пароль.</p>
    <div class="issued__row">
      <span class="issued__label">Логин</span>
      <span class="code issued__value">{{ login }}</span>
    </div>
    <div class="issued__row">
      <span class="issued__label">Временный пароль</span>
      <input ref="field" class="code issued__value issued__password" :value="password" readonly aria-label="Временный пароль" @focus="field?.select()" />
      <AppButton size="small" @click="copy(password)">Скопировать</AppButton>
    </div>
    <p class="issued__warning">Пароль показан один раз. Если он потеряется — сбросьте его ещё раз.</p>
  </div>
</template>

<style scoped>
.issued {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.issued__lead,
.issued__warning {
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.issued__warning {
  color: var(--amber);
}

.issued__row {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
}

.issued__label {
  font-size: var(--text-small);
  color: var(--muted);
}

.issued__value {
  font-size: 16px;
}

.issued__password {
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-button);
  background: var(--field);
  color: var(--ink);
  letter-spacing: 0.04em;
}

@media (max-width: 650px) {
  .issued__row {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .issued__label {
    grid-column: 1 / -1;
  }
}
</style>
