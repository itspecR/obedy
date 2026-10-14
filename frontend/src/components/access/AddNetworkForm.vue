<script setup lang="ts">
import { ref } from "vue";
import AppButton from "../ui/AppButton.vue";
import TextField from "../ui/TextField.vue";

const props = defineProps<{ busy: boolean; submit: (network: string, note: string) => Promise<boolean> }>();

const network = ref("");
const note = ref("");
const error = ref("");

async function send(): Promise<void> {
  error.value = network.value.trim() ? "" : "Укажите адрес, например 192.168.1.10 или 192.168.1.0/24";
  if (error.value) {
    return;
  }
  if (await props.submit(network.value, note.value)) {
    network.value = "";
    note.value = "";
  }
}
</script>

<template>
  <form class="add-network" novalidate @submit.prevent="send">
    <TextField v-model="network" label="Адрес или подсеть" placeholder="например: 192.168.1.10 или 192.168.1.0/24" plain :error="error" :disabled="busy" />
    <TextField v-model="note" label="Пометка" placeholder="например: RDP-1" :disabled="busy" />
    <AppButton type="submit" variant="primary" class="add-network__button" :disabled="busy">Добавить</AppButton>
  </form>
</template>

<style scoped>
.add-network {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) auto;
  align-items: start;
  gap: 12px;
}

.add-network__button {
  margin-top: 24px;
  min-height: 46px;
}

@media (max-width: 760px) {
  .add-network {
    grid-template-columns: minmax(0, 1fr);
  }

  .add-network__button {
    margin-top: 0;
  }
}
</style>
