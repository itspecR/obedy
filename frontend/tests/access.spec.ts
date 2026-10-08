import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AccessState } from "../src/api/access";
import AccessPage from "../src/pages/AccessPage.vue";
import { useConfirm } from "../src/composables/useConfirm";
import { useToasts } from "../src/composables/useToasts";

function access(overrides: Partial<AccessState> = {}): AccessState {
  return {
    allow_private: true,
    private_ranges: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
    your_address: "192.168.5.20",
    networks: [],
    ...overrides,
  };
}

function reply(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function serve(...responses: Response[]) {
  const spy = vi.fn();
  responses.forEach((response) => spy.mockResolvedValueOnce(response));
  vi.stubGlobal("fetch", spy);
  return spy;
}

function call(spy: ReturnType<typeof vi.fn>, index: number): { url: string; method: string; body: unknown } {
  const [url, init] = spy.mock.calls[index] as [string, RequestInit];
  return { url, method: init.method ?? "GET", body: init.body ? JSON.parse(init.body as string) : undefined };
}

async function mounted(...responses: Response[]) {
  const spy = serve(...responses);
  const wrapper = mount(AccessPage);
  await flushPromises();
  return { spy, wrapper };
}

describe("AccessPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  it("shows the policy, own address and an explained empty list", async () => {
    const { wrapper } = await mounted(reply(200, access()));

    expect(wrapper.get('[role="switch"]').attributes("aria-checked")).toBe("true");
    expect(wrapper.text()).toContain("192.168.5.20");
    expect(wrapper.text()).toContain("10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16");
    expect(wrapper.text()).toContain("Список пуст");
  });

  it("adds an address and clears the form", async () => {
    const added = access({ networks: [{ id: 1, network: "10.1.1.7/32", note: "RDP-1" }] });
    const { spy, wrapper } = await mounted(reply(200, access()), reply(201, added));
    const inputs = wrapper.findAll("input");
    await inputs[0].setValue("10.1.1.7");
    await inputs[1].setValue("RDP-1");

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(call(spy, 1)).toEqual({ url: "/api/access/networks", method: "POST", body: { network: "10.1.1.7", note: "RDP-1" } });
    expect(wrapper.text()).toContain("10.1.1.7/32");
    expect((inputs[0].element as HTMLInputElement).value).toBe("");
  });

  it("asks for an address before calling the server", async () => {
    const { spy, wrapper } = await mounted(reply(200, access()));

    await wrapper.get("form").trigger("submit");

    expect(wrapper.text()).toContain("Укажите адрес");
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("asks before closing the local network and shows the server refusal", async () => {
    const refusal = { detail: "Нельзя: ваш адрес 192.168.5.20 потеряет доступ. Сначала добавьте его в список" };
    const { spy, wrapper } = await mounted(reply(200, access()), reply(400, refusal));

    await wrapper.get('[role="switch"]').trigger("click");
    expect(useConfirm().current.request?.title).toBe("Закрыть всю локальную сеть?");
    useConfirm().answer(true);
    await flushPromises();

    expect(call(spy, 1)).toEqual({ url: "/api/access/private", method: "PUT", body: { enabled: false } });
    expect(useToasts().items.map((toast) => toast.text)).toContain(refusal.detail);
    expect(wrapper.get('[role="switch"]').attributes("aria-checked")).toBe("true");
  });

  it("keeps everything as is when closing is cancelled", async () => {
    const { spy, wrapper } = await mounted(reply(200, access()));

    await wrapper.get('[role="switch"]').trigger("click");
    useConfirm().answer(false);
    await flushPromises();

    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("removes an address after confirmation", async () => {
    const listed = access({ networks: [{ id: 7, network: "10.1.1.7/32", note: "" }] });
    const { spy, wrapper } = await mounted(reply(200, listed), reply(200, access()));

    await wrapper.get('[aria-label="Убрать 10.1.1.7/32"]').trigger("click");
    useConfirm().answer(true);
    await flushPromises();

    expect(call(spy, 1)).toEqual({ url: "/api/access/networks/7", method: "DELETE", body: undefined });
    expect(wrapper.text()).toContain("Список пуст");
  });

  it("offers a retry when loading fails", async () => {
    const { wrapper } = await mounted(reply(403, { detail: "Раздел доступен только администратору" }));

    expect(wrapper.get('[role="alert"]').text()).toContain("Раздел доступен только администратору");
    expect(wrapper.findAll("button").some((button) => button.text() === "Повторить")).toBe(true);
  });
});
