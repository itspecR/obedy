<script setup lang="ts">
import InfoTip from "./InfoTip.vue";

defineProps<{ title: string; info?: string; titleId?: string }>();
</script>

<template>
  <div class="block-title">
    <h2 :id="titleId" class="block-title__text">{{ title }}</h2>
    <InfoTip v-if="info" :text="info" :label="title" />
  </div>
</template>

<style scoped>
.block-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.block-title__text {
  font-size: var(--text-h3);
}
</style>
