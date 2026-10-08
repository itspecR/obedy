import { onBeforeUnmount, ref, type Ref } from "vue";

const POPOVER_WIDTH_GUESS = 320;

export function usePopover(root: Ref<HTMLElement | null>) {
  const open = ref(false);
  const alignEnd = ref(false);

  function onOutside(event: Event): void {
    if (root.value && !root.value.contains(event.target as Node)) {
      close();
    }
  }

  function show(): void {
    const rect = root.value?.getBoundingClientRect();
    alignEnd.value = Boolean(rect && rect.left + POPOVER_WIDTH_GUESS > window.innerWidth);
    open.value = true;
    document.addEventListener("pointerdown", onOutside);
  }

  function close(): void {
    open.value = false;
    document.removeEventListener("pointerdown", onOutside);
  }

  function toggle(): void {
    if (open.value) {
      close();
    } else {
      show();
    }
  }

  function closeOnEscape(event: KeyboardEvent): void {
    if (event.key === "Escape" && open.value) {
      event.stopPropagation();
      close();
    }
  }

  onBeforeUnmount(close);

  return { open, alignEnd, show, close, toggle, closeOnEscape };
}
