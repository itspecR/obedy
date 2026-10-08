import { onBeforeUnmount, onMounted } from "vue";
import { onBeforeRouteLeave } from "vue-router";

type Guard = () => Promise<boolean>;

const guards = new Set<Guard>();

export async function mayLeaveAll(): Promise<boolean> {
  for (const guard of guards) {
    if (!(await guard())) {
      return false;
    }
  }
  return true;
}

export function useLeaveGuard(guard: Guard, dirty: () => boolean): void {
  function onUnload(event: BeforeUnloadEvent): void {
    if (dirty()) {
      event.preventDefault();
      event.returnValue = "";
    }
  }

  onMounted(() => {
    guards.add(guard);
    window.addEventListener("beforeunload", onUnload);
  });

  onBeforeUnmount(() => {
    guards.delete(guard);
    window.removeEventListener("beforeunload", onUnload);
  });

  onBeforeRouteLeave(guard);
}
