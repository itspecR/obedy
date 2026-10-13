import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import CalendarCard from "../src/components/rules/CalendarCard.vue";
import { entryOf, kindLabel, kindTone, yearOf } from "../src/components/rules/calendarDays";
import { useToasts } from "../src/composables/useToasts";
import { formatDay, todayIso } from "../src/format/dateTime";
import { bodySentTo, chooseDay, infoText, routeFetch, wasRequested } from "./helpers";

const YEAR = yearOf(todayIso());
const HOLIDAY = `${todayIso().slice(0, 8)}04`;
const SATURDAY = `${YEAR}-11-07`;
const CALENDAR = "/api/lunch/rules/calendar";
const yearUrl = (year: number) => `${CALENDAR}?year=${year}`;

async function mounted(routes: Record<string, [number, unknown]>) {
  const spy = routeFetch(routes);
  const wrapper = mount(CalendarCard);
  await flushPromises();
  return { spy, wrapper };
}

const rows = (wrapper: Awaited<ReturnType<typeof mounted>>["wrapper"]) => wrapper.findAll(".calendar__row").map((row) => row.text());

afterEach(() => {
  vi.unstubAllGlobals();
  const { items, dismiss } = useToasts();
  [...items].forEach((toast) => dismiss(toast.id));
});

describe("calendar days", () => {
  it("turns the chosen kind into the server form and back into a label", () => {
    expect(entryOf("2026-11-04", "holiday")).toEqual({ day: "2026-11-04", working: false });
    expect(entryOf("2026-11-07", "working")).toEqual({ day: "2026-11-07", working: true });
    expect([kindLabel({ day: "", working: false }), kindTone({ day: "", working: false })]).toEqual(["Выходной", "neutral"]);
    expect([kindLabel({ day: "", working: true }), kindTone({ day: "", working: true })]).toEqual(["Рабочий", "ok"]);
  });
});

describe("CalendarCard", () => {
  it("lists the days of the current year", async () => {
    const { wrapper } = await mounted({ [yearUrl(YEAR)]: [200, [{ day: SATURDAY, working: true }]] });

    expect(wrapper.get(".calendar__year").text()).toBe(String(YEAR));
    expect(rows(wrapper)).toEqual([`${formatDay(SATURDAY)}РабочийУбрать`]);
  });

  it("keeps the explanation in the info button", async () => {
    const { wrapper } = await mounted({ [yearUrl(YEAR)]: [200, []] });

    expect(await infoText(wrapper, "Праздники и переносы")).toContain("рабочие субботы");
    expect(wrapper.find(".calendar__text").exists()).toBe(false);
  });

  it("explains an empty year", async () => {
    const { wrapper } = await mounted({ [yearUrl(YEAR)]: [200, []] });

    expect(wrapper.get(".calendar__empty").text()).toContain(`На ${YEAR} год ничего не добавлено`);
  });

  it("adds a holiday and shows the updated list", async () => {
    const { spy, wrapper } = await mounted({ [yearUrl(YEAR)]: [200, []], [CALENDAR]: [201, [{ day: HOLIDAY, working: false }]] });

    await chooseDay(wrapper, "Дата", HOLIDAY);
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(bodySentTo(spy, CALENDAR)).toEqual({ day: HOLIDAY, working: false });
    expect(rows(wrapper)).toEqual([`${formatDay(HOLIDAY)}ВыходнойУбрать`]);
    expect(useToasts().items.map((toast) => toast.text)).toContain("День добавлен в календарь");
  });

  it("asks for a date before adding", async () => {
    const { spy, wrapper } = await mounted({ [yearUrl(YEAR)]: [200, []] });

    await wrapper.get("form").trigger("submit");

    expect(wrapper.get(".calendar__error").text()).toBe("Выберите дату");
    expect(wasRequested(spy, CALENDAR, "POST")).toBe(false);
  });

  it("shows the server explanation when a day changes nothing", async () => {
    const { wrapper } = await mounted({ [yearUrl(YEAR)]: [200, []], [CALENDAR]: [400, { detail: "Этот день и так выходной по правилам" }] });

    await chooseDay(wrapper, "Дата", HOLIDAY);
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(useToasts().items.map((toast) => toast.text)).toContain("Этот день и так выходной по правилам");
  });

  it("removes a day", async () => {
    const { spy, wrapper } = await mounted({ [yearUrl(YEAR)]: [200, [{ day: SATURDAY, working: true }]], [`${CALENDAR}/${SATURDAY}`]: [200, []] });

    await wrapper.get(".calendar__row button").trigger("click");
    await flushPromises();

    expect(wasRequested(spy, `${CALENDAR}/${SATURDAY}`, "DELETE")).toBe(true);
    expect(wrapper.find(".calendar__empty").exists()).toBe(true);
  });

  it("moves between years", async () => {
    const { wrapper } = await mounted({ [yearUrl(YEAR)]: [200, []], [yearUrl(YEAR + 1)]: [200, [{ day: `${YEAR + 1}-01-01`, working: false }]] });

    await wrapper.get('[aria-label="Следующий год"]').trigger("click");
    await flushPromises();

    expect(wrapper.get(".calendar__year").text()).toBe(String(YEAR + 1));
    expect(rows(wrapper)).toHaveLength(1);
  });

  it("offers a retry when the calendar cannot be loaded", async () => {
    const { wrapper } = await mounted({ [yearUrl(YEAR)]: [500, { detail: "На сервере произошла ошибка" }] });

    expect(wrapper.get(".calendar__failed").text()).toContain("На сервере произошла ошибка");
  });
});
