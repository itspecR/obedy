import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import DateField from "../src/components/ui/DateField.vue";
import InfoTip from "../src/components/ui/InfoTip.vue";
import PersonPicker from "../src/components/ui/PersonPicker.vue";
import TimeField from "../src/components/ui/TimeField.vue";
import TimeWheel from "../src/components/ui/TimeWheel.vue";
import { MINUTES, indexAt, parseClock } from "../src/components/ui/timeWheel";
import { monthGrid, shiftDay, weekdayIndex } from "../src/format/calendar";

describe("calendar math", () => {
  it("builds six Monday-first weeks around the month", () => {
    const grid = monthGrid("2026-10");

    expect(grid).toHaveLength(42);
    expect(grid[0]).toEqual({ day: "2026-09-28", inMonth: false });
    expect(grid[3]).toEqual({ day: "2026-10-01", inMonth: true });
    expect(weekdayIndex("2026-10-05")).toBe(0);
    expect(weekdayIndex("2026-10-11")).toBe(6);
    expect(shiftDay("2026-12-31", 1)).toBe("2027-01-01");
  });
});

describe("time wheel math", () => {
  it("reads only real clock values", () => {
    expect(parseClock("09:05")).toEqual({ hours: 9, minutes: 5 });
    expect(parseClock("24:00")).toBeNull();
    expect(parseClock("9:5")).toBeNull();
    expect(parseClock("")).toBeNull();
  });

  it("finds the centred item from the scroll position", () => {
    expect(indexAt(0, 24)).toBe(0);
    expect(indexAt(81, 24)).toBe(2);
    expect(indexAt(5000, 24)).toBe(23);
  });
});

describe("DateField", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-08T09:00:00Z"));
  });
  afterEach(() => vi.useRealTimers());

  it("shows the day in Russian format and picks another day", async () => {
    const wrapper = mount(DateField, { props: { label: "День", modelValue: "2026-10-08", max: "2026-10-08" }, attachTo: document.body });

    expect(wrapper.get(".field-control").text()).toBe("08.10.2026");
    await wrapper.get(".field-control").trigger("click");
    expect(wrapper.get(".date-field__month").text()).toBe("Октябрь 2026");
    expect(wrapper.get('[aria-label="08.10.2026"]').attributes("aria-pressed")).toBe("true");
    expect(wrapper.get('[aria-label="09.10.2026"]').attributes("disabled")).toBeDefined();
    expect(wrapper.get('[aria-label="Следующий месяц"]').attributes("disabled")).toBeDefined();
    await wrapper.get('[aria-label="05.10.2026"]').trigger("click");

    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["2026-10-05"]);
    expect(wrapper.emitted("change")?.[0]).toEqual(["2026-10-05"]);
    expect(wrapper.find(".date-field__panel").exists()).toBe(false);
    wrapper.unmount();
  });

  it("moves between months and returns to today", async () => {
    const wrapper = mount(DateField, { props: { label: "С", modelValue: "" }, attachTo: document.body });

    expect(wrapper.get(".field-control").text()).toBe("дд.мм.гггг");
    await wrapper.get(".field-control").trigger("click");
    await wrapper.get('[aria-label="Предыдущий месяц"]').trigger("click");
    expect(wrapper.get(".date-field__month").text()).toBe("Сентябрь 2026");
    await wrapper.findAll("button").find((button) => button.text() === "Сегодня")?.trigger("click");

    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["2026-10-08"]);
    wrapper.unmount();
  });

  it("closes on Escape without changing the value", async () => {
    const wrapper = mount(DateField, { props: { label: "С", modelValue: "2026-10-01" }, attachTo: document.body });

    await wrapper.get(".field-control").trigger("click");
    await wrapper.get(".date-field").trigger("keydown", { key: "Escape" });

    expect(wrapper.find(".date-field__panel").exists()).toBe(false);
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
    wrapper.unmount();
  });
});

describe("TimeField", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-08T09:07:00Z"));
  });
  afterEach(() => vi.useRealTimers());

  it("starts an empty field at the current time and turns the wheels", async () => {
    const wrapper = mount(TimeField, { props: { label: "Вернулся", modelValue: "" }, attachTo: document.body });

    expect(wrapper.get(".field-control").text()).toBe("--:--");
    await wrapper.get(".field-control").trigger("click");
    const [hours, minutes] = wrapper.findAll(".wheel");
    expect(hours.attributes("aria-valuetext")).toBe("12");
    expect(minutes.attributes("aria-valuetext")).toBe("07");
    await minutes.trigger("keydown", { key: "ArrowDown" });
    await hours.trigger("keydown", { key: "ArrowUp" });

    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual(["11:08"]);
    await wrapper.findAll("button").find((button) => button.text() === "Готово")?.trigger("click");
    expect(wrapper.find(".time-field__panel").exists()).toBe(false);
    wrapper.unmount();
  });

  it("opens on the saved time", async () => {
    const wrapper = mount(TimeField, { props: { label: "Ушёл", modelValue: "13:45" }, attachTo: document.body });

    await wrapper.get(".field-control").trigger("click");

    expect(wrapper.findAll(".wheel").map((wheel) => wheel.attributes("aria-valuetext"))).toEqual(["13", "45"]);
    expect(wrapper.find(".wheel__item--chosen").text()).toBe("13");
    wrapper.unmount();
  });
});

