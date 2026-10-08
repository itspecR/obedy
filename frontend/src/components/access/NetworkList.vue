<script setup lang="ts">
import type { AllowedNetwork } from "../../api/access";
import AppButton from "../ui/AppButton.vue";

defineProps<{ networks: AllowedNetwork[]; busy: boolean }>();
const emit = defineEmits<{ remove: [network: AllowedNetwork] }>();
</script>

<template>
  <ul v-if="networks.length" class="networks">
    <li v-for="item in networks" :key="item.id" class="networks__row">
      <span class="code networks__address">{{ item.network }}</span>
      <span class="networks__note">{{ item.note || "Без пометки" }}</span>
      <AppButton size="small" :disabled="busy" :aria-label="`Убрать ${item.network}`" @click="emit('remove', item)">Убрать</AppButton>
    </li>
  </ul>
  <div v-else class="networks__empty">
    <p class="networks__empty-title">Список пуст</p>
    <p class="networks__empty-text">Добавьте адреса RDP-серверов и компьютеров, с которых должен открываться сайт.</p>
  </div>
</template>

<style scoped>
.networks {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  list-style: none;
}

.networks__row {
  display: grid;
  grid-template-columns: minmax(140px, auto) minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 12px 4px;
  border-top: 1px solid var(--line);
}

.networks__row:first-child {
  border-top: 0;
}

.networks__address {
  font-size: 15px;
}

.networks__note {
  min-width: 0;
  overflow: hidden;
  color: var(--muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.networks__empty {
  padding: 20px 4px 8px;
  text-align: center;
}

.networks__empty-title {
  margin: 0 0 4px;
  font-weight: 600;
}

.networks__empty-text {
  margin: 0;
  color: var(--muted);
}

@media (max-width: 650px) {
  .networks__row {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 4px 12px;
  }

  .networks__note {
    grid-row: 2;
  }

  .networks__row :deep(.button) {
    grid-row: 1 / span 2;
    grid-column: 2;
  }
}
</style>
