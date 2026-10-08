<script setup lang="ts" generic="T extends string">
import { useId } from "vue";

defineProps<{ label: string; options: { value: T; label: string }[]; disabled?: boolean }>();
const model = defineModel<T>({ required: true });
const id = useId();
</script>

<template>
  <div class="select-field">
    <label class="select-field__label" :for="id">{{ label }}</label>
    <select :id="id" v-model="model" class="select-field__input" :disabled="disabled">
      <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
    </select>
  </div>
</template>

<style scoped>
.select-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.select-field__label {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--muted);
}

.select-field__input {
  min-height: 46px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-field);
  background: var(--field-solid);
  color: var(--ink);
  font: inherit;
  font-size: 15px;
  outline: none;
  transition: border-color var(--motion), box-shadow var(--motion);
}

.select-field__input:focus {
  border-color: var(--blue);
  box-shadow: 0 0 0 3px var(--blue-tint);
}

.select-field__input:disabled {
  opacity: 0.6;
}
</style>
