<script setup lang="ts">
import ChoiceField from "../ui/ChoiceField.vue";
import TextField from "../ui/TextField.vue";
import { ROLE_OPTIONS, STATUS_OPTIONS, type StaffFilter } from "./filters";

const filter = defineModel<StaffFilter>({ required: true });
</script>

<template>
  <div class="panel filters">
    <TextField v-model="filter.query" label="Поиск" icon="search" placeholder="например: Иванов, склад или ivanov" plain />
    <div class="filters__choices">
      <ChoiceField v-model="filter.role" label="Роль" :options="ROLE_OPTIONS" />
      <ChoiceField v-model="filter.status" label="Статус" :options="STATUS_OPTIONS" />
    </div>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 20px;
}

.filters__choices {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px;
}

@media (max-width: 900px) {
  .filters__choices {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 650px) {
  .filters {
    padding: 16px;
  }
}
</style>
