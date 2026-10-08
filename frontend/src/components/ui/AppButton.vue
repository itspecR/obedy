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
  min-height: 42px;
  padding: 10px 16px;
  border: 1px solid var(--line);
  border-radius: var(--radius-button);
  background: var(--field);
  color: var(--ink);
  font: inherit;
  font-weight: 600;
  line-height: 1.2;
  cursor: pointer;
  transition: background var(--motion), transform var(--motion), border-color var(--motion), box-shadow var(--motion);
}

.button:hover:not(:disabled) {
  border-color: var(--line-strong);
  background: var(--hover);
}

.button:active:not(:disabled) {
  transform: translateY(1px);
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.button--small {
  min-height: 32px;
  padding: 6px 12px;
  font-size: var(--text-small);
}

.button--block {
  width: 100%;
}

.button--primary {
  min-height: 48px;
  border-color: transparent;
  background: var(--primary);
  color: var(--primary-ink);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35), inset 0 -1px 0 rgba(0, 0, 0, 0.08);
}

.button--primary:hover:not(:disabled) {
  border-color: transparent;
  background: var(--primary-hover);
}

.button--danger {
  border-color: var(--red-strong);
  background: var(--red-strong);
  color: #fff;
}

.button--danger:hover:not(:disabled) {
  border-color: var(--red-strong-hover);
  background: var(--red-strong-hover);
}

.button--ghost {
  border-color: transparent;
  background: transparent;
  color: var(--blue);
}

.button--ghost:hover:not(:disabled) {
  border-color: transparent;
  background: var(--blue-tint);
}

.button--pressed {
  border-color: var(--blue);
  background: var(--blue-tint);
  color: var(--blue);
}
</style>
