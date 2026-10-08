<script setup lang="ts">
import { useId } from "vue";

withDefaults(
  defineProps<{
    label: string;
    type?: string;
    autocomplete?: string;
    error?: string;
    hint?: string;
    disabled?: boolean;
    required?: boolean;
    plain?: boolean;
    placeholder?: string;
    hideLabel?: boolean;
  }>(),
  { type: "text", autocomplete: "off", error: "", hint: "", disabled: false, required: false, plain: false, placeholder: undefined, hideLabel: false },
);

const model = defineModel<string>({ default: "" });
const id = useId();
</script>

<template>
  <div class="field">
    <label class="field__label" :class="{ 'visually-hidden': hideLabel }" :for="id">{{ label }}</label>
    <input
      :id="id"
      v-model="model"
      class="field__input"
      :class="{ 'field__input--invalid': error }"
      :type="type"
      :autocomplete="autocomplete"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="error || hint ? `${id}-note` : undefined"
      :autocapitalize="plain ? 'none' : undefined"
      :autocorrect="plain ? 'off' : undefined"
      :spellcheck="plain ? false : undefined"
    />
    <p v-if="error" :id="`${id}-note`" class="field__note field__note--error">{{ error }}</p>
    <p v-else-if="hint" :id="`${id}-note`" class="field__note">{{ hint }}</p>
  </div>
</template>

<style scoped>
.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field__label {
  font-size: var(--text-small);
  font-weight: 600;
}

.field__input {
  width: 100%;
  padding: 9px 11px;
  border: 1px solid var(--line);
  border-radius: var(--radius-button);
  background: var(--surface);
  color: var(--ink);
  font: inherit;
}

.field__input:disabled {
  background: var(--canvas);
  color: var(--muted);
}

.field__input--invalid {
  border-color: var(--red);
}

.field__note {
  margin: 0;
  font-size: var(--text-small);
  color: var(--muted);
}

.field__note--error {
  color: var(--red);
}
</style>
