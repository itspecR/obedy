import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Absence } from "../src/api/absences";
import AbsenceDialog from "../src/components/absences/AbsenceDialog.vue";
import { formProblem, rangeText, wholeMonth } from "../src/components/absences/absences";
import { useConfirm } from "../src/composables/useConfirm";
import { useToasts } from "../src/composables/useToasts";
import { todayIso } from "../src/format/dateTime";
import AbsencesPage from "../src/pages/AbsencesPage.vue";
import { bodySentTo, choosePerson, routeFetch, wasRequested } from "./helpers";

const PEOPLE = [
  { id: 11, name: "Иванов Иван", login: "ivanov" },
  { id: 12, name: "Петрова Анна", login: "petrova" },
];
const VACATION: Absence = { id: 5, person_id: 11, name: "Иванов Иван", login: "ivanov", first: "2026-11-02", last: "2026-11-13", kind: "vacation", note: "приказ № 45" };
const MONTH = wholeMonth(todayIso());
const LIST = `/api/absences?date_from=${MONTH.from}&date_to=${MONTH.to}`;

afterEach(() => {
  vi.unstubAllGlobals();
  const { items, dismiss } = useToasts();
  [...items].forEach((toast) => dismiss(toast.id));
});

describe("absence helpers", () => {
  it("covers the whole month around a day", () => {
    expect(wholeMonth("2026-02-10")).toEqual({ from: "2026-02-01", to: "2026-02-28" });
    expect(wholeMonth("2028-02-29")).toEqual({ from: "2028-02-01", to: "2028-02-29" });
  });

  it("writes one day or a range", () => {
    expect(rangeText("2026-11-02", "2026-11-02")).toBe("02.11.2026");
    expect(rangeText("2026-11-02", "2026-11-13")).toBe("02.11.2026 — 13.11.2026");
  });

  it("explains missing or reversed dates", () => {
    expect(formProblem({ first: "", last: "2026-11-02", kind: "sick", note: "" })).toBe("Укажите даты «с» и «по»");
    expect(formProblem({ first: "2026-11-03", last: "2026-11-02", kind: "sick", note: "" })).toBe("Дата «по» не может быть раньше даты «с»");
    expect(formProblem({ first: "2026-11-02", last: "2026-11-02", kind: "sick", note: "" })).toBe("");
  });
});

describe("AbsenceDialog", () => {
  it("marks a sick leave for a chosen person", async () => {
    const spy = routeFetch({ "/api/lunch/board/people": [200, PEOPLE], "/api/absences": [201, { ...VACATION, kind: "sick" }] });
    const wrapper = mount(AbsenceDialog, { props: { day: "2026-11-02" }, attachTo: document.body });
    await flushPromises();

    expect(wrapper.get("button[type=submit]").attributes("disabled")).toBeDefined();
    await choosePerson(wrapper, "иван", "Иванов Иван");
    await wrapper.findAll("[role=radio]").find((radio) => radio.text() === "Больничный")?.trigger("click");
    await wrapper.findAll("input").at(-1)?.setValue("справка");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(bodySentTo(spy, "/api/absences")).toEqual({ first: "2026-11-02", last: "2026-11-02", kind: "sick", note: "справка", account_id: 11 });
    expect(wrapper.emitted("saved")).toHaveLength(1);
    expect(useToasts().items.map((toast) => toast.text)).toContain("Отсутствие отмечено");
    wrapper.unmount();
  });

  it("edits an absence without choosing the person again", async () => {
    const spy = routeFetch({ "/api/absences/5": [200, VACATION] });
    const wrapper = mount(AbsenceDialog, { props: { day: "2026-11-20", absence: VACATION }, attachTo: document.body });
    await flushPromises();

    expect(wrapper.find("input[role=combobox]").exists()).toBe(false);
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(bodySentTo(spy, "/api/absences/5")).toEqual({ first: "2026-11-02", last: "2026-11-13", kind: "vacation", note: "приказ № 45" });
    expect(wasRequested(spy, "/api/lunch/board/people", "GET")).toBe(false);
    wrapper.unmount();
  });

  it("shows the server refusal for overlapping dates", async () => {
    routeFetch({ "/api/lunch/board/people": [200, PEOPLE], "/api/absences": [400, { detail: "В эти даты уже есть отсутствие: Отпуск 02.11.2026 — 13.11.2026. Исправьте его" }] });
    const wrapper = mount(AbsenceDialog, { props: { day: "2026-11-05" }, attachTo: document.body });
    await flushPromises();

    await choosePerson(wrapper, "иван", "Иванов Иван");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(useToasts().items.map((toast) => toast.text)).toContain("В эти даты уже есть отсутствие: Отпуск 02.11.2026 — 13.11.2026. Исправьте его");
    wrapper.unmount();
  });
});

describe("AbsencesPage", () => {
  it("lists absences of the current month with kind and note", async () => {
    routeFetch({ [LIST]: [200, [VACATION]] });
    const wrapper = mount(AbsencesPage, { attachTo: document.body });
    await flushPromises();

    expect(wrapper.get(".absences__row").text()).toContain("Иванов Иван");
    expect(wrapper.get(".absences__row").text()).toContain("02.11.2026 — 13.11.2026");
    expect(wrapper.get(".absences__row .badge").text()).toBe("Отпуск");
    expect(wrapper.get(".absences__note").text()).toBe("приказ № 45");
    wrapper.unmount();
  });

  it("explains an empty period", async () => {
    routeFetch({ [LIST]: [200, []] });
    const wrapper = mount(AbsencesPage);
    await flushPromises();

    expect(wrapper.get(".absences__empty-title").text()).toBe("В этот период отсутствий нет");
  });

  it("deletes an absence after confirmation and reloads the list", async () => {
    const spy = routeFetch({ [LIST]: [200, [VACATION]], "/api/absences/5": [204, null] });
    const wrapper = mount(AbsencesPage, { attachTo: document.body });
    await flushPromises();

    await wrapper.get(".more__button").trigger("click");
    await wrapper.findAll("[role=menuitem]").find((item) => item.text() === "Удалить")?.trigger("click");
    expect(useConfirm().current.request?.title).toBe("Удалить отсутствие?");
    useConfirm().answer(true);
    await flushPromises();

    expect(wasRequested(spy, "/api/absences/5", "DELETE")).toBe(true);
    expect(spy.mock.calls.filter(([url]) => url === LIST)).toHaveLength(2);
    wrapper.unmount();
  });

  it("offers a retry when the list cannot be loaded", async () => {
    routeFetch({ [LIST]: [500, { detail: "На сервере произошла ошибка" }] });
    const wrapper = mount(AbsencesPage);
    await flushPromises();

    expect(wrapper.get("[role=alert]").text()).toContain("На сервере произошла ошибка");
  });
});
