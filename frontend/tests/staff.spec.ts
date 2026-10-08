import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { StaffMember } from "../src/api/staff";
import { EMPTY_FILTER, filterStaff } from "../src/components/staff/filters";
import StaffPage from "../src/pages/StaffPage.vue";
import { routeFetch } from "./helpers";

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
  afterEach(() => vi.unstubAllGlobals());

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
