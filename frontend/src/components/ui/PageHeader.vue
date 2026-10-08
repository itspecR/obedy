<script setup lang="ts">
defineProps<{ title: string; subtitle?: string }>();
</script>

<template>
  <header class="page-head">
    <div class="page-head__text">
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="page-head__subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.default" class="page-head__actions"><slot /></div>
  </header>
</template>

<style scoped>
.page-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

.page-head__text {
  min-width: 0;
}

.page-head__subtitle {
  margin: 2px 0 0;
  color: var(--muted);
}

.page-head__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
