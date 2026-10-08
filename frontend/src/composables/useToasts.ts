import { reactive, readonly } from "vue";

export type ToastKind = "info" | "error";

export interface Toast {
  id: number;
  kind: ToastKind;
  text: string;
}

const INFO_LIFETIME_MS = 5500;

const state = reactive<{ items: Toast[] }>({ items: [] });
let nextId = 1;

function dismiss(id: number): void {
  const index = state.items.findIndex((toast) => toast.id === id);
  if (index !== -1) {
    state.items.splice(index, 1);
  }
}

function push(kind: ToastKind, text: string): number {
  const id = nextId++;
  state.items.push({ id, kind, text });
  if (kind === "info") {
    window.setTimeout(() => dismiss(id), INFO_LIFETIME_MS);
  }
  return id;
}

export function useToasts() {
  return {
    items: readonly(state).items,
    notify: (text: string) => push("info", text),
    fail: (text: string) => push("error", text),
    dismiss,
  };
}
