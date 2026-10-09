<script setup lang="ts">
defineProps<{ checked: boolean; label: string; disabled?: boolean }>();
const emit = defineEmits<{ change: [checked: boolean] }>();
</script>

<template>
  <input
    type="checkbox"
    class="check"
    :checked="checked"
    :aria-label="label"
    :disabled="disabled"
    @change="emit('change', ($event.target as HTMLInputElement).checked)"
  />
</template>

<style scoped>
.check {
  display: inline-grid;
  place-content: center;
  flex: none;
  width: 20px;
  height: 20px;
  margin: 0;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background: var(--field);
  cursor: pointer;
  appearance: none;
  transition: background var(--motion), border-color var(--motion);
}

.check::after {
  width: 10px;
  height: 6px;
  border-bottom: 2px solid var(--ink);
  border-left: 2px solid var(--ink);
  content: "";
  opacity: 0;
  transform: translateY(-1px) rotate(-45deg);
}

.check:checked {
  border-color: var(--blue);
  background: var(--blue);
}

.check:checked::after {
  opacity: 1;
}

.check:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

.check:disabled {
  cursor: default;
  opacity: 0.5;
}
</style>
