<script setup lang="ts">
import { useId } from "vue";

defineProps<{ label: string; hint?: string; checked: boolean; disabled?: boolean }>();
const emit = defineEmits<{ change: [value: boolean] }>();
const id = useId();
</script>

<template>
  <div class="switch-field">
    <div class="switch-field__text">
      <span :id="`${id}-label`" class="switch-field__label">{{ label }}</span>
      <span v-if="hint" :id="`${id}-hint`" class="switch-field__hint">{{ hint }}</span>
    </div>
    <button
      type="button"
      role="switch"
      class="switch"
      :class="{ 'switch--on': checked }"
      :aria-checked="checked"
      :aria-labelledby="`${id}-label`"
      :aria-describedby="hint ? `${id}-hint` : undefined"
      :disabled="disabled"
      @click="emit('change', !checked)"
    >
      <span class="switch__knob" />
    </button>
  </div>
</template>

<style scoped>
.switch-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.switch-field__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.switch-field__label {
  font-weight: 600;
}

.switch-field__hint {
  font-size: var(--text-small);
  color: var(--muted);
}

.switch {
  position: relative;
  width: 50px;
  height: 30px;
  flex: none;
  padding: 0;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: var(--field);
  cursor: pointer;
  transition: background var(--motion), border-color var(--motion);
}

.switch--on {
  border-color: transparent;
  background: var(--green);
}

.switch:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.switch__knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  transition: transform var(--motion);
}

.switch--on .switch__knob {
  transform: translateX(20px);
}
</style>
