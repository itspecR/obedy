<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, useId } from "vue";
import { enterModal, isTopModal, leaveModal } from "../../composables/modalStack";
import { keepFocusInside } from "../../composables/useFocusTrap";

withDefaults(defineProps<{ title: string; wide?: boolean; huge?: boolean; eyebrow?: string }>(), { wide: false, huge: false, eyebrow: "" });
const emit = defineEmits<{ close: [] }>();

const box = ref<HTMLElement | null>(null);
const titleId = useId();

async function focusFirst(): Promise<void> {
  await nextTick();
  const target = box.value?.querySelector<HTMLElement>("input") ?? box.value?.querySelector<HTMLElement>("button");
  target?.focus();
}

let token: symbol | null = null;

function onKeydown(event: KeyboardEvent): void {
  if (!token || !isTopModal(token)) {
    return;
  }
  if (event.key === "Escape") {
    event.preventDefault();
    emit("close");
    return;
  }
  if (box.value) {
    keepFocusInside(box.value, event);
  }
}

onMounted(() => {
  token = enterModal();
  document.addEventListener("keydown", onKeydown);
  void focusFirst();
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", onKeydown);
  if (token) {
    leaveModal(token);
  }
});

defineExpose({ focusFirst });
</script>

<template>
  <div class="overlay">
    <div ref="box" class="modal" :class="{ 'modal--wide': wide, 'modal--huge': huge }" role="dialog" aria-modal="true" :aria-labelledby="titleId">
      <div class="modal__head">
        <div>
          <p v-if="eyebrow" class="eyebrow modal__eyebrow">{{ eyebrow }}</p>
          <h2 :id="titleId" class="modal__title">{{ title }}</h2>
        </div>
        <div class="modal__tools">
          <slot name="actions" />
          <button type="button" class="modal__close" aria-label="Закрыть" @click="emit('close')">×</button>
        </div>
      </div>
      <slot />
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
  background: rgba(15, 45, 105, 0.35);
}

.modal {
  width: min(460px, 100%);
  max-height: calc(100vh - 28px);
  overflow: auto;
  padding: 22px;
  border: 1px solid var(--line);
  border-radius: var(--radius-panel);
  background: var(--surface);
  animation: appear var(--motion) ease-out;
}

.modal--wide {
  width: min(620px, 100%);
}

.modal--huge {
  width: min(960px, 100%);
}

.modal__eyebrow {
  margin: 0 0 2px;
}

.modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.modal__title {
  font-size: 18px;
}

.modal__tools {
  display: flex;
  flex: none;
  align-items: center;
  gap: 8px;
}

.modal__close {
  padding: 0 4px;
  border: 0;
  background: transparent;
  color: var(--muted);
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

@keyframes appear {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
}
</style>
