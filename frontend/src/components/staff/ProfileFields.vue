<script setup lang="ts">
import type { Profile } from "../../api/staff";
import TextField from "../ui/TextField.vue";

defineProps<{ disabled?: boolean }>();
const profile = defineModel<Profile>({ required: true });
</script>

<template>
  <TextField v-model="profile.full_name" label="ФИО" placeholder="например: Иванова Анна Сергеевна" :disabled="disabled" />
</template>
