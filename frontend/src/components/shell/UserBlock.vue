<script setup lang="ts">
import { computed } from "vue";
import type { Me } from "../../api/auth";
import { initials, shortName } from "../../navigation";

const props = defineProps<{ me: Me }>();
const emit = defineEmits<{ open: [] }>();

const name = computed(() => shortName(props.me.display_name));
</script>

<template>
  <button type="button" class="user" aria-label="Открыть профиль" @click="emit('open')">
    <span class="user__avatar" aria-hidden="true">{{ initials(me.display_name) }}</span>
    <span class="user__name">{{ name }}</span>
  </button>
</template>

<style scoped>
.user {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius-panel);
  background: var(--field);
  color: var(--ink);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: background var(--motion), border-color var(--motion);
}

.user:hover {
  border-color: var(--line-strong);
  background: var(--hover);
}

.user:active {
  transform: translateY(1px);
}

.user__avatar {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  flex: none;
  border-radius: 50%;
  background: var(--blue-tint);
  color: var(--brand);
  font-size: var(--text-small);
  font-weight: 700;
}

.user__name {
  min-width: 0;
  overflow: hidden;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
