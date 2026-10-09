<script setup lang="ts">
import { computed, ref, useId } from "vue";
import AppIcon, { type IconName } from "./AppIcon.vue";
import InfoTip from "./InfoTip.vue";

const props = withDefaults(
  defineProps<{
    label: string;
    type?: string;
    autocomplete?: string;
    error?: string;
    invalid?: boolean;
    hint?: string;
    disabled?: boolean;
    required?: boolean;
    plain?: boolean;
    placeholder?: string;
    hideLabel?: boolean;
    icon?: IconName;
  }>(),
  { type: "text", autocomplete: "off", error: "", invalid: false, hint: "", disabled: false, required: false, plain: false, placeholder: undefined, hideLabel: false, icon: undefined },
);

const model = defineModel<string>({ default: "" });
const id = useId();
const revealed = ref(false);
const isPassword = computed(() => props.type === "password");
const inputType = computed(() => (isPassword.value && revealed.value ? "text" : props.type));
const marked = computed(() => Boolean(props.error) || props.invalid);
const revealLabel = computed(() => (revealed.value ? "Скрыть пароль" : "Показать пароль"));
</script>

<template>
  <div class="field">
    <div class="field__head" :class="{ 'visually-hidden': hideLabel }">
      <label class="field__label" :for="id">{{ label }}</label>
      <InfoTip v-if="hint" :text="hint" :label="label" />
    </div>
    <div class="field__box" :class="{ 'field__box--invalid': marked, 'field__box--disabled': disabled }">
      <AppIcon v-if="icon" :name="icon" class="field__icon" />
      <input
        :id="id"
        v-model="model"
        class="field__input"
        :type="inputType"
        :autocomplete="autocomplete"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :aria-invalid="marked ? 'true' : undefined"
        :aria-describedby="error ? `${id}-note` : undefined"
        :autocapitalize="plain || isPassword ? 'none' : undefined"
        :autocorrect="plain || isPassword ? 'off' : undefined"
        :spellcheck="plain || isPassword ? false : undefined"
      />
      <button
        v-if="isPassword"
        type="button"
        class="field__reveal"
        :aria-label="revealLabel"
        :aria-pressed="revealed"
        :aria-controls="id"
        :disabled="disabled"
        @click="revealed = !revealed"
      >
        <AppIcon :name="revealed ? 'eye-off' : 'eye'" />
      </button>
    </div>
    <p v-if="error" :id="`${id}-note`" class="field__note field__note--error">{{ error }}</p>
  </div>
</template>

<style scoped>
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field__head {
  display: flex;
  align-items: center;
  gap: 6px;
}

.field__label {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--muted);
}

.field__box {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 46px;
  padding: 0 6px 0 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-field);
  background: var(--field);
  transition: border-color var(--motion), background var(--motion), box-shadow var(--motion);
}

.field__box:focus-within {
  border-color: var(--blue);
  background: var(--field-focus);
  box-shadow: 0 0 0 3px var(--blue-tint);
}

.field__box--invalid,
.field__box--invalid:focus-within {
  border-color: var(--red);
}

.field__box--invalid:focus-within {
  box-shadow: 0 0 0 3px var(--red-bg);
}

.field__box--disabled {
  opacity: 0.6;
}

.field__icon {
  color: var(--muted);
}

.field__input {
  flex: 1;
  min-width: 0;
  padding: 11px 8px 11px 0;
  border: 0;
  background: transparent;
  color: var(--ink);
  font: inherit;
  font-size: 15px;
  outline: none;
}

.field__input::placeholder {
  color: var(--placeholder);
}

.field__reveal {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  flex: none;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  transition: background var(--motion), color var(--motion);
}

.field__reveal:hover:not(:disabled) {
  background: var(--hover);
  color: var(--ink);
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
