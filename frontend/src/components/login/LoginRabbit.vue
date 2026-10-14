<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { frameUrl } from "../../rabbit/frames";
import { MORPH_MS, boxOf, type Box } from "../../rabbit/morph";
import { FEET_LINE, SCENES } from "../../rabbit/scenes";
import ButtonMorph, { type MorphDirection } from "../rabbit/ButtonMorph.vue";
import RabbitHole from "../rabbit/RabbitHole.vue";
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
const RUN_MS = 420;
const DIVE_MS = 420;
const TIMED: Partial<Record<Phase, number>> = { run: RUN_MS, dive: DIVE_MS, fill: FILL_MS };
const MORPHS: Partial<Record<Phase, MorphDirection>> = { appear: "in", melt: "out" };
const LAST_NO_FRAME = SCENES.no.steps[SCENES.no.steps.length - 1][0];

const props = defineProps<{ outcome: Outcome; button: () => Box }>();
const emit = defineEmits<{ fill: [center: Point]; done: [] }>();

const root = ref<HTMLElement | null>(null);
const hole = ref<InstanceType<typeof RabbitHole> | null>(null);
const sprite = ref<HTMLElement | null>(null);
const target = ref<Box | null>(null);
const buttonBox = ref<Box | null>(null);
const shown = ref(false);
const phase = ref<Phase>("appear");
const holeOffset = ref(HOLE_DISTANCE);
let timer = 0;

const scene = computed(() => PHASE_SCENE[phase.value]);
const travelled = computed(() => ["run", "dive", "fill"].includes(phase.value));
const dived = computed(() => ["dive", "fill"].includes(phase.value));
const holeOpen = computed(() => ["start", "run", "dive", "fill"].includes(phase.value));

const morph = computed(() => MORPHS[phase.value] ?? null);
const morphFrame = computed(() => (morph.value === "in" ? frameUrl("tap", 1) : frameUrl("no", LAST_NO_FRAME)));
const sizes = { "--size": `${RABBIT_SIZE}px`, "--sink": `${(1 - FEET_LINE) * RABBIT_SIZE}px` };
const holeStyle = computed(() => ({ left: `${holeOffset.value}px` }));
const body = computed(() => ({
  transform: `translate(${travelled.value ? holeOffset.value : 0}px, ${dived.value ? RABBIT_SIZE : 0}px)`,
  transition: dived.value ? `transform ${DIVE_MS}ms cubic-bezier(0.5, 0, 0.9, 0.6)` : `transform ${RUN_MS}ms linear`,
}));

function measure(): void {
  target.value = sprite.value ? boxOf(sprite.value) : null;
  buttonBox.value = props.button();
}

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
  if (MORPHS[next]) {
    measure();
  }
  if (next === "fill" && hole.value) {
    emit("fill", centerOf(hole.value.$el as HTMLElement));
  }
  schedule();
}

function swapped(): void {
  shown.value = morph.value === "in";
}

function sceneEnded(): void {
  if (TIMED[phase.value] === undefined) {
    advance();
  }
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
  measure();
  schedule();
});
onBeforeUnmount(() => window.clearTimeout(timer));
</script>

<template>
  <div ref="root" class="login-rabbit" aria-hidden="true" :style="sizes">
    <RabbitHole ref="hole" class="login-rabbit__hole" :open="holeOpen" :style="holeStyle" />
    <div class="login-rabbit__box">
      <div ref="sprite" class="login-rabbit__body" :class="{ 'login-rabbit__body--hidden': !shown }" :style="body">
        <RabbitSprite v-if="scene" :scene="scene" :speed="SPEED" :still="phase === 'appear'" :repeat="phase === 'tap' && outcome === 'pending'" @ended="sceneEnded" />
      </div>
    </div>
    <ButtonMorph
      v-if="morph && target && buttonBox"
      :key="morph"
      :from="buttonBox"
      :to="target"
      :frame="morphFrame"
      :direction="morph"
      :duration="MORPH_MS"
      @swap="swapped"
      @done="advance"
    />
  </div>
</template>

<style scoped>
.login-rabbit {
  position: absolute;
  pointer-events: none;
}

.login-rabbit__box {
  position: absolute;
  bottom: calc(var(--sink) * -1);
  left: calc(var(--size) / -2);
  width: var(--size);
  height: var(--size);
  clip-path: inset(-100vh -100vw var(--sink) -100vw);
}

.login-rabbit__body {
  width: 100%;
  height: 100%;
}

.login-rabbit__body--hidden {
  visibility: hidden;
}

.login-rabbit__hole {
  top: 0;
}

</style>
