import { describe, expect, it } from "vitest";
import { useConfirm } from "../src/composables/useConfirm";

const request = { title: "Удалить?", text: "Последствия.", action: "Удалить" };

describe("useConfirm", () => {
  it("resolves with the given answer and clears the request", async () => {
    const { ask, answer, current } = useConfirm();
    const pending = ask(request);

    expect(current.request?.title).toBe("Удалить?");
    answer(true);

    await expect(pending).resolves.toBe(true);
    expect(current.request).toBeNull();
  });

  it("cancels the previous question when a new one is asked", async () => {
    const { ask, answer } = useConfirm();
    const first = ask(request);
    const second = ask({ ...request, title: "Другое?" });

    await expect(first).resolves.toBe(false);
    answer(true);
    await expect(second).resolves.toBe(true);
  });
});
