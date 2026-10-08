<script setup lang="ts">
import { useId } from "vue";

withDefaults(defineProps<{ label: string; hint?: string; placeholder?: string; rows?: number; disabled?: boolean }>(), {
  hint: "",
  placeholder: undefined,
  rows: 4,
  disabled: false,
});
const model = defineModel<string>({ default: "" });
const id = useId();
</script>

<template>
  <div class="area">
    <label class="area__label" :for="id">{{ label }}</label>
    <textarea
      :id="id"
      v-model="model"
      class="area__input code"
      :rows="rows"
      :placeholder="placeholder"
      :disabled="disabled"
      :aria-describedby="hint ? `${id}-hint` : undefined"
      spellcheck="false"
    />
    <p v-if="hint" :id="`${id}-hint`" class="area__hint">{{ hint }}</p>
  </div>
</template>

<style scoped>
.area {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.area__label {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--muted);
}

.area__input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-field);
  background: var(--field);
  color: var(--ink);
  font-size: var(--text-small);
  resize: vertical;
  outline: none;
  transition: border-color var(--motion), box-shadow var(--motion);
}

.area__input:focus {
  border-color: var(--blue);
  box-shadow: 0 0 0 3px var(--blue-tint);
}

.area__hint {
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}
</style>
