<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { FRAMES_PER_SECOND, SCENES, sceneLength } from "../../rabbit/scenes";
import RabbitSprite from "../rabbit/RabbitSprite.vue";
import { FILL_MS, PHASE_SCENE, nextPhase, type Outcome, type Phase } from "./rabbitPlot";

export interface Point {
  x: number;
  y: number;
}

const RABBIT_SIZE = 150;
const HOLE_DISTANCE = 150;
const HOLE_MARGIN = 70;
const SPEED = 1.8;
const APPEAR_MS = 220;
const RUN_MS = 420;
const MS_PER_SECOND = 1000;
const DIVE_MS = (sceneLength(SCENES.dive) / (FRAMES_PER_SECOND * SPEED)) * MS_PER_SECOND;
const TIMED: Partial<Record<Phase, number>> = { appear: APPEAR_MS, run: RUN_MS, fill: FILL_MS };

const props = defineProps<{ outcome: Outcome }>();
const emit = defineEmits<{ fill: [center: Point]; done: [] }>();

const root = ref<HTMLElement | null>(null);
const hole = ref<HTMLElement | null>(null);
const phase = ref<Phase>("appear");
const holeOffset = ref(HOLE_DISTANCE);
let timer = 0;

const scene = computed(() => PHASE_SCENE[phase.value]);
const travelled = computed(() => ["run", "dive", "fill"].includes(phase.value));
const dived = computed(() => ["dive", "fill"].includes(phase.value));
const holeOpen = computed(() => ["start", "run", "dive", "fill"].includes(phase.value));

const sizes = { "--size": `${RABBIT_SIZE}px`, "--appear": `${APPEAR_MS}ms` };
const holeStyle = computed(() => ({ left: `${holeOffset.value}px` }));
const body = computed(() => ({
  transform: `translate(${travelled.value ? holeOffset.value : 0}px, ${dived.value ? RABBIT_SIZE : 0}px)`,
  transition: dived.value ? `transform ${DIVE_MS}ms cubic-bezier(0.5, 0, 0.9, 0.6)` : `transform ${RUN_MS}ms linear`,
}));

function centerOf(element: HTMLElement): Point {
  const rect = element.getBoundingClientRect();
  return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
}

function advance(): void {
  const next = nextPhase(phase.value, props.outcome);
  if (next === null) {
    emit("done");
    return;
  }
  if (next === phase.value) {
    return;
  }
  phase.value = next;
  if (next === "fill" && hole.value) {
    emit("fill", centerOf(hole.value));
  }
  schedule();
}

function schedule(): void {
  const wait = TIMED[phase.value];
  if (wait !== undefined) {
    timer = window.setTimeout(advance, wait);
  }
}

onMounted(() => {
  const anchor = root.value?.getBoundingClientRect().left ?? 0;
  holeOffset.value = Math.max(0, Math.min(HOLE_DISTANCE, window.innerWidth - HOLE_MARGIN - anchor));
  schedule();
});
onBeforeUnmount(() => window.clearTimeout(timer));
</script>

<template>
  <div ref="root" class="login-rabbit" aria-hidden="true" :style="sizes">
    <span ref="hole" class="login-rabbit__hole" :class="{ 'login-rabbit__hole--open': holeOpen }" :style="holeStyle" />
    <div class="login-rabbit__box">
      <div class="login-rabbit__body" :class="{ 'login-rabbit__body--appear': phase === 'appear' }" :style="body">
        <RabbitSprite v-if="scene" :scene="scene" :speed="SPEED" :repeat="phase === 'tap' && outcome === 'pending'" @ended="advance" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-rabbit {
  position: absolute;
  pointer-events: none;
}

.login-rabbit__box {
  position: absolute;
  bottom: 0;
  left: calc(var(--size) / -2);
  width: var(--size);
  height: var(--size);
  clip-path: inset(-100vh -100vw 0 -100vw);
}

.login-rabbit__body {
  width: 100%;
  height: 100%;
}

.login-rabbit__body--appear {
  animation: rabbit-appear var(--appear) cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.login-rabbit__hole {
  position: absolute;
  top: 0;
  width: 120px;
  height: 30px;
  border-radius: 50%;
  background: radial-gradient(closest-side, #000 62%, #0a1222 78%, rgba(110, 168, 255, 0.85) 94%, rgba(110, 168, 255, 0) 100%);
  box-shadow: 0 0 22px rgba(110, 168, 255, 0.45);
  transform: translate(-50%, -50%) scale(0);
  transition: transform 260ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.login-rabbit__hole--open {
  transform: translate(-50%, -50%) scale(1);
}

@keyframes rabbit-appear {
  from {
    opacity: 0;
    transform: scale(0.5);
    filter: blur(8px) brightness(4);
  }
}
</style>
