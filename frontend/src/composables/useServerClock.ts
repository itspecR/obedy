import { onMounted, onUnmounted, ref } from "vue";

const TICK_MS = 1000;

export function useServerClock() {
  const offset = ref(0);
  const now = ref(Date.now());
  let timer: number | undefined;

  function tick(): void {
    now.value = Date.now() + offset.value;
  }

  function sync(serverTime: string): void {
    offset.value = Date.parse(serverTime) - Date.now();
    tick();
  }

  onMounted(() => {
    timer = window.setInterval(tick, TICK_MS);
  });
  onUnmounted(() => window.clearInterval(timer));

  return { now, sync };
}
