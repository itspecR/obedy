<script setup lang="ts">
export type IconName = "lunch" | "logout";

defineProps<{ name: IconName }>();
</script>

<template>
  <svg class="icon" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <template v-if="name === 'lunch'">
      <circle cx="10" cy="10" r="6.75" />
      <circle cx="10" cy="10" r="3.75" />
      <path d="M2 3.5v4M2 5.5h1.5M3.5 3.5v4M2.75 7.5v9" />
      <path d="M18 3.5c-1.1.6-1.6 2-1.6 3.6v2.4H18M18 3.5v13" />
    </template>
    <template v-else>
      <path d="M8 3.5H4.75a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1H8" />
      <path d="M12.5 13.5 16 10l-3.5-3.5" />
      <path d="M16 10H8" />
    </template>
  </svg>
</template>

<style scoped>
.icon {
  flex: none;
}
</style>
