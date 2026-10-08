<script setup lang="ts" generic="T extends string">
import { useId } from "vue";

defineProps<{ label: string; options: { value: T; label: string }[]; disabled?: boolean }>();
const model = defineModel<T>({ required: true });
const id = useId();
</script>

<template>
  <div class="choice">
    <span :id="`${id}-label`" class="choice__label">{{ label }}</span>
    <div class="choice__options" role="radiogroup" :aria-labelledby="`${id}-label`">
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        role="radio"
        class="choice__option"
        :class="{ 'choice__option--active': model === option.value }"
        :aria-checked="model === option.value"
        :disabled="disabled"
        @click="model = option.value"
      >
        {{ option.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.choice {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.choice__label {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--muted);
}

.choice__options {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: var(--radius-field);
  background: var(--field);
}

.choice__option {
  flex: 1 1 auto;
  min-height: 36px;
  padding: 6px 12px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--motion), color var(--motion);
}

.choice__option:hover:not(:disabled) {
  color: var(--ink);
}

.choice__option--active {
  background: var(--pill-raised);
  color: var(--ink);
  box-shadow: var(--card-shine);
}
</style>
