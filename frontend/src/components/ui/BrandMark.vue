<script setup lang="ts">
withDefaults(defineProps<{ onDark?: boolean; caption?: boolean }>(), { onDark: false, caption: true });
</script>

<template>
  <div :class="['brand', { 'brand--dark': onDark }]">
    <svg class="brand__sign" viewBox="0 0 48 48" aria-hidden="true">
      <rect class="brand__tile" x="1" y="1" width="46" height="46" rx="13" />
      <circle class="brand__plate" cx="24" cy="24" r="13" />
      <path class="brand__hands" d="M24 16.5V24l5 3" />
    </svg>
    <span class="brand__text">
      <span class="brand__name">Обеды</span>
      <span v-if="caption" class="brand__caption">Учёт перерывов</span>
    </span>
  </div>
</template>

<style scoped>
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand__sign {
  display: block;
  width: 44px;
  height: 44px;
  flex: none;
}

.brand__tile {
  fill: var(--blue);
}

.brand--dark .brand__tile {
  fill: var(--glass-fill);
  stroke: var(--glass-edge);
}

.brand__plate {
  fill: none;
  stroke: #fff;
  stroke-width: 2.5;
}

.brand__hands {
  fill: none;
  stroke: #fff;
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.brand__text {
  display: flex;
  flex-direction: column;
}

.brand__name {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.3px;
  color: var(--ink);
}

.brand--dark .brand__name {
  color: #fff;
}

.brand__caption {
  margin-top: 3px;
  font-size: 11px;
  color: var(--muted);
}

.brand--dark .brand__caption {
  color: var(--login-art-caption);
}
</style>
