<script setup lang="ts">
withDefaults(defineProps<{ caption?: boolean }>(), { caption: true });
</script>

<template>
  <div class="brand">
    <span class="brand__sign" aria-hidden="true">
      <svg viewBox="0 0 48 48">
        <circle class="brand__rim" cx="24" cy="24" r="20" />
        <path class="brand__ticks" d="M24 7v4M24 37v4M7 24h4M37 24h4" />
        <path class="brand__hands" d="M24 15v9l6 3.5" />
      </svg>
    </span>
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
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  flex: none;
}

.brand__sign svg {
  width: 100%;
  height: 100%;
  fill: none;
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.brand__rim,
.brand__ticks {
  stroke: var(--accent);
}

.brand__hands {
  stroke: var(--brand);
  stroke-width: 2.8;
}

.brand__text {
  display: flex;
  flex-direction: column;
}

.brand__name {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.3px;
  color: var(--ink);
}

.brand__caption {
  margin-top: 3px;
  font-size: 11px;
  color: var(--muted);
}
</style>
