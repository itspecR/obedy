<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { frameUrl } from "../../rabbit/frames";
import { FRAMES_PER_SECOND, SCENES, frameAt, sceneEnded, type SceneName } from "../../rabbit/scenes";

const MS_PER_SECOND = 1000;
const LONGEST_STEP_MS = 100;
const BLEND_TICKS = 2;

const props = withDefaults(defineProps<{ scene: SceneName; speed?: number; repeat?: boolean; still?: boolean }>(), { speed: 1, repeat: false, still: false });
const emit = defineEmits<{ ended: [scene: SceneName] }>();

const tick = ref(0);
const src = computed(() => frameUrl(props.scene, frameAt(SCENES[props.scene], tick.value)));
const previous = ref("");
const blending = computed(() => Boolean(SCENES[props.scene].blend) && !props.still && previous.value !== "");
const blendMs = computed(() => `${(BLEND_TICKS * MS_PER_SECOND) / (FRAMES_PER_SECOND * props.speed)}ms`);
let frame = 0;
let last = 0;
let carried = 0;

function step(now: number): void {
  carried += Math.min(now - (last || now), LONGEST_STEP_MS);
  last = now;
  const tickMs = MS_PER_SECOND / (FRAMES_PER_SECOND * props.speed);
  while (carried >= tickMs) {
    carried -= tickMs;
    tick.value += 1;
    if (sceneEnded(SCENES[props.scene], tick.value)) {
      emit("ended", props.scene);
      if (!props.repeat) {
        tick.value -= 1;
        return;
      }
      tick.value = 0;
    }
  }
  frame = requestAnimationFrame(step);
}

function play(): void {
  cancelAnimationFrame(frame);
  tick.value = 0;
  last = 0;
  carried = 0;
  if (!props.still) {
    frame = requestAnimationFrame(step);
  }
}

watch(src, (_, old) => (previous.value = old));
watch(() => [props.scene, props.still], play);
onMounted(play);
onBeforeUnmount(() => cancelAnimationFrame(frame));
</script>

<template>
  <span class="rabbit-sprite" :style="{ '--blend': blendMs }">
    <img v-if="blending" class="rabbit-sprite__frame" :src="previous" alt="" draggable="false" />
    <img :key="src" class="rabbit-sprite__frame" :class="{ 'rabbit-sprite__frame--blend': blending }" :src="src" alt="" draggable="false" />
  </span>
</template>

<style scoped>
.rabbit-sprite {
  position: relative;
  display: block;
  width: 100%;
  height: 100%;
}

.rabbit-sprite__frame {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  user-select: none;
}

.rabbit-sprite__frame--blend {
  animation: rabbit-sprite-blend var(--blend) linear both;
}

@keyframes rabbit-sprite-blend {
  from {
    opacity: 0;
  }
}
</style>
