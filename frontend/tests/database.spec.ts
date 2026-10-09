import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import DatabasePage from "../src/pages/DatabasePage.vue";
import { bodySentTo, routeFetch, wasRequested } from "./helpers";

const confirm = vi.hoisted(() => ({ answer: true }));
vi.mock("../src/composables/useConfirm", () => ({ useConfirm: () => ({ ask: async () => confirm.answer }) }));

const CURRENT = { host: "192.168.1.10\\SQLEXPRESS", port: "", name: "obedy", user: "obedy", trust_certificate: true };

afterEach(() => {
  confirm.answer = true;
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function button(wrapper: ReturnType<typeof mount>, text: string) {
  return wrapper.findAll("button").find((item) => item.text().startsWith(text))!;
}

async function openForm(routes: Record<string, [number, unknown]>) {
  const spy = routeFetch({ "/api/database": [200, CURRENT], ...routes });
  const wrapper = mount(DatabasePage);
  await flushPromises();
  await button(wrapper, "Изменить подключение").trigger("click");
  const password = wrapper.find('input[type="password"]');
  await password.setValue("New-Pa55");
  return { wrapper, spy };
}

describe("DatabasePage", () => {
  it("shows the current connection without the password", async () => {
    routeFetch({ "/api/database": [200, CURRENT] });
    const wrapper = mount(DatabasePage);
    await flushPromises();

    expect(wrapper.text()).toContain("192.168.1.10\\SQLEXPRESS");
    expect(wrapper.text()).toContain("по умолчанию");
    expect(wrapper.text()).toContain("obedy");
  });

  it("checks a new connection before saving", async () => {
    const { wrapper, spy } = await openForm({ "/api/database/check": [200, { ok: false, message: "SQL Server не пустил", has_data: false }] });

    await button(wrapper, "Проверить").trigger("click");
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toBe("SQL Server не пустил");
    expect(bodySentTo(spy, "/api/database/check")).toEqual({ ...CURRENT, password: "New-Pa55" });
  });

  it("does nothing when the switch is not confirmed", async () => {
    confirm.answer = false;
    const { wrapper, spy } = await openForm({});

    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(wasRequested(spy, "/api/database", "PUT")).toBe(false);
  });

  it("saves, waits for the restart and reloads the page", async () => {
    vi.useFakeTimers();
    const reload = vi.fn();
    vi.stubGlobal("location", { ...window.location, reload });
    const { wrapper } = await openForm({
      "/api/database": [200, { ok: true, message: "Подключение сохранено", has_data: true }],
      "/api/health": [200, { status: "ok", database: "ok" }],
    });

    await wrapper.get("form").trigger("submit");
    await flushPromises();
    expect(wrapper.get('[role="status"]').text()).toContain("перезапускается");

    await vi.advanceTimersByTimeAsync(2000);

    expect(reload).toHaveBeenCalled();
  });
});
