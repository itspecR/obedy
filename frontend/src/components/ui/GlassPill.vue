<script setup lang="ts">
import { ref, watchEffect } from "vue";
import type { GlassPill } from "../../composables/useGlassPill";

const props = defineProps<{ pill: GlassPill; tone?: "active" | "hover" | "raised" }>();
const element = ref<HTMLElement | null>(null);

function variables(pill: GlassPill): Record<string, string> {
  const { box, scale, offset, angle, motion } = pill;
  const edges: Record<string, string> = box ? { "--top": `${box.top}px`, "--right": `${box.right}px`, "--bottom": `${box.bottom}px`, "--left": `${box.left}px` } : {};
  return { ...edges, "--sx": String(scale.x), "--sy": String(scale.y), "--tx": `${offset.x}px`, "--ty": `${offset.y}px`, "--dx": `${motion.dx}px`, "--dy": `${motion.dy}px`, "--msx": String(motion.sx), "--msy": String(motion.sy), "--angle": `${135 + angle}deg` };
}

watchEffect(() => {
  const target = element.value;
  const values = variables(props.pill);
  if (target) {
    Object.entries(values).forEach(([name, value]) => target.style.setProperty(name, value));
  }
});
</script>

<template>
  <span
    ref="element"
    class="glass"
    :class="[
      `glass--${tone ?? 'active'}`,
      {
        'glass--shown': pill.shown,
        'glass--moving': pill.moving,
        'glass--lifted': pill.lifted,
      },
    ]"
    aria-hidden="true"
  >
    <span class="glass__body">
      <span class="glass__warp" />
      <template v-if="pill.lifted && $slots.default">
        <span class="glass__layer"><span class="glass__view"><slot /></span></span>
      </template>
      <span class="glass__rim" />
      <span class="glass__rim glass__rim--overlay" />
    </span>
  </span>
</template>

<style scoped>
.glass {
  --liquid: cubic-bezier(0.3, 1.35, 0.55, 1);
  --lead: 300ms;
  --trail: 480ms;
  --capsule: 999px;
  position: absolute;
  top: var(--top, 0);
  right: var(--right, 0);
  bottom: var(--bottom, 0);
  left: var(--left, 0);
  z-index: 0;
  border-radius: var(--capsule);
  opacity: 0;
  pointer-events: none;
  transform: translate(var(--dx, 0px), var(--dy, 0px)) scale(var(--msx, 1), var(--msy, 1));
  transition: opacity 180ms ease;
  will-change: transform;
}

.glass__body {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border-radius: inherit;
  transform: translate(var(--tx, 0px), var(--ty, 0px)) scale(var(--sx, 1), var(--sy, 1));
  transition:
    transform var(--lead) var(--liquid),
    box-shadow var(--lead) ease;
}

.glass--active .glass__body,
.glass--raised .glass__body {
  box-shadow:
    0 6px 18px rgba(0, 0, 0, 0.1),
    0 1px 3px rgba(0, 0, 0, 0.08);
}

.glass__warp {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border-radius: inherit;
  backdrop-filter: blur(6px) saturate(140%);
}

.glass--active .glass__warp {
  background: rgba(118, 118, 128, 0.12);
}

.glass--raised .glass__warp {
  background: rgba(255, 255, 255, 0.82);
}

.glass--hover .glass__warp {
  background: rgba(118, 118, 128, 0.07);
}

.glass__warp::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle 60px at calc(var(--mx, -100px) - var(--left, 0px)) calc(var(--my, -100px) - var(--top, 0px)),
    rgba(255, 255, 255, 0.5),
    transparent 70%
  );
}

.glass__warp::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    105deg,
    transparent 30%,
    rgba(255, 255, 255, 0.6) 45%,
    rgba(236, 244, 255, 0.5) 52%,
    rgba(255, 246, 252, 0.45) 58%,
    transparent 72%
  );
  background-size: 260% 100%;
  background-position: 130% 0;
  opacity: 0;
}

.glass__rim {
  position: absolute;
  inset: 0;
  padding: 1.5px;
  border-radius: inherit;
  background: linear-gradient(var(--angle, 135deg), rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.35) 33%, rgba(255, 255, 255, 0.75) 66%, rgba(255, 255, 255, 0) 100%);
  box-shadow:
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.5),
    inset 0 1px 3px rgba(255, 255, 255, 0.25),
    0 1px 4px rgba(0, 0, 0, 0.12);
  mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0);
  mix-blend-mode: screen;
  opacity: 0.6;
}

.glass__rim--overlay {
  mix-blend-mode: overlay;
  opacity: 1;
}

.glass--hover .glass__rim {
  opacity: 0.35;
}

.glass--shown {
  opacity: 1;
}



.glass--lifted {
  z-index: 2;
}

.glass--lifted .glass__body {
  box-shadow:
    0 12px 32px rgba(0, 0, 0, 0.16),
    0 2px 6px rgba(0, 0, 0, 0.1);
}

.glass--lifted .glass__warp {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(0.5px) saturate(150%) brightness(1.04);
}

.glass--lifted .glass__warp {
  background: rgba(255, 255, 255, 0.985);
}

.glass__view {
  --magnify: 1.12;
  position: absolute;
  top: calc(-1 * var(--top, 0px));
  left: calc(-1 * var(--left, 0px));
  width: var(--nav-w, 0px);
  height: var(--nav-h, 0px);
  transform-origin: calc((var(--nav-w, 0px) + var(--left, 0px) - var(--right, 0px)) / 2) calc((var(--nav-h, 0px) + var(--top, 0px) - var(--bottom, 0px)) / 2);
  will-change: transform;
  transform: scale(calc(var(--magnify) / (var(--sx, 1) * var(--msx, 1))), calc(var(--magnify) / (var(--sy, 1) * var(--msy, 1)))) translate(calc(-1 * var(--dx, 0px)), calc(-1 * var(--dy, 0px)));
  text-shadow:
    0.7px 0 rgba(255, 40, 90, 0.35),
    -0.7px 0 rgba(0, 150, 255, 0.35);
}

.glass__view :deep(svg) {
  filter: drop-shadow(0.7px 0 rgba(255, 40, 90, 0.35)) drop-shadow(-0.7px 0 rgba(0, 150, 255, 0.35));
}

.glass__layer {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border-radius: inherit;
  background: rgba(255, 255, 255, 0.985);
}




.glass--lifted .glass__warp::before {
  opacity: 0.4;
}



.glass--moving .glass__warp::after {
  animation: glass-sheen 700ms ease-out;
}

@keyframes glass-sheen {
  0% {
    background-position: 130% 0;
    opacity: 0;
  }
  25% {
    opacity: 1;
  }
  100% {
    background-position: -30% 0;
    opacity: 0;
  }
}

@media (prefers-reduced-transparency: reduce) {
  .glass--active .glass__warp {
    background: #e7e7ec;
  }

  .glass--raised .glass__warp {
  background: rgba(255, 255, 255, 0.82);
}

.glass--hover .glass__warp {
    background: #f0f0f3;
  }

  .glass__rim,
  .glass__warp::before,
  .glass__warp::after {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .glass__body {
    transition: none;
  }

  .glass--moving .glass__warp::after {
    animation: none;
  }
}
</style>
