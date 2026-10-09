<script setup lang="ts">
import { useToasts } from "../../composables/useToasts";

const { items, dismiss } = useToasts();
</script>

<template>
  <TransitionGroup tag="div" name="toast" class="toasts">
    <div
      v-for="toast in items"
      :key="toast.id"
      :class="['toast', `toast--${toast.kind}`]"
      :role="toast.kind === 'error' ? 'alert' : 'status'"
    >
      <span>{{ toast.text }}</span>
      <button v-if="toast.kind === 'error'" type="button" class="toast__close" aria-label="Закрыть уведомление" @click="dismiss(toast.id)">×</button>
    </div>
  </TransitionGroup>
</template>

<style scoped>
.toasts {
  position: fixed;
  left: 50%;
  bottom: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: min(560px, calc(100vw - 28px));
  transform: translateX(-50%);
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-menu);
  background: var(--toast);
  color: var(--ink);
  box-shadow: var(--shadow-menu);
  pointer-events: auto;
}

.toast-enter-active {
  transition: opacity var(--motion) ease-out, transform var(--motion) ease-out;
}

.toast-leave-active {
  transition: opacity 0.6s ease, transform 0.6s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.toast-move {
  transition: transform var(--motion) ease;
}

.toast--error {
  background: var(--toast-error);
}

.toast__close {
  margin-left: auto;
  padding: 0 4px;
  border: 0;
  background: transparent;
  color: #fff;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
}
</style>
