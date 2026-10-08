<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "danger" | "ghost";
    size?: "normal" | "small";
    type?: "button" | "submit";
    block?: boolean;
    disabled?: boolean;
    pressed?: boolean;
  }>(),
  { variant: "secondary", size: "normal", type: "button", block: false, disabled: false, pressed: undefined },
);
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    :aria-pressed="pressed"
    :class="['button', `button--${variant}`, `button--${size}`, { 'button--block': block, 'button--pressed': pressed }]"
  >
    <slot />
  </button>
</template>

<style scoped>
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-button);
  background: var(--surface);
  color: var(--ink);
  font: inherit;
  font-weight: 600;
  line-height: 1.2;
  cursor: pointer;
  transition: background var(--motion), transform var(--motion), border-color var(--motion);
}

.button:hover:not(:disabled) {
  background: var(--hover);
}

.button:active:not(:disabled) {
  transform: translateY(1px);
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.button--small {
  padding: 6px 10px;
  font-size: var(--text-small);
}

.button--block {
  width: 100%;
}

.button--primary {
  border-color: var(--blue);
  background: var(--blue);
  color: #fff;
}

.button--primary:hover:not(:disabled) {
  border-color: var(--blue-hover);
  background: var(--blue-hover);
}

.button--danger {
  border-color: var(--red);
  background: var(--red);
  color: #fff;
}

.button--danger:hover:not(:disabled) {
  border-color: #9a3240;
  background: #9a3240;
}

.button--ghost {
  border-color: transparent;
  background: transparent;
  color: var(--blue);
}

.button--pressed {
  border-color: var(--blue);
  background: var(--blue-tint);
  color: var(--blue);
}
</style>
