<script setup lang="ts">
import { computed } from "vue";

const SEED = 20;

const props = defineProps<{ x: number; y: number; duration: number }>();

const style = computed(() => {
  const reach = Math.hypot(Math.max(props.x, window.innerWidth - props.x), Math.max(props.y, window.innerHeight - props.y));
  return {
    left: `${props.x}px`,
    top: `${props.y}px`,
    width: `${SEED}px`,
    height: `${SEED}px`,
    "--cover": String((2 * reach) / SEED),
    "--duration": `${props.duration}ms`,
  };
});
</script>

<template>
  <span class="screen-fill" :style="style" aria-hidden="true" />
</template>

<style scoped>
.screen-fill {
  position: fixed;
  z-index: 1000;
  border-radius: 50%;
  background: #000;
  pointer-events: none;
  transform: translate(-50%, -50%) scale(var(--cover));
  animation: screen-fill var(--duration) cubic-bezier(0.4, 0, 1, 1) both;
}

@keyframes screen-fill {
  from {
    transform: translate(-50%, -50%) scale(0);
  }
}
</style>
