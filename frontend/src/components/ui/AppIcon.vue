<script setup lang="ts">
export type IconName = "lunch" | "logout" | "user" | "users" | "search" | "lock" | "eye" | "eye-off" | "shield" | "server" | "clock" | "board" | "chart" | "calendar";

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
    <template v-else-if="name === 'calendar'">
      <rect x="3.25" y="4.25" width="13.5" height="12.5" rx="2" />
      <path d="M3.25 8.25h13.5M7 2.75v3M13 2.75v3" />
    </template>
    <template v-else-if="name === 'chart'">
      <path d="M3.25 16.75h13.5" />
      <path d="M5.75 13.5v-3.75M10 13.5V5.25M14.25 13.5V8.5" />
    </template>
    <template v-else-if="name === 'board'">
      <rect x="2.75" y="3.75" width="14.5" height="12.5" rx="2" />
      <path d="M2.75 8h14.5M7.5 8v8.25" />
    </template>
    <template v-else-if="name === 'clock'">
      <circle cx="10" cy="10" r="7.25" />
      <path d="M10 5.75V10l2.75 1.75" />
    </template>
    <template v-else-if="name === 'shield'">
      <path d="M10 2.75 16 5v4.6c0 3.6-2.5 6.4-6 7.65-3.5-1.25-6-4.05-6-7.65V5z" />
      <path d="m7.5 10 1.75 1.75L12.75 8.5" />
    </template>
    <template v-else-if="name === 'server'">
      <rect x="3.25" y="3.5" width="13.5" height="5.25" rx="1.5" />
      <rect x="3.25" y="11.25" width="13.5" height="5.25" rx="1.5" />
      <path d="M6.25 6.1h.01M6.25 13.9h.01M9.25 6.1h4.5M9.25 13.9h4.5" />
    </template>
    <template v-else-if="name === 'user'">
      <circle cx="10" cy="7" r="3.25" />
      <path d="M3.75 16.5c.6-3 3.2-4.75 6.25-4.75s5.65 1.75 6.25 4.75" />
    </template>
    <template v-else-if="name === 'users'">
      <circle cx="7.5" cy="7" r="2.75" />
      <path d="M2.5 16c.5-2.6 2.5-4.25 5-4.25s4.5 1.65 5 4.25" />
      <path d="M12.75 4.6a2.75 2.75 0 0 1 0 5.1M14.25 11.9c1.7.45 2.9 1.9 3.25 4.1" />
    </template>
    <template v-else-if="name === 'search'">
      <circle cx="8.75" cy="8.75" r="5.25" />
      <path d="m12.6 12.6 4.15 4.15" />
    </template>
    <template v-else-if="name === 'lock'">
      <rect x="4" y="8.75" width="12" height="8" rx="2" />
      <path d="M6.75 8.75V6.5a3.25 3.25 0 0 1 6.5 0v2.25" />
    </template>
    <template v-else-if="name === 'eye'">
      <path d="M1.75 10S4.75 4.5 10 4.5 18.25 10 18.25 10 15.25 15.5 10 15.5 1.75 10 1.75 10Z" />
      <circle cx="10" cy="10" r="2.5" />
    </template>
    <template v-else-if="name === 'eye-off'">
      <path d="M8.2 4.7A8.3 8.3 0 0 1 10 4.5c5.25 0 8.25 5.5 8.25 5.5a14 14 0 0 1-2.2 2.9M5.6 5.9A13.7 13.7 0 0 0 1.75 10S4.75 15.5 10 15.5a8 8 0 0 0 4.3-1.25" />
      <path d="M8.25 8.25a2.5 2.5 0 0 0 3.5 3.5" />
      <path d="M2.5 2.5l15 15" />
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
