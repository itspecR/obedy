import { reactive, readonly } from "vue";

export interface ConfirmRequest {
  title: string;
  text: string;
  action: string;
  danger?: boolean;
}

interface ConfirmState {
  request: ConfirmRequest | null;
  resolve: ((accepted: boolean) => void) | null;
}

const state = reactive<ConfirmState>({ request: null, resolve: null });

function ask(request: ConfirmRequest): Promise<boolean> {
  state.resolve?.(false);
  return new Promise((resolve) => {
    state.request = request;
    state.resolve = resolve;
  });
}

function answer(accepted: boolean): void {
  const resolve = state.resolve;
  state.request = null;
  state.resolve = null;
  resolve?.(accepted);
}

export function useConfirm() {
  return { current: readonly(state), ask, answer };
}
