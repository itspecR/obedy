<script setup lang="ts">
withDefaults(defineProps<{ caption?: boolean }>(), { caption: true });
</script>

<template>
  <div class="brand">
    <span class="brand__sign" aria-hidden="true">
      <svg viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="7.5" />
        <path d="M12 7.75V12l3 1.75" />
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
  border: 1px solid var(--line-strong);
  border-radius: 13px;
  background:
    radial-gradient(circle at 30% 20%, rgba(130, 200, 255, 0.45), transparent 60%),
    linear-gradient(150deg, #2c2f38 0%, #111216 100%);
  box-shadow: var(--card-shine);
}

.brand__sign svg {
  width: 24px;
  height: 24px;
  fill: none;
  stroke: #fff;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
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
