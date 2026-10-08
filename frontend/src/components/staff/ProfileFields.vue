<script setup lang="ts">
import type { Profile } from "../../api/staff";
import TextField from "../ui/TextField.vue";

defineProps<{ disabled?: boolean }>();
const profile = defineModel<Profile>({ required: true });
</script>

<template>
  <TextField v-model="profile.full_name" label="ФИО" placeholder="например: Иванова Анна Сергеевна" :disabled="disabled" />
  <div class="profile-fields__row">
    <TextField v-model="profile.department" label="Отдел" placeholder="например: Бухгалтерия" :disabled="disabled" />
    <TextField v-model="profile.position" label="Должность" placeholder="например: Кассир" :disabled="disabled" />
  </div>
</template>

<style scoped>
.profile-fields__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px;
}

@media (max-width: 650px) {
  .profile-fields__row {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
