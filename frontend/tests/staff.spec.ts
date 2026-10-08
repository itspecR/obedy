import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { StaffMember } from "../src/api/staff";
import { EMPTY_FILTER, filterStaff } from "../src/components/staff/filters";
import StaffPage from "../src/pages/StaffPage.vue";
import { useConfirm } from "../src/composables/useConfirm";
import { useToasts } from "../src/composables/useToasts";
import { useSession } from "../src/stores/session";
import { bodySentTo, routeFetch } from "./helpers";
import { me } from "./people";

function member(overrides: Partial<StaffMember> = {}): StaffMember {
  return {
    id: 1,
    login: "ivanov",
    full_name: "Иванов Иван",
    department: "Склад",
    position: "Кладовщик",
    role: "employee",
    source: "domain",
    status: "active",
    track_lunch: true,
    last_login_at: null,
    ...overrides,
  };
}

const PEOPLE = [
  member(),
  member({ id: 2, login: "petrov", full_name: "Пётр Петров", department: "Бухгалтерия", role: "hr", track_lunch: false }),
  member({ id: 3, login: "sidorov", full_name: "", department: "", position: "", status: "blocked", source: "local" }),
  member({ id: 4, login: "gone", full_name: "Ушедший", status: "gone" }),
];

const logins = (members: StaffMember[]) => members.map((item) => item.login);

describe("staff filters", () => {
  it("finds by several words across name, login, department and position", () => {
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, query: "иван склад" }))).toEqual(["ivanov"]);
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, query: "SIDOROV" }))).toEqual(["sidorov"]);
  });

  it("treats ё and е as the same letter", () => {
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, query: "петр" }))).toEqual(["petrov"]);
  });

  it("filters by role and status", () => {
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, role: "hr" }))).toEqual(["petrov"]);
    expect(logins(filterStaff(PEOPLE, { ...EMPTY_FILTER, status: "gone" }))).toEqual(["gone"]);
    expect(logins(filterStaff(PEOPLE, EMPTY_FILTER))).toEqual(["ivanov", "petrov", "sidorov", "gone"]);
  });
});

describe("StaffPage", () => {
  beforeEach(() => setActivePinia(createPinia()));
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  async function mounted(response: [number, unknown]) {
    routeFetch({ "/api/staff": response });
    const wrapper = mount(StaffPage);
    await flushPromises();
    return wrapper;
  }

  it("lists everyone with role, lunch tracking and coloured status", async () => {
    const wrapper = await mounted([200, PEOPLE]);
    const rows = wrapper.findAll(".staff__row");

    expect(wrapper.text()).toContain("Всего 4");
    expect(rows).toHaveLength(4);
    expect(rows[1].text()).toContain("Пётр Петров");
    expect(rows[1].text()).toContain("HR");
    expect(rows[1].text()).toContain("Не учитываются");
    expect(rows[2].text()).toContain("sidorov");
    expect(rows[2].text()).toContain("Отдел и должность не указаны");
    expect(rows[2].get(".badge").classes()).toContain("badge--alarm");
    expect(rows[3].get(".badge").text()).toBe("Нет в домене");
  });

  it("counts shown people and explains an empty search", async () => {
    const wrapper = await mounted([200, PEOPLE]);

    await wrapper.get("input").setValue("никого такого");

    expect(wrapper.text()).toContain("Показано 0 из 4");
    expect(wrapper.text()).toContain("Никого не нашли");
  });

  it("explains where people come from when there are none", async () => {
    const wrapper = await mounted([200, []]);

    expect(wrapper.text()).toContain("Сотрудников пока нет");
  });

  it("shows a load error with a retry button", async () => {
    const wrapper = await mounted([500, { detail: "На сервере произошла ошибка" }]);

    expect(wrapper.get('[role="alert"]').text()).toContain("На сервере произошла ошибка");
    expect(wrapper.findAll("button").some((button) => button.text() === "Повторить")).toBe(true);
  });
});

describe("StaffPage management", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    useSession().me = { ...me("admin"), login: "boss" };
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  async function opened(people: StaffMember[], login: string, routes: Record<string, [number, unknown]> = {}) {
    const spy = routeFetch({ "/api/staff": [200, people], ...routes });
    const wrapper = mount(StaffPage, { attachTo: document.body });
    await flushPromises();
    const target = people.find((person) => person.login === login);
    await wrapper.get(`[aria-label="Действия: ${target?.full_name || login}"]`).trigger("click");
    return { spy, wrapper };
  }

  const dialog = () => document.body.querySelector('[role="dialog"]') as HTMLElement;
  const buttonIn = (text: string) => [...dialog().querySelectorAll("button")].find((button) => button.textContent?.trim() === text) as HTMLButtonElement;

  it("changes the role and shows the server answer in the list", async () => {
    const promoted = member({ role: "hr", track_lunch: false });
    const { spy, wrapper } = await opened(PEOPLE, "ivanov", { "/api/staff/1/role": [200, promoted] });

    buttonIn("HR").click();
    await flushPromises();

    expect(bodySentTo(spy, "/api/staff/1/role")).toEqual({ role: "hr" });
    expect(wrapper.findAll(".staff__row")[0].text()).toContain("Не учитываются");
    wrapper.unmount();
  });

  it("switches lunch tracking", async () => {
    const { spy, wrapper } = await opened(PEOPLE, "ivanov", { "/api/staff/1/track-lunch": [200, member({ track_lunch: false })] });

    (dialog().querySelector('[role="switch"]') as HTMLButtonElement).click();
    await flushPromises();

    expect(bodySentTo(spy, "/api/staff/1/track-lunch")).toEqual({ track_lunch: false });
    wrapper.unmount();
  });

  it("asks before blocking and blocks after confirmation", async () => {
    const { spy, wrapper } = await opened(PEOPLE, "ivanov", { "/api/staff/1/blocked": [200, member({ status: "blocked" })] });

    buttonIn("Заблокировать").click();
    expect(useConfirm().current.request?.title).toBe("Заблокировать: Иванов Иван?");
    useConfirm().answer(true);
    await flushPromises();

    expect(bodySentTo(spy, "/api/staff/1/blocked")).toEqual({ blocked: true });
    expect(buttonIn("Разблокировать")).toBeTruthy();
    wrapper.unmount();
  });

  it("does not block when the admin changes their mind", async () => {
    const { spy, wrapper } = await opened(PEOPLE, "ivanov");

    buttonIn("Заблокировать").click();
    useConfirm().answer(false);
    await flushPromises();

    expect(bodySentTo(spy, "/api/staff/1/blocked")).toBeUndefined();
    wrapper.unmount();
  });

  it("keeps the admin from changing their own role or blocking themselves", async () => {
    const self = member({ id: 7, login: "boss", full_name: "Начальник", role: "admin" });
    const { wrapper } = await opened([self], "boss");

    expect(buttonIn("Сотрудник").disabled).toBe(true);
    expect(buttonIn("Заблокировать").disabled).toBe(true);
    expect(dialog().textContent).toContain("Свою роль изменить нельзя");
    wrapper.unmount();
  });

  it("shows the server refusal", async () => {
    const { wrapper } = await opened(PEOPLE, "ivanov", { "/api/staff/1/role": [409, { detail: "Нельзя: это последний активный администратор" }] });

    buttonIn("Администратор").click();
    await flushPromises();

    expect(useToasts().items.map((toast) => toast.text)).toContain("Нельзя: это последний активный администратор");
    wrapper.unmount();
  });
});