describe("PersonPicker", () => {
  const PEOPLE = [
    { id: 1, name: "Иванов Иван", login: "ivanov" },
    { id: 2, name: "Иванова Анна", login: "ivanova" },
    { id: 3, name: "Петров Пётр", login: "petrov" },
  ];

  const picker = (modelValue: number | null = null) => mount(PersonPicker, { props: { label: "Сотрудник", people: PEOPLE, modelValue }, attachTo: document.body });
  const names = (wrapper: ReturnType<typeof picker>) => wrapper.findAll(".picker__name").map((name) => name.text());

  it("narrows the list with every typed letter", async () => {
    const wrapper = picker();
    const input = wrapper.get("input");

    await input.setValue("и");
    expect(names(wrapper)).toEqual(["Иванов Иван", "Иванова Анна"]);
    await input.setValue("иванова");
    expect(names(wrapper)).toEqual(["Иванова Анна"]);
    await input.setValue("петр");
    expect(names(wrapper)).toEqual(["Петров Пётр"]);
    await input.setValue("сидоров");
    expect(wrapper.text()).toContain("Никого не нашли");
    wrapper.unmount();
  });

  it("opens the list on click, not on focus", async () => {
    const wrapper = picker();

    await wrapper.get("input").trigger("focus");
    expect(wrapper.find("[role=listbox]").exists()).toBe(false);
    await wrapper.get("input").trigger("click");
    expect(names(wrapper)).toEqual(["Иванов Иван", "Иванова Анна", "Петров Пётр"]);
    wrapper.unmount();
  });

  it("chooses with the keyboard", async () => {
    const wrapper = picker();
    const input = wrapper.get("input");

    await input.setValue("иван");
    await input.trigger("keydown", { key: "ArrowDown" });
    await input.trigger("keydown", { key: "Enter" });

    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual([2]);
    expect((input.element as HTMLInputElement).value).toBe("Иванова Анна");
    expect(wrapper.find("[role=listbox]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("drops the choice when the name is edited", async () => {
    const wrapper = picker(3);
    const input = wrapper.get("input");

    expect((input.element as HTMLInputElement).value).toBe("Петров Пётр");
    await input.setValue("Петров");

    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual([null]);
    wrapper.unmount();
  });
});

describe("InfoTip", () => {
  it("opens the hint on click and closes it on Escape", async () => {
    const wrapper = mount(InfoTip, { props: { text: "Пояснение к блоку", label: "Лимит" }, attachTo: document.body });
    const button = wrapper.get('[aria-label="Подсказка: Лимит"]');

    expect(wrapper.text()).not.toContain("Пояснение к блоку");
    await button.trigger("click");
    expect(button.attributes("aria-expanded")).toBe("true");
    expect(wrapper.get("[role=note]").text()).toBe("Пояснение к блоку");
    await wrapper.trigger("keydown", { key: "Escape" });
    expect(wrapper.find("[role=note]").exists()).toBe(false);
    wrapper.unmount();
  });
});

describe("TimeWheel drag", () => {
  it("turns with the mouse held down and ignores the click that ends the drag", async () => {
    const wrapper = mount(TimeWheel, { props: { values: MINUTES, label: "Минуты", modelValue: 10 }, attachTo: document.body });
    const wheel = wrapper.get(".wheel");
    (wheel.element as HTMLElement).scrollTop = 400;

    await wheel.trigger("pointerdown", { pointerType: "mouse", button: 0, pointerId: 1, clientY: 300 });
    await wheel.trigger("pointermove", { pointerType: "mouse", pointerId: 1, clientY: 220 });
    expect(wheel.classes()).toContain("wheel--dragging");
    await wheel.trigger("pointerup", { pointerType: "mouse", pointerId: 1, clientY: 220 });
    await wrapper.findAll(".wheel__item")[30].trigger("click");

    expect(wrapper.emitted("update:modelValue")).toEqual([[12]]);
    expect(wheel.classes()).not.toContain("wheel--dragging");
    wrapper.unmount();
  });

  it("leaves touch scrolling to the browser", async () => {
    const wrapper = mount(TimeWheel, { props: { values: MINUTES, label: "Минуты", modelValue: 10 }, attachTo: document.body });
    const wheel = wrapper.get(".wheel");

    await wheel.trigger("pointerdown", { pointerType: "touch", pointerId: 2, clientY: 300 });
    await wheel.trigger("pointermove", { pointerType: "touch", pointerId: 2, clientY: 100 });
    await wheel.trigger("pointerup", { pointerType: "touch", pointerId: 2, clientY: 100 });

    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
    wrapper.unmount();
  });
});
