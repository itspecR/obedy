import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { JournalEntry } from "../src/api/journal";
import { recentPeriod, rowValue, subjectName } from "../src/components/journal/entries";
import { useToasts } from "../src/composables/useToasts";
import JournalPage from "../src/pages/JournalPage.vue";
import { choosePerson, routeFetch } from "./helpers";

const WEEK = "/api/journal?date_from=2026-10-02&date_to=2026-10-08";
const PEOPLE = "/api/journal/people";
const ADMIN = { id: 1, name: "Администратор", login: "admin" };
const PETROVA = { id: 2, name: "Петрова Анна", login: "petrova" };

function entry(overrides: Partial<JournalEntry> = {}): JournalEntry {
  return {
    id: 10,
    created_at: "2026-10-08T09:15:00Z",
    action: "role_changed",
    actor: ADMIN,
    target: PETROVA,
    address: "10.0.0.7",
    details: [{ label: "Роль", before: "Сотрудник", after: "HR" }],
    ...overrides,
  };
}

const FAILED = entry({ id: 9, action: "login_failed", actor: null, target: null, details: [] });

describe("journal entries", () => {
  it("shows changes, new values and removed values", () => {
    expect(rowValue({ label: "Роль", before: "Сотрудник", after: "HR" })).toBe("Сотрудник → HR");
    expect(rowValue({ label: "Адрес", before: null, after: "10.0.0.0/24" })).toBe("10.0.0.0/24");
    expect(rowValue({ label: "Адрес", before: "10.0.0.0/24", after: null })).toBe("10.0.0.0/24");
  });

  it("names the attempted account or an unknown login on a failed sign-in", () => {
    expect(subjectName(FAILED)).toBe("Неизвестный логин");
    expect(subjectName({ ...FAILED, target: PETROVA })).toBe("Петрова Анна");
    expect(subjectName(entry())).toBe("Администратор");
  });

  it("opens on the last seven days", () => {
    expect(recentPeriod("2026-10-08")).toEqual({ from: "2026-10-02", to: "2026-10-08" });
  });
});

describe("JournalPage", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-08T09:00:00Z"));
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  async function mounted(routes: Record<string, [number, unknown]> = {}) {
    const spy = routeFetch({ [WEEK]: [200, { entries: [entry(), FAILED], has_more: false }], [PEOPLE]: [200, [ADMIN, PETROVA]], ...routes });
    const wrapper = mount(JournalPage, { attachTo: document.body });
    await flushPromises();
    return { spy, wrapper };
  }

  const requested = (spy: ReturnType<typeof routeFetch>) => spy.mock.calls.map(([url]) => url);

  it("lists who did what to whom with before and after", async () => {
    const { wrapper } = await mounted();
    const [changed, failed] = wrapper.findAll(".journal-list__row");

    expect(changed.text()).toContain("Изменена роль");
    expect(changed.get(".journal-list__who").text()).toContain("Администратор→Петрова Анна");
    expect(changed.text()).toContain("10.0.0.7");
    expect(changed.get(".journal-list__detail").text()).toBe("РольСотрудник → HR");
    expect(failed.get(".badge").classes()).toContain("badge--attention");
    expect(failed.text()).toContain("Неизвестный логин");
    expect(wrapper.text()).not.toContain("Показать ещё");
    wrapper.unmount();
  });

  it("filters by kind of action and by person", async () => {
    const { spy, wrapper } = await mounted({
      [`${WEEK}&category=logins`]: [200, { entries: [FAILED], has_more: false }],
      [`${WEEK}&person=2&category=logins`]: [200, { entries: [], has_more: false }],
    });

    await wrapper.findAll("[role=radio]").find((button) => button.text() === "Входы")?.trigger("click");
    await flushPromises();
    expect(wrapper.findAll(".journal-list__row")).toHaveLength(1);

    await choosePerson(wrapper, "петр", "Петрова Анна");
    await flushPromises();
    expect(requested(spy)).toContain(`${WEEK}&person=2&category=logins`);
    expect(wrapper.text()).toContain("За выбранный период записей нет");
    wrapper.unmount();
  });

  it("loads the next page after the last shown entry", async () => {
    const older = entry({ id: 3, action: "logout", target: null, details: [] });
    const { spy, wrapper } = await mounted({
      [WEEK]: [200, { entries: [entry()], has_more: true }],
      [`${WEEK}&before=10`]: [200, { entries: [older], has_more: false }],
    });

    await wrapper.findAll("button").find((button) => button.text() === "Показать ещё")?.trigger("click");
    await flushPromises();

    expect(requested(spy)).toContain(`${WEEK}&before=10`);
    expect(wrapper.findAll(".journal-list__row")).toHaveLength(2);
    expect(wrapper.text()).not.toContain("Показать ещё");
    wrapper.unmount();
  });

  it("explains a failed load", async () => {
    const { wrapper } = await mounted({ [WEEK]: [403, { detail: "Раздел доступен только администратору" }] });

    expect(wrapper.get("[role=alert]").text()).toContain("Раздел доступен только администратору");
    wrapper.unmount();
  });
});
