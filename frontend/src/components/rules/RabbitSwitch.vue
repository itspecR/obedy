<script setup lang="ts">
import { onMounted, ref } from "vue";
import { fetchAppearance, switchRabbit } from "../../api/appearance";
import { errorMessage } from "../../api/http";
import { useToasts } from "../../composables/useToasts";
import SwitchField from "../ui/SwitchField.vue";

const HINT = "Белый кролик с часами при входе на сайт и рядом с таймером обеда у сотрудника. Выключено — привычные анимации";

const rabbit = ref<boolean | null>(null);
const busy = ref(false);
const { notify, fail } = useToasts();

async function load(): Promise<void> {
  try {
    rabbit.value = (await fetchAppearance()).rabbit;
  } catch (error) {
    fail(errorMessage(error, "Не удалось узнать, включён ли кролик"));
  }
}

async function change(enabled: boolean): Promise<void> {
  busy.value = true;
  try {
    rabbit.value = (await switchRabbit(enabled)).rabbit;
    notify(enabled ? "Кролик включён" : "Кролик выключен");
  } catch (error) {
    fail(errorMessage(error, "Не удалось переключить кролика. Попробуйте ещё раз"));
  } finally {
    busy.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="panel rabbit-switch">
    <h2 class="rabbit-switch__title">Оформление</h2>
    <SwitchField label="Анимация с кроликом" :hint="HINT" :checked="rabbit === true" :disabled="busy || rabbit === null" @change="change" />
  </div>
</template>

<style scoped>
.rabbit-switch {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px 24px;
}

.rabbit-switch__title {
  font-size: var(--text-h3);
}

@media (max-width: 650px) {
  .rabbit-switch {
    padding: 18px 16px;
  }
}
</style>
