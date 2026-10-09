<script setup lang="ts">
defineProps<{ open: boolean }>();
</script>

<template>
  <span class="rabbit-hole" :class="{ 'rabbit-hole--open': open }" aria-hidden="true" />
</template>

<style scoped>
.rabbit-hole {
  position: absolute;
  width: var(--hole-width, 120px);
  height: calc(var(--hole-width, 120px) / 4);
  border-radius: 50%;
  background: radial-gradient(closest-side, #000 62%, #0a1222 78%, rgba(110, 168, 255, 0.85) 94%, rgba(110, 168, 255, 0) 100%);
  box-shadow: 0 0 22px rgba(110, 168, 255, 0.45);
  transform: translate(-50%, -50%) scale(0);
  transition: transform 260ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.rabbit-hole--open {
  transform: translate(-50%, -50%) scale(1);
}
</style>
