<script setup lang="ts">
import { computed, ref, useId, watch } from "vue";
import { usePopover } from "../../composables/usePopover";
import { matchesQuery } from "../../format/search";

export interface PickerPerson {
  id: number;
  name: string;
  login: string;
}

const props = withDefaults(defineProps<{ label: string; people: PickerPerson[]; placeholder?: string; disabled?: boolean }>(), {
  placeholder: "Начните вводить ФИО или логин",
  disabled: false,
});
const model = defineModel<number | null>({ default: null });

const root = ref<HTMLElement | null>(null);
const { open, place, show, close } = usePopover(root, "stretch");
const id = useId();
const text = ref("");
const typed = ref(false);
const active = ref(0);

const chosen = computed(() => props.people.find((person) => person.id === model.value) ?? null);
const shown = computed(() => (typed.value ? props.people.filter((person) => matchesQuery(text.value, [person.name, person.login])) : props.people));
const activeId = computed(() => (open.value && shown.value[active.value] ? `${id}-option-${shown.value[active.value].id}` : undefined));

function onInput(): void {
  typed.value = true;
  active.value = 0;
  if (chosen.value && text.value !== chosen.value.name) {
    model.value = null;
  }
  show();
}

function pick(person: PickerPerson): void {
  model.value = person.id;
  text.value = person.name;
  typed.value = false;
  close();
}

function move(delta: number): void {
  if (!open.value) {
    show();
    return;
  }
  const count = shown.value.length;
  active.value = count ? (active.value + delta + count) % count : 0;
}

function onKey(event: KeyboardEvent): void {
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    move(event.key === "ArrowDown" ? 1 : -1);
  } else if (event.key === "Enter" && open.value && shown.value[active.value]) {
    event.preventDefault();
    pick(shown.value[active.value]);
  } else if (event.key === "Escape" && open.value) {
    event.stopPropagation();
    close();
  }
}

watch(
  chosen,
  (person) => {
    if (person && !typed.value) {
      text.value = person.name;
    }
  },
  { immediate: true },
);
</script>

<template>
  <div ref="root" class="picker">
    <label class="field-label" :for="id">{{ label }}</label>
    <input
      :id="id"
      v-model="text"
      class="field-control picker__input"
      :class="{ 'field-control--open': open }"
      type="text"
      role="combobox"
      autocomplete="off"
      spellcheck="false"
      aria-autocomplete="list"
      :aria-expanded="open"
      :aria-controls="`${id}-list`"
      :aria-activedescendant="activeId"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="onInput"
      @click="show"
      @keydown="onKey"
      @blur="close"
    />
    <ul v-if="open" :id="`${id}-list`" class="popover picker__list" :style="place" role="listbox" :aria-label="label">
      <li
        v-for="(person, index) in shown"
        :id="`${id}-option-${person.id}`"
        :key="person.id"
        class="picker__option"
        :class="{ 'picker__option--active': index === active, 'picker__option--chosen': person.id === model }"
        role="option"
        :aria-selected="person.id === model"
        @mousedown.prevent="pick(person)"
        @mousemove="active = index"
      >
        <span class="picker__name">{{ person.name }}</span>
        <span class="picker__login code">{{ person.login }}</span>
      </li>
      <li v-if="!shown.length" class="picker__empty">Никого не нашли</li>
    </ul>
  </div>
</template>

<style scoped>
.picker {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.picker__input {
  cursor: text;
}

.picker__input::placeholder {
  color: var(--placeholder);
}

.picker__list {
  max-height: 280px;
  margin: 0;
  padding: 6px;
  overflow-y: auto;
  list-style: none;
}

.picker__option {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 12px;
  border-radius: var(--radius-button);
  cursor: pointer;
}

.picker__option--active {
  background: var(--hover-menu);
}

.picker__option--chosen {
  color: var(--blue-hover);
}

.picker__name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker__login {
  flex: none;
  font-size: var(--text-small);
  color: var(--muted);
}

.picker__empty {
  padding: 9px 12px;
  color: var(--muted);
}
</style>
