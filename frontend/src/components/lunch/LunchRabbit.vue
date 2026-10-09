<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { SceneName } from "../../rabbit/scenes";
import RabbitHole from "../rabbit/RabbitHole.vue";
import RabbitSprite from "../rabbit/RabbitSprite.vue";

type Phase = "appear" | "start" | "run" | "ontime" | "vanish";

const RABBIT_SIZE = 96;
const HOLE_WIDTH = 84;
const APPEAR_MS = 220;
const VANISH_MS = 320;
const JOG_SPEED = 0.6;
const PHASE_SCENE: Record<Phase, SceneName> = { appear: "start", start: "start", run: "run", ontime: "ontime", vanish: "ontime" };

const props = defineProps<{ progress: number; fresh: boolean; still: boolean; parting: boolean }>();
const emit = defineEmits<{ parted: [] }>();

const phase = ref<Phase>(props.fresh && !props.still ? "appear" : "run");
let timer = 0;

const scene = computed(() => PHASE_SCENE[phase.value]);
const speed = computed(() => (phase.value === "run" ? JOG_SPEED : 1));
const holeOpen = computed(() => !["ontime", "vanish"].includes(phase.value));
const sizes = {
  "--size": `${RABBIT_SIZE}px`,
  "--hole-width": `${HOLE_WIDTH}px`,
  "--appear": `${APPEAR_MS}ms`,
  "--vanish": `${VANISH_MS}ms`,
};
const runner = computed(() => ({ left: `calc((100% - var(--size) - var(--hole-width) / 2) * ${props.progress})` }));

function later(ms: number, action: () => void): void {
  window.clearTimeout(timer);
  timer = window.setTimeout(action, ms);
}

function ended(): void {
  if (phase.value === "start") {
    phase.value = "run";
  } else if (phase.value === "ontime") {
    phase.value = "vanish";
    later(VANISH_MS, () => emit("parted"));
  }
}

function part(): void {
  if (props.still) {
    emit("parted");
    return;
  }
  phase.value = "ontime";
}

watch(
  () => props.parting,
  (parting) => parting && part(),
);

onMounted(() => {
  if (phase.value === "appear") {
    later(APPEAR_MS, () => (phase.value = "start"));
  }
  if (props.parting) {
    part();
  }
});
onBeforeUnmount(() => window.clearTimeout(timer));
</script>

<template>
  <div class="lunch-rabbit" :class="{ 'lunch-rabbit--still': still }" aria-hidden="true" :style="sizes">
    <span class="lunch-rabbit__path" />
    <span class="lunch-rabbit__trail" :style="{ width: `calc((100% - var(--hole-width) / 2) * ${progress})` }" />
    <RabbitHole class="lunch-rabbit__hole" :open="holeOpen" />
    <div class="lunch-rabbit__runner" :style="runner">
      <div class="lunch-rabbit__body" :class="`lunch-rabbit__body--${phase}`">
        <RabbitSprite :scene="scene" :speed="speed" :still="still" @ended="ended" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.lunch-rabbit {
  position: relative;
  width: min(100%, 420px);
  height: calc(var(--size) + 12px);
}

.lunch-rabbit__path,
.lunch-rabbit__trail {
  position: absolute;
  bottom: 6px;
  left: 0;
  height: 2px;
  border-radius: 1px;
}

.lunch-rabbit__path {
  right: calc(var(--hole-width) / 2);
  background: repeating-linear-gradient(90deg, var(--line-strong) 0 4px, transparent 4px 10px);
}

.lunch-rabbit__trail {
  background: var(--line-strong);
  transition: width 1s linear;
}

.lunch-rabbit__hole {
  right: calc(var(--hole-width) / -2);
  bottom: calc(6px - var(--hole-width) / 8);
}

.lunch-rabbit__runner {
  position: absolute;
  bottom: 6px;
  width: var(--size);
  height: var(--size);
  transition: left 1s linear;
}

.lunch-rabbit__body {
  width: 100%;
  height: 100%;
}

.lunch-rabbit__body--appear {
  animation: lunch-rabbit-appear var(--appear) cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.lunch-rabbit__body--vanish {
  opacity: 0;
  filter: blur(8px) brightness(3);
  transform: scale(0.6);
  transition:
    opacity var(--vanish) ease,
    filter var(--vanish) ease,
    transform var(--vanish) ease;
}

.lunch-rabbit--still .lunch-rabbit__runner,
.lunch-rabbit--still .lunch-rabbit__trail {
  transition: none;
}

@keyframes lunch-rabbit-appear {
  from {
    opacity: 0;
    transform: scale(0.5);
    filter: blur(8px) brightness(4);
  }
}
</style>
