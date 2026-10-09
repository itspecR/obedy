<script setup lang="ts">
import { ref, useId } from "vue";
import { usePopover } from "../../composables/usePopover";

export interface MenuItem {
  key: string;
  label: string;
  danger?: boolean;
}

defineProps<{ label: string; items: MenuItem[] }>();
const emit = defineEmits<{ select: [key: string] }>();

const root = ref<HTMLElement | null>(null);
const { open, toggle, close, closeOnEscape } = usePopover(root);
const id = useId();

function choose(key: string): void {
  close();
  emit("select", key);
}
</script>

<template>
  <div ref="root" class="more" @keydown="closeOnEscape">
    <button type="button" class="more__button" :aria-label="label" aria-haspopup="menu" :aria-expanded="open" :aria-controls="`${id}-menu`" @click="toggle">⋯</button>
    <div v-if="open" :id="`${id}-menu`" class="popover more__menu" role="menu" :aria-label="label">
      <button
        v-for="item in items"
        :key="item.key"
        type="button"
        role="menuitem"
        class="more__item"
        :class="{ 'more__item--danger': item.danger }"
        @click="choose(item.key)"
      >
        {{ item.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.more {
  position: relative;
}

.more__button {
  width: 36px;
  height: 32px;
  border: 1px solid transparent;
  border-radius: var(--radius-button);
  background: transparent;
  color: var(--muted);
  font-size: 18px;
  cursor: pointer;
  transition: background var(--motion), color var(--motion);
}

.more__button:hover,
.more__button[aria-expanded="true"] {
  background: var(--hover);
  color: var(--ink);
}

.more__menu {
  right: 0;
  left: auto;
  display: flex;
  flex-direction: column;
  min-width: 200px;
  padding: 6px;
}

.more__item {
  padding: 9px 12px;
  border: 0;
  border-radius: var(--radius-button);
  background: transparent;
  color: var(--ink);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.more__item:hover,
.more__item:focus-visible {
  background: var(--hover-menu);
  outline: none;
}

.more__item--danger {
  color: var(--red);
}
</style>
