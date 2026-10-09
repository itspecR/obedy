<script setup lang="ts">
import { useId } from "vue";
import InfoTip from "./InfoTip.vue";

withDefaults(defineProps<{ label: string; hint?: string; placeholder?: string; rows?: number; disabled?: boolean; code?: boolean }>(), {
  hint: "",
  code: true,
  placeholder: undefined,
  rows: 4,
  disabled: false,
});
const model = defineModel<string>({ default: "" });
const id = useId();
</script>

<template>
  <div class="area">
    <div class="area__head">
      <label class="area__label" :for="id">{{ label }}</label>
      <InfoTip v-if="hint" :text="hint" :label="label" />
    </div>
    <textarea
      :id="id"
      v-model="model"
      class="area__input"
      :class="code ? 'code' : 'area__input--text'"
      :rows="rows"
      :placeholder="placeholder"
      :disabled="disabled"
      spellcheck="false"
    />
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

.area__input--text {
  font-family: var(--font-sans);
  font-size: 15px;
}

.area__input::placeholder {
  color: var(--placeholder);
}

.area__input:focus {
  border-color: var(--blue);
  box-shadow: 0 0 0 3px var(--blue-tint);
}

.area__head {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
