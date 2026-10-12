<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { FEET_LINE, type SceneName } from "../../rabbit/scenes";
import RabbitHole from "../rabbit/RabbitHole.vue";
import RabbitSprite from "../rabbit/RabbitSprite.vue";

type Phase = "appear" | "start" | "run" | "fall" | "rise" | "late" | "ontime" | "vanish";

const RABBIT_SIZE = 96;
const LATE_SIZE = 116;
const HOLE_WIDTH = 84;
const APPEAR_MS = 220;
const VANISH_MS = 320;
const FALL_MS = 420;
const RISE_MS = 600;
const JOG_SPEED = 0.6;
const PHASE_SCENE: Record<Phase, SceneName> = {
  appear: "start",
  start: "start",
  run: "run",
  fall: "dive",
  rise: "late",
  late: "late",
  ontime: "ontime",
  vanish: "ontime",
};
const RUNNING: Phase[] = ["appear", "start", "run"];
const IN_HOLE: Phase[] = ["rise", "late"];

const props = defineProps<{ progress: number; fresh: boolean; still: boolean; parting: boolean; late?: boolean }>();
const emit = defineEmits<{ parted: [] }>();

const phase = ref<Phase>(firstPhase());
let timer = 0;

const scene = computed(() => PHASE_SCENE[phase.value]);
const speed = computed(() => (phase.value === "run" ? JOG_SPEED : 1));
const holeOpen = computed(() => !["ontime", "vanish"].includes(phase.value));
const peeking = computed(() => IN_HOLE.includes(phase.value));
const sizes = {
  "--size": `${RABBIT_SIZE}px`,
  "--late-size": `${LATE_SIZE}px`,
  "--hole-width": `${HOLE_WIDTH}px`,
  "--appear": `${APPEAR_MS}ms`,
  "--vanish": `${VANISH_MS}ms`,
  "--fall": `${FALL_MS}ms`,
  "--rise": `${RISE_MS}ms`,
  "--sink": `${(1 - FEET_LINE) * RABBIT_SIZE}px`,
};
const runner = computed(() => ({ left: `calc((100% - var(--size) - var(--hole-width) / 2) * ${props.progress})` }));

function firstPhase(): Phase {
  if (props.late) {
    return "late";
  }
  return props.fresh && !props.still ? "appear" : "run";
}

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

function fall(): void {
  if (!RUNNING.includes(phase.value)) {
    return;
  }
  if (props.still) {
    phase.value = "late";
    return;
  }
  phase.value = "fall";
  later(FALL_MS, () => {
    phase.value = "rise";
    later(RISE_MS, () => (phase.value = "late"));
  });
}

watch(
  () => props.parting,
  (parting) => parting && part(),
);
watch(
  () => props.late,
  (late) => late && fall(),
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
    <div v-if="peeking" class="lunch-rabbit__peek">
      <div class="lunch-rabbit__peek-body" :class="{ 'lunch-rabbit__peek-body--rise': phase === 'rise' }">
        <RabbitSprite :scene="scene" :still="still" />
      </div>
    </div>
    <div v-else class="lunch-rabbit__runner" :style="runner">
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
  height: calc(max(var(--size), var(--late-size)) + 12px);
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
  bottom: calc(6px - var(--sink));
  width: var(--size);
  height: var(--size);
  clip-path: inset(-100vh -100vw var(--sink) -100vw);
  transition: left 1s linear;
}

.lunch-rabbit__body {
  width: 100%;
  height: 100%;
}

.lunch-rabbit__body--appear {
  animation: lunch-rabbit-appear var(--appear) cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.lunch-rabbit__body--fall {
  transform: translate(calc(var(--size) / 2), var(--size));
  transition: transform var(--fall) cubic-bezier(0.5, 0, 0.9, 0.6);
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

.lunch-rabbit__peek {
  position: absolute;
  right: calc(var(--hole-width) / 2 - var(--late-size) / 2);
  bottom: 6px;
  width: var(--late-size);
  height: var(--late-size);
  clip-path: inset(-100vh -100vw 0 -100vw);
}

.lunch-rabbit__peek-body {
  width: 100%;
  height: 100%;
}

.lunch-rabbit__peek-body--rise {
  animation: lunch-rabbit-rise var(--rise) cubic-bezier(0.2, 0.8, 0.2, 1) both;
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

@keyframes lunch-rabbit-rise {
  from {
    transform: translateY(100%);
  }
}
</style>
