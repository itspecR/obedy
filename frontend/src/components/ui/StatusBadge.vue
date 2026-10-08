<script setup lang="ts">
import type { Tone } from "./tone";

defineProps<{ tone: Tone; label: string }>();
</script>

<template>
  <span class="badge" :class="`badge--${tone}`">{{ label }}</span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border: 1px solid var(--gray-line);
  border-radius: 999px;
  background: var(--gray-bg);
  color: var(--muted);
  font-size: var(--text-small);
  white-space: nowrap;
}

.badge--ok {
  border-color: var(--green-line);
  background: var(--green-bg);
  color: var(--green);
}

.badge--attention {
  border-color: var(--amber-line);
  background: var(--amber-bg);
  color: var(--amber);
}

.badge--alarm {
  border-color: var(--red-line);
  background: var(--red-bg);
  color: var(--red);
}
</style>
