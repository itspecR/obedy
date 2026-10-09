<script setup lang="ts">
import { computed } from "vue";
import { useLightMode, type LightPreference } from "../../composables/useLightMode";
import ChoiceField from "../ui/ChoiceField.vue";

const OPTIONS: { value: LightPreference; label: string }[] = [
  { value: "auto", label: "Авто" },
  { value: "on", label: "Включён" },
  { value: "off", label: "Выключен" },
];
const LIGHT_HINT = "Без размытия стекла и эффектов меню — для удалённого рабочего стола и компьютеров без видеокарты. «Авто» включает режим сам, когда браузер рисует без видеокарты. Выбор запоминается в этом браузере.";

const { preference, weakDevice, choose } = useLightMode();
const model = computed({ get: () => preference.value, set: choose });
const status = computed(() => {
  if (preference.value !== "auto") {
    return "";
  }
  return weakDevice.value ? "Сейчас включён: браузер рисует без видеокарты" : "Сейчас выключен: видеокарта справляется";
});
</script>

<template>
  <div class="light">
    <ChoiceField v-model="model" label="Лёгкий режим" :options="OPTIONS" :hint="LIGHT_HINT" />
    <p v-if="status" class="light__status">{{ status }}</p>
  </div>
</template>

<style scoped>
.light {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.light__status {
  margin: 0;
  color: var(--muted);
  font-size: var(--text-small);
}
</style>
