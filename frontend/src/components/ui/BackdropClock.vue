<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { fetchClock, type LunchWindow } from "../../api/clock";
import { DEGREES_PER_HOUR, DEGREES_PER_MINUTE, arcOf, clockTimeOf, hourAngle, minuteAngle, turnTowards, wallTime } from "../../clock/dial";
import { useServerClock } from "../../composables/useServerClock";

const CENTER = 600;
const RIM = 560;
const ARC_RADIUS = 500;
const NUMERAL_RADIUS = 450;
const TICK_INSET = 8;
const MAJOR_TICK = 46;
const MINOR_TICK = 20;
const HOUR_HAND = 250;
const MINUTE_HAND = 380;
const HAND_TAIL = 45;
const PIN_RADIUS = 12;
const HALF_TURN = 180;
const MINUTES_PER_HOUR = 60;
const TICKS_PER_HOUR = 5;
const TICKS = Array.from({ length: MINUTES_PER_HOUR }, (_, index) => ({ index, major: index % TICKS_PER_HOUR === 0 }));
const NUMERALS = [12, 3, 6, 9];

const { now, sync } = useServerClock();
const zone = ref<string | undefined>();
const lunchWindow = ref<LunchWindow | null>(null);
const hourTurn = ref(0);
const minuteTurn = ref(0);

const time = computed(() => wallTime(now.value, zone.value));
const arcPath = computed(() => (lunchWindow.value ? arcPathOf(lunchWindow.value) : ""));

function point(angle: number, radius: number): { x: number; y: number } {
  const radians = (angle * Math.PI) / HALF_TURN;
  return { x: CENTER + radius * Math.sin(radians), y: CENTER - radius * Math.cos(radians) };
}

function tickLine(index: number, major: boolean) {
  const inner = point(index * DEGREES_PER_MINUTE, RIM - (major ? MAJOR_TICK : MINOR_TICK));
  const outer = point(index * DEGREES_PER_MINUTE, RIM - TICK_INSET);
  return { x1: inner.x, y1: inner.y, x2: outer.x, y2: outer.y };
}

function numeralPoint(hour: number) {
  return point(hour * DEGREES_PER_HOUR, NUMERAL_RADIUS);
}

function arcPathOf(window: LunchWindow): string {
  const arc = arcOf(clockTimeOf(window.start), clockTimeOf(window.end));
  const from = point(arc.start, ARC_RADIUS);
  const to = point(arc.end, ARC_RADIUS);
  const large = arc.end - arc.start > HALF_TURN ? 1 : 0;
  return `M${from.x} ${from.y}A${ARC_RADIUS} ${ARC_RADIUS} 0 ${large} 1 ${to.x} ${to.y}`;
}

async function syncWithServer(): Promise<void> {
  try {
    const clock = await fetchClock();
    sync(clock.server_time);
    zone.value = clock.time_zone;
    lunchWindow.value = clock.lunch_window;
  } catch {
    lunchWindow.value = null;
  }
}

function syncWhenVisible(): void {
  if (document.visibilityState === "visible") {
    void syncWithServer();
  }
}

watch(
  time,
  (current) => {
    hourTurn.value = turnTowards(hourTurn.value, hourAngle(current));
    minuteTurn.value = turnTowards(minuteTurn.value, minuteAngle(current));
  },
  { immediate: true },
);

onMounted(() => {
  void syncWithServer();
  document.addEventListener("visibilitychange", syncWhenVisible);
});
onUnmounted(() => document.removeEventListener("visibilitychange", syncWhenVisible));
</script>

<template>
  <div class="backdrop-clock" aria-hidden="true">
    <svg class="backdrop-clock__dial" viewBox="0 0 1200 1200" fill="none">
      <circle :cx="CENTER" :cy="CENTER" :r="RIM" class="backdrop-clock__rim" />
      <line v-for="tick in TICKS" :key="tick.index" v-bind="tickLine(tick.index, tick.major)" :class="tick.major ? 'backdrop-clock__tick--major' : 'backdrop-clock__tick'" />
      <text v-for="hour in NUMERALS" :key="hour" v-bind="numeralPoint(hour)" class="backdrop-clock__numeral">{{ hour }}</text>
      <path v-if="arcPath" :d="arcPath" class="backdrop-clock__window" />
      <g class="backdrop-clock__hand" :style="{ transform: `rotate(${hourTurn}deg)` }">
        <line :x1="CENTER" :y1="CENTER + HAND_TAIL" :x2="CENTER" :y2="CENTER - HOUR_HAND" class="backdrop-clock__hour" />
      </g>
      <g class="backdrop-clock__hand" :style="{ transform: `rotate(${minuteTurn}deg)` }">
        <line :x1="CENTER" :y1="CENTER + HAND_TAIL" :x2="CENTER" :y2="CENTER - MINUTE_HAND" class="backdrop-clock__minute" />
      </g>
      <circle :cx="CENTER" :cy="CENTER" :r="PIN_RADIUS" class="backdrop-clock__pin" />
    </svg>
  </div>
</template>

<style scoped>
.backdrop-clock {
  position: fixed;
  inset: 0;
  z-index: -1;
  display: grid;
  place-items: center;
  pointer-events: none;
}

.backdrop-clock__dial {
  width: min(88vmin, 820px);
  height: auto;
  stroke-linecap: round;
}

.backdrop-clock__rim {
  stroke: rgba(255, 255, 255, 0.07);
  stroke-width: 2;
}

.backdrop-clock__tick {
  stroke: rgba(255, 255, 255, 0.07);
  stroke-width: 2;
}

.backdrop-clock__tick--major {
  stroke: rgba(255, 255, 255, 0.14);
  stroke-width: 4;
}

.backdrop-clock__numeral {
  fill: rgba(255, 255, 255, 0.12);
  font-family: var(--font-display);
  font-size: 64px;
  font-weight: 600;
  text-anchor: middle;
  dominant-baseline: central;
}

.backdrop-clock__window {
  stroke: var(--green);
  stroke-opacity: 0.4;
  stroke-width: 14;
}

.backdrop-clock__hand {
  transform-box: view-box;
  transform-origin: 50% 50%;
  transition: transform 250ms var(--ease-in-out);
}

.backdrop-clock__hour {
  stroke: rgba(255, 255, 255, 0.13);
  stroke-width: 12;
}

.backdrop-clock__minute {
  stroke: rgba(255, 255, 255, 0.11);
  stroke-width: 8;
}

.backdrop-clock__pin {
  fill: rgba(255, 255, 255, 0.14);
}
</style>
