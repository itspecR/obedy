<script setup lang="ts">
import { nextTick, ref, useId, watch } from "vue";
import { useConfirm } from "../../composables/useConfirm";
import { keepFocusInside } from "../../composables/useFocusTrap";
import AppButton from "./AppButton.vue";

const { current, answer } = useConfirm();
const box = ref<HTMLElement | null>(null);
const actionButton = ref<InstanceType<typeof AppButton> | null>(null);
const titleId = useId();
let returnFocusTo: HTMLElement | null = null;

watch(
  () => current.request,
  async (request) => {
    if (request) {
      returnFocusTo = document.activeElement as HTMLElement | null;
      await nextTick();
      (actionButton.value?.$el as HTMLButtonElement | undefined)?.focus();
    } else {
      returnFocusTo?.focus();
      returnFocusTo = null;
    }
  },
);

function onKeydown(event: KeyboardEvent): void {
  event.stopPropagation();
  if (event.key === "Escape") {
    event.preventDefault();
    answer(false);
    return;
  }
  if (box.value) {
    keepFocusInside(box.value, event);
  }
}
</script>

<template>
  <div v-if="current.request" class="overlay" @keydown="onKeydown">
    <div ref="box" class="confirm" role="dialog" aria-modal="true" :aria-labelledby="titleId">
      <h2 :id="titleId" class="confirm__title">{{ current.request.title }}</h2>
      <p class="confirm__text">{{ current.request.text }}</p>
      <div class="confirm__actions">
        <AppButton @click="answer(false)">Отмена</AppButton>
        <AppButton ref="actionButton" :variant="current.request.danger ? 'danger' : 'primary'" @click="answer(true)">
          {{ current.request.action }}
        </AppButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 900;
  display: grid;
  place-items: center;
  padding: 14px;
  background: rgba(24, 40, 63, 0.35);
}

.confirm {
  width: min(440px, 100%);
  padding: 22px;
  border: 1px solid var(--line);
  border-radius: var(--radius-panel);
  background: var(--surface);
  animation: appear var(--motion) ease-out;
}

.confirm__title {
  font-size: 18px;
}

.confirm__text {
  margin: 8px 0 20px;
  color: var(--muted);
}

.confirm__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@keyframes appear {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
}
</style>
