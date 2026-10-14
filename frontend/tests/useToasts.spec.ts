import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useToasts } from "../src/composables/useToasts";

describe("useToasts", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    const { items, dismiss } = useToasts();
    items.forEach((toast) => dismiss(toast.id));
    vi.useRealTimers();
  });

  it("hides an info toast after 5 seconds", () => {
    const { items, notify } = useToasts();
    notify("Отметки сохранены");

    vi.advanceTimersByTime(4999);
    expect(items).toHaveLength(1);
    vi.advanceTimersByTime(1);
    expect(items).toHaveLength(0);
  });

  it("hides an error toast after 5 seconds or right away on close", () => {
    const { items, fail, dismiss } = useToasts();
    fail("Не удалось сохранить");
    const closed = fail("Ещё одна ошибка");

    dismiss(closed);
    expect(items).toHaveLength(1);
    vi.advanceTimersByTime(5000);
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
