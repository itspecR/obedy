import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { LunchRules } from "../src/api/lunchRules";
import { draftFrom, formFrom, toggleDay } from "../src/components/rules/draft";
import { useToasts } from "../src/composables/useToasts";
import RulesPage from "../src/pages/RulesPage.vue";
import { useSession } from "../src/stores/session";
import { bodySentTo, chooseTime, routeFetch, shownTime, infoText } from "./helpers";
import { me } from "./people";

function rules(overrides: Partial<LunchRules> = {}): LunchRules {
  return {
    limit_minutes: 45,
    workdays: "12345",
    day_end: "18:00:00",
    window_enabled: false,
    window_start: "12:00:00",
    window_end: "15:00:00",
    updated_at: "2026-10-08T09:00:00Z",
    min_limit_minutes: 5,
    max_limit_minutes: 240,
    ...overrides,
  };
}

describe("rules draft", () => {
  it("shows times without seconds and sends the limit as a number", () => {
    const draft = draftFrom(rules());

    expect([draft.day_end, draft.window_start, draft.limit_minutes]).toEqual(["18:00", "12:00", "45"]);
    expect(formFrom({ ...draft, limit_minutes: " 30 " }).limit_minutes).toBe(30);
  });

  it("toggles weekdays keeping them in order", () => {
    expect(toggleDay("12345", "6")).toBe("123456");
    expect(toggleDay("135", "3")).toBe("15");
    expect(toggleDay("", "7")).toBe("7");
  });
});

describe("RulesPage", () => {
  beforeEach(() => setActivePinia(createPinia()));
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  async function mounted(save: [number, unknown] = [200, rules()]) {
    const spy = vi.fn((url: string, init?: RequestInit) => {
      const [status, body] = init?.method === "PUT" ? save : [200, rules()];
      return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
    });
    vi.stubGlobal("fetch", spy);
    const wrapper = mount(RulesPage);
    await flushPromises();
    return { spy, wrapper };
  }

  const day = (wrapper: Awaited<ReturnType<typeof mounted>>["wrapper"], name: string) => wrapper.get(`[aria-label="${name}"]`);

  it("shows current rules with the allowed limit range", async () => {
    const { wrapper } = await mounted();

    expect(await infoText(wrapper, "Лимит обеда, минут")).toContain("От 5 до 240 мин");
    expect(day(wrapper, "Пятница").attributes("aria-pressed")).toBe("true");
    expect(day(wrapper, "Суббота").attributes("aria-pressed")).toBe("false");
    expect(wrapper.get("button[type=submit]").attributes("disabled")).toBeDefined();
    expect(wrapper.findAll(".time-field")).toHaveLength(1);
    expect(shownTime(wrapper, "Конец рабочего дня")).toBe("18:00");
  });

  it("saves changed days, limit and lunch window", async () => {
    const saved = rules({ limit_minutes: 30, workdays: "123456", window_enabled: true, updated_at: "2026-10-08T10:00:00Z" });
    const { spy, wrapper } = await mounted([200, saved]);

    await day(wrapper, "Суббота").trigger("click");
    await wrapper.get("input[type=number]").setValue("30");
    await wrapper.get("[role=switch]").trigger("click");
    expect(wrapper.findAll(".time-field")).toHaveLength(3);
    await chooseTime(wrapper, "До", "15:30");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(bodySentTo(spy, "/api/lunch/rules")).toEqual({
      limit_minutes: 30,
      workdays: "123456",
      day_end: "18:00",
      window_enabled: true,
      window_start: "12:00",
      window_end: "15:30",
    });
    expect(useToasts().items.map((toast) => toast.text)).toContain("Правила обеда сохранены");
    expect(wrapper.get("button[type=submit]").attributes("disabled")).toBeDefined();
  });

  it("shows the server explanation when rules are rejected", async () => {
    const { wrapper } = await mounted([400, { detail: "Отметьте хотя бы один рабочий день" }]);

    for (const name of ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]) {
      await day(wrapper, name).trigger("click");
    }
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(useToasts().items.map((toast) => toast.text)).toContain("Отметьте хотя бы один рабочий день");
  });

  it("reverts unsaved changes", async () => {
    const { wrapper } = await mounted();

    await day(wrapper, "Воскресенье").trigger("click");
    await wrapper.get("button.button--ghost").trigger("click");

    expect(day(wrapper, "Воскресенье").attributes("aria-pressed")).toBe("false");
    expect(wrapper.find("button.button--ghost").exists()).toBe(false);
  });

  it("offers a retry when rules cannot be loaded", async () => {
    routeFetch({ "/api/lunch/rules": [500, { detail: "На сервере произошла ошибка" }] });
    const wrapper = mount(RulesPage);
    await flushPromises();

    expect(wrapper.get("[role=alert]").text()).toContain("На сервере произошла ошибка");
    expect(wrapper.get("[role=alert] button").text()).toBe("Повторить");
  });
});

describe("RulesPage rabbit switch", () => {
  beforeEach(() => setActivePinia(createPinia()));
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  async function mountedAs(role: "admin" | "hr", saved: [number, unknown] = [200, { rabbit: true }]) {
    useSession().me = me(role);
    const spy = vi.fn((url: string, init?: RequestInit) => {
      const routes: Record<string, [number, unknown]> = {
        "/api/lunch/rules": [200, rules()],
        "/api/appearance": [200, { rabbit: false }],
        "/api/appearance/rabbit": saved,
      };
      const [status, body] = routes[url] ?? [404, { detail: "Не найдено" }];
      return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
    });
    vi.stubGlobal("fetch", spy);
    const wrapper = mount(RulesPage);
    await flushPromises();
    return { spy, wrapper };
  }

  const rabbitSwitch = (wrapper: Awaited<ReturnType<typeof mountedAs>>["wrapper"]) => wrapper.get(".rabbit-switch [role=switch]");

  it("lets the admin switch the rabbit on", async () => {
    const { spy, wrapper } = await mountedAs("admin");
    const toggle = rabbitSwitch(wrapper);

    expect(toggle.attributes("aria-checked")).toBe("false");
    await toggle.trigger("click");
    await flushPromises();

    expect(bodySentTo(spy, "/api/appearance/rabbit")).toEqual({ enabled: true });
    expect(rabbitSwitch(wrapper).attributes("aria-checked")).toBe("true");
    expect(useToasts().items.map((toast) => toast.text)).toContain("Кролик включён");
  });

  it("keeps the switch as it was when saving fails", async () => {
    const { wrapper } = await mountedAs("admin", [500, { detail: "На сервере произошла ошибка" }]);

    await rabbitSwitch(wrapper).trigger("click");
    await flushPromises();

    expect(rabbitSwitch(wrapper).attributes("aria-checked")).toBe("false");
    expect(useToasts().items.map((toast) => toast.text)).toContain("На сервере произошла ошибка");
  });

  it("hides the switch from HR", async () => {
    const { spy, wrapper } = await mountedAs("hr");

    expect(wrapper.text()).not.toContain("Анимация с кроликом");
    expect(spy.mock.calls.some(([url]) => url === "/api/appearance")).toBe(false);
  });
});
