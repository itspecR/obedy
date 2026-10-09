<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { Me } from "../../api/auth";
import { useGlassNav } from "../../composables/useGlassNav";
import { SECTIONS_BY_ROLE } from "../../navigation";
import AppIcon from "../ui/AppIcon.vue";
import BrandMark from "../ui/BrandMark.vue";
import GlassPill from "../ui/GlassPill.vue";
import UserBlock from "./UserBlock.vue";

const props = defineProps<{ me: Me }>();
const emit = defineEmits<{ logout: []; openProfile: [] }>();

const sections = computed(() => SECTIONS_BY_ROLE[props.me.role]);
const route = useRoute();
const router = useRouter();
const nav = ref<HTMLElement | null>(null);
const side = ref<HTMLElement | null>(null);
const glass = useGlassNav(nav, {
  items: ":scope > a.side__item",
  isActive: (item) => item.classList.contains("side__item--active"),
  select: (item) => void router.push(item.getAttribute("href") ?? "/"),
  changes: () => [route.path, sections.value],
  area: side,
});
</script>

<template>
  <aside ref="side" class="side">
    <div class="side__top">
      <BrandMark class="side__brand" />
      <nav
        ref="nav"
        class="side__nav"
        aria-label="Разделы"
        @pointerover="glass.on.over"
        @pointermove="glass.on.move"
        @pointerleave="glass.on.leave"
        @pointerdown="glass.on.down"
        @pointerup="glass.on.up"
        @pointercancel="glass.on.up"
        @click.capture="glass.on.click"
        @contextmenu="glass.on.contextMenu"
        @keydown="glass.on.keydown"
        @focusin="glass.on.focusin"
        @focusout="glass.on.focusout"
      >
        <GlassPill :pill="glass.hovered.pill" tone="hover" />
        <GlassPill :pill="glass.active.pill">
          <span class="side__copy">
            <span v-for="item in sections" :key="item.name" class="side__item" :class="{ 'side__item--active': route.path.startsWith(item.path) }">
              <AppIcon :name="item.icon" />
              <span class="side__label">{{ item.label }}</span>
            </span>
          </span>
        </GlassPill>
        <RouterLink v-for="item in sections" :key="item.name" :to="item.path" class="side__item" active-class="side__item--active" draggable="false">
          <AppIcon :name="item.icon" />
          <span class="side__label">{{ item.label }}</span>
        </RouterLink>
      </nav>
    </div>
    <div class="side__bottom">
      <UserBlock class="side__user" :me="me" @open="emit('openProfile')" />
      <button type="button" class="side__item side__logout" @click="emit('logout')">
        <AppIcon name="logout" />
        <span class="side__label">Выйти</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.side {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 24px;
  height: 100vh;
  padding: 24px 16px;
  border-right: 1px solid var(--line);
  background: var(--surface-glass);
}

.side__top,
.side__bottom {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.side__nav {
  position: relative;
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.side__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border: 0;
  border-radius: 999px;
  background: none;
  color: var(--ink);
  font: inherit;
  text-align: left;
  text-decoration: none;
  cursor: pointer;
  transition: background var(--motion), color var(--motion);
}

.side__item:hover {
  background: var(--hover-menu);
}

.side__nav {
  user-select: none;
  -webkit-user-select: none;
}

.side__copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.side__nav .side__item {
  position: relative;
  z-index: 1;
  -webkit-user-drag: none;
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
}

.side__nav .side__item--active {
  touch-action: none;
  cursor: grab;
}

.side__nav .side__item:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
}

.side__nav .side__item:hover {
  background: none;
}

.side__item--active,
.side__item--active:hover {
  color: var(--ink);
  font-weight: 600;
}

@media (max-width: 850px) {
  .side {
    position: static;
    flex-direction: row;
    align-items: center;
    height: auto;
    padding: 10px 16px;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .side__top,
  .side__bottom {
    flex-direction: row;
    align-items: center;
  }

  .side__top {
    flex: 1;
    min-width: 0;
  }

  .side__copy {
    flex-direction: row;
    padding: 5px;
  }

  .side__nav {
    flex-direction: row;
    min-width: 0;
    margin-top: 0;
    padding: 5px;
    overflow-x: auto;
    scrollbar-width: none;
    border-radius: 999px;
    background: var(--pill-hover);
  }

  .side__nav .side__item {
    flex: none;
  }

  :deep(.brand__text) {
    display: none;
  }

  .side__user {
    width: auto;
    padding: 4px;
    border: 0;
    background: none;
  }

  .side__user :deep(.user__name) {
    display: none;
  }
}

@media (max-width: 650px) {
  .side {
    gap: 8px;
    padding: 6px 8px;
  }

  :deep(.brand__sign) {
    width: 32px;
    height: 32px;
  }

  .side__item {
    flex-direction: column;
    gap: 2px;
    padding: 6px 8px;
  }

  .side__label {
    font-size: 10px;
  }

  .side__logout .side__label {
    display: none;
  }

  .side__logout {
    justify-content: center;
  }

  .side__bottom {
    gap: 4px;
  }

  .side__user :deep(.user__avatar) {
    width: 32px;
    height: 32px;
  }
}
</style>
