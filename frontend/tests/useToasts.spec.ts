import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useToasts } from "../src/composables/useToasts";

describe("useToasts", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    const { items, dismiss } = useToasts();
    items.forEach((toast) => dismiss(toast.id));
    vi.useRealTimers();
  });

  it("hides an info toast after 5.5 seconds", () => {
    const { items, notify } = useToasts();
    notify("Отметки сохранены");

    vi.advanceTimersByTime(5499);
    expect(items).toHaveLength(1);
    vi.advanceTimersByTime(1);
    expect(items).toHaveLength(0);
  });

  it("keeps an error toast until it is dismissed", () => {
    const { items, fail, dismiss } = useToasts();
    const id = fail("Не удалось сохранить");

    vi.advanceTimersByTime(60_000);
    expect(items).toHaveLength(1);
    dismiss(id);
    expect(items).toHaveLength(0);
  });
});

describe("useToasts after a dismissal", () => {
  it("still shows new toasts through the same list", () => {
    const { items, notify, fail, dismiss } = useToasts();
    dismiss(fail("Первая ошибка"));
    notify("Новое уведомление");

    expect(items.map((toast) => toast.text)).toEqual(["Новое уведомление"]);
    items.forEach((toast) => dismiss(toast.id));
  });
});
