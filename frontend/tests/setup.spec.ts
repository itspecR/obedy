import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { decideSetup } from "../src/components/setup/setupRoute";
import SetupPage from "../src/pages/SetupPage.vue";
import { bodySentTo, routeFetch } from "./helpers";

const NOT_CONFIGURED = { configured: false, needs_admin: false };
const EMPTY_DATABASE = { configured: true, needs_admin: true };
const READY = { configured: true, needs_admin: false };

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("setup routing", () => {
  it("sends every page to setup until the database and the first admin exist", () => {
    expect(decideSetup("login", NOT_CONFIGURED)).toEqual({ name: "setup" });
    expect(decideSetup("board", EMPTY_DATABASE)).toEqual({ name: "setup" });
    expect(decideSetup("setup", NOT_CONFIGURED)).toBeNull();
  });

  it("closes setup once everything is ready", () => {
    expect(decideSetup("setup", READY)).toEqual({ name: "login" });
    expect(decideSetup("board", READY)).toBeNull();
  });
});

async function fill(wrapper: ReturnType<typeof mount>) {
  const inputs = wrapper.findAll("input:not([type=checkbox])");
  const values = ["abcd-efgh-jkmn", "192.168.1.10\\SQLEXPRESS", "", "obedy", "obedy", "Pa55-word"];
  for (const [index, value] of values.entries()) {
    await inputs[index].setValue(value);
  }
}

function button(wrapper: ReturnType<typeof mount>, text: string) {
  return wrapper.findAll("button").find((item) => item.text().startsWith(text))!;
}

describe("SetupPage", () => {
  it("checks the connection and shows the answer", async () => {
    const spy = routeFetch({
      "/api/setup/status": [200, NOT_CONFIGURED],
      "/api/setup/check": [200, { ok: false, message: "SQL Server не пустил", has_data: false }],
    });
    const wrapper = mount(SetupPage);
    await flushPromises();
    await fill(wrapper);

    await button(wrapper, "Проверить").trigger("click");
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toBe("SQL Server не пустил");
    expect(bodySentTo(spy, "/api/setup/check")).toMatchObject({ code: "abcd-efgh-jkmn", host: "192.168.1.10\\SQLEXPRESS", port: "", trust_certificate: true });
  });

  it("shows why the code was refused", async () => {
    routeFetch({ "/api/setup/status": [200, NOT_CONFIGURED], "/api/setup/check": [403, { detail: "Неверный код настройки" }] });
    const wrapper = mount(SetupPage);
    await flushPromises();
    await fill(wrapper);

    await button(wrapper, "Проверить").trigger("click");
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toBe("Неверный код настройки");
  });

  it("connects, waits for the restart and creates the first admin", async () => {
    vi.useFakeTimers();
    const routes: Record<string, [number, unknown]> = {
      "/api/setup/status": [200, NOT_CONFIGURED],
      "/api/setup/database": [200, { ok: true, message: "Подключение сохранено", has_data: false }],
      "/api/setup/admin": [200, { login: "admin", password: "Temp-Pass-1234" }],
    };
    const spy = routeFetch(routes);
    const wrapper = mount(SetupPage);
    await flushPromises();
    await fill(wrapper);

    await wrapper.get("form").trigger("submit");
    await flushPromises();
    expect(wrapper.get('[role="status"]').text()).toContain("перезапускается");

    routes["/api/setup/status"] = [200, EMPTY_DATABASE];
    await vi.advanceTimersByTimeAsync(2000);
    await button(wrapper, "Создать администратора").trigger("click");
    await flushPromises();

    expect(bodySentTo(spy, "/api/setup/admin")).toEqual({ code: "abcd-efgh-jkmn" });
    expect(wrapper.text()).toContain("admin");
    expect(wrapper.text()).toContain("Temp-Pass-1234");
  });

  it("opens on the admin step when the database is already connected", async () => {
    routeFetch({ "/api/setup/status": [200, EMPTY_DATABASE] });
    const wrapper = mount(SetupPage);
    await flushPromises();

    expect(wrapper.text()).toContain("Создать администратора");
  });
});
