<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { SWAP_IN, SWAP_OUT, bodyOf, type Box } from "../../rabbit/morph";

export type MorphDirection = "in" | "out";

const BUTTON_RADIUS = "12px";
const BODY_RADIUS = "45%";
const EASING = "cubic-bezier(0.5, 0, 0.2, 1)";

const props = withDefaults(defineProps<{ from: Box; to: Box; frame: string; direction: MorphDirection; duration: number; lands?: boolean }>(), { lands: true });
const emit = defineEmits<{ swap: []; done: [] }>();

const blob = ref<HTMLElement | null>(null);
const ghost = ref<HTMLElement | null>(null);
const timers: number[] = [];

function frameOf(box: Box, radius: string, opacity: number, offset: number): Keyframe {
  return { left: `${box.left}px`, top: `${box.top}px`, width: `${box.width}px`, height: `${box.height}px`, borderRadius: radius, opacity, offset };
}

function blobFrames(): Keyframe[] {
  const button = props.from;
  const body = bodyOf(props.to);
  const forward = [
    frameOf(button, BUTTON_RADIUS, 1, 0),
    frameOf(body, BODY_RADIUS, 1, 0.45),
    frameOf(body, BODY_RADIUS, 0, 0.7),
    frameOf(body, BODY_RADIUS, 0, 1),
  ];
  if (props.direction === "in") {
    return forward;
  }
  const backward = forward.reverse().map((frame) => ({ ...frame, offset: 1 - Number(frame.offset) }));
  return props.lands ? backward : [...backward.slice(0, -1), { ...backward[backward.length - 1], opacity: 0 }];
}

function ghostFrames(): Keyframe[] {
  const forward = [
    { opacity: 0, offset: 0 },
    { opacity: 0, offset: 0.35 },
    { opacity: 1, offset: SWAP_IN },
    { opacity: 0, offset: 1 },
  ];
  return props.direction === "in" ? forward : forward.reverse().map((frame) => ({ ...frame, offset: 1 - frame.offset }));
}

function play(element: HTMLElement | null, frames: Keyframe[]): void {
  if (element && typeof element.animate === "function") {
    element.animate(frames, { duration: props.duration, easing: EASING, fill: "both" });
  }
}

onMounted(() => {
  play(blob.value, blobFrames());
  play(ghost.value, ghostFrames());
  const swapAt = props.duration * (props.direction === "in" ? SWAP_IN : SWAP_OUT);
  timers.push(window.setTimeout(() => emit("swap"), swapAt));
  timers.push(window.setTimeout(() => emit("done"), props.duration));
});
onBeforeUnmount(() => timers.forEach((timer) => window.clearTimeout(timer)));
</script>

<template>
  <Teleport to="body">
    <div class="button-morph" aria-hidden="true">
      <span ref="blob" class="button-morph__blob" />
      <img
        ref="ghost"
        class="button-morph__ghost"
        :src="frame"
        alt=""
        :style="{ left: `${to.left}px`, top: `${to.top}px`, width: `${to.width}px`, height: `${to.height}px` }"
      />
    </div>
  </Teleport>
</template>

<style scoped>
.button-morph {
  position: fixed;
  inset: 0;
  z-index: 1000;
  pointer-events: none;
}

.button-morph__blob,
.button-morph__ghost {
  position: fixed;
  opacity: 0;
}

.button-morph__blob {
  background: linear-gradient(180deg, #ffffff 0%, #e6e7eb 100%);
  box-shadow: 0 0 24px rgba(255, 255, 255, 0.35);
}

.button-morph__ghost {
  object-fit: contain;
  filter: brightness(0) invert(1);
}
</style>
