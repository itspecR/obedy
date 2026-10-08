import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Board, BoardEntry } from "../src/api/board";
import type { Lunch } from "../src/api/lunch";
import BoardList from "../src/components/board/BoardList.vue";
import CorrectionDialog from "../src/components/board/CorrectionDialog.vue";
import { EMPTY_BOARD_FILTER, departmentsOf, filterEntries, groupEntries } from "../src/components/board/groups";
import { useToasts } from "../src/composables/useToasts";
import BoardPage from "../src/pages/BoardPage.vue";
import { bodySentTo, routeFetch, wasRequested } from "./helpers";

const NOON = "2026-10-08T09:00:00Z";
const at = (minutes: number) => Date.parse(NOON) + minutes * 60_000;
const iso = (minutes: number) => new Date(at(minutes)).toISOString();

function entry(id: number, name: string, lunch: Partial<Lunch> = {}, department = "Склад"): BoardEntry {
  return {
    person: { id, name, login: `user${id}`, department, position: "Кассир" },
    lunch: {
      id,
      day: "2026-10-08",
      started_at: NOON,
      ended_at: null,
      limit_minutes: 45,
      status: "ongoing",
      duration_seconds: 0,
      auto_closed: false,
      correction: null,
      ...lunch,
    },
    can_correct: true,
  };
}

const AWAY_EARLY = entry(1, "Ранний Роман", { started_at: iso(-50) });
const AWAY_LATE = entry(2, "Поздний Пётр", { started_at: iso(-10) }, "Бухгалтерия");
const OVERRUN = entry(3, "Долгий Денис", { ended_at: iso(-5), status: "overrun", duration_seconds: 3000 });
const UNRETURNED = entry(4, "Забывчивая Зоя", { ended_at: iso(360), status: "unreturned", auto_closed: true });
const RETURNED = entry(5, "Вовремя Вера", { ended_at: iso(30), status: "on_time", duration_seconds: 1800 }, "Бухгалтерия");
const ENTRIES = [AWAY_LATE, AWAY_EARLY, OVERRUN, UNRETURNED, RETURNED];

function board(overrides: Partial<Board> = {}): Board {
  return { server_time: NOON, day: "2026-10-08", today: "2026-10-08", warning_minutes: 5, entries: ENTRIES, ...overrides };
}

const names = (entries: BoardEntry[]) => entries.map((item) => item.person.name);

describe("board groups", () => {
  it("puts the longest overdue lunch on top and splits the rest", () => {
    const groups = groupEntries(ENTRIES, at(0));

    expect(names(groups.away)).toEqual(["Ранний Роман", "Поздний Пётр"]);
    expect(names(groups.violations)).toEqual(["Долгий Денис", "Забывчивая Зоя"]);
    expect(names(groups.returned)).toEqual(["Вовремя Вера"]);
  });

  it("filters by words and department", () => {
    expect(names(filterEntries(ENTRIES, { ...EMPTY_BOARD_FILTER, query: "петр" }))).toEqual(["Поздний Пётр"]);
    expect(names(filterEntries(ENTRIES, { query: "", department: "Бухгалтерия" }))).toEqual(["Поздний Пётр", "Вовремя Вера"]);
    expect(departmentsOf(ENTRIES)).toEqual(["Бухгалтерия", "Склад"]);
  });
});

describe("BoardList", () => {
  const list = (entries: BoardEntry[], now = at(0)) =>
    mount(BoardList, { props: { title: "На обеде сейчас", entries, now, warningMinutes: 5, empty: "Сейчас никто не обедает" } });

  it("counts down ongoing lunches in colour", () => {
    const rows = list([AWAY_EARLY, AWAY_LATE]).findAll(".board-list__row");

    expect(rows[0].get(".board-list__timer").text()).toBe("Превышение +5 мин");
    expect(rows[0].get(".board-list__timer").classes()).toContain("board-list__timer--alarm");
    expect(rows[1].get(".board-list__timer").text()).toBe("35:00");
  });

  it("shows duration, status, correction and the menu only when allowed", async () => {
    const corrected = { ...RETURNED, lunch: { ...RETURNED.lunch, correction: { by: "Кадрова Ольга", at: NOON, reason: "Забыл нажать" } } };
    const own = { ...OVERRUN, can_correct: false };
    const wrapper = list([corrected, own]);
    const rows = wrapper.findAll(".board-list__row");

    expect(rows[0].text()).toContain("30 мин");
    expect(rows[0].text()).toContain("Исправлено: Кадрова Ольга. Причина: Забыл нажать");
    expect(rows[1].text()).toContain("Превышение");
    expect(rows[1].find("button").exists()).toBe(false);
    await rows[0].get("button").trigger("click");
    expect(wrapper.emitted("correct")?.[0]).toEqual([corrected]);
  });

  it("explains an empty block", () => {
    expect(list([]).text()).toContain("Сейчас никто не обедает");
  });
});

describe("CorrectionDialog", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    const { items, dismiss } = useToasts();
    [...items].forEach((toast) => dismiss(toast.id));
  });

  it("needs a return time and a reason, then saves the correction", async () => {
    const saved = { ...UNRETURNED, lunch: { ...UNRETURNED.lunch, status: "on_time" as const } };
    const spy = routeFetch({ "/api/lunch/board/4/correction": [200, saved] });
    const wrapper = mount(CorrectionDialog, { props: { entry: UNRETURNED }, attachTo: document.body });
    const [started, ended] = wrapper.findAll("input[type=time]");
    const submit = wrapper.get("button[type=submit]");

    expect((started.element as HTMLInputElement).value).toBe("12:00");
    expect((ended.element as HTMLInputElement).value).toBe("");
    expect(submit.attributes("disabled")).toBeDefined();
    await ended.setValue("12:40");
    await wrapper.get("textarea").setValue("Забыл нажать «Вернулся»");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(bodySentTo(spy, "/api/lunch/board/4/correction")).toEqual({ started_at: "12:00", ended_at: "12:40", reason: "Забыл нажать «Вернулся»" });
    expect(wrapper.emitted("saved")?.[0]).toEqual([saved]);
    wrapper.unmount();
  });

  it("shows the server refusal", async () => {
    routeFetch({ "/api/lunch/board/3/correction": [400, { detail: "Время возврата ещё не наступило" }] });
    const wrapper = mount(CorrectionDialog, { props: { entry: OVERRUN }, attachTo: document.body });

    await wrapper.get("textarea").setValue("Проверка");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(useToasts().items.map((toast) => toast.text)).toContain("Время возврата ещё не наступило");
    expect(wrapper.emitted("saved")).toBeUndefined();
    wrapper.unmount();
  });
});

describe("BoardPage", () => {
  beforeEach(() => setActivePinia(createPinia()));
  afterEach(() => vi.unstubAllGlobals());

  async function mounted(routes: Record<string, [number, unknown]>) {
    const spy = routeFetch(routes);
    const wrapper = mount(BoardPage);
    await flushPromises();
    return { spy, wrapper };
  }

  it("shows the three blocks for today", async () => {
    const { wrapper } = await mounted({ "/api/lunch/board": [200, board()] });
    const titles = wrapper.findAll(".board-list__title").map((title) => title.text());

    expect(titles).toEqual(["На обеде сейчас 2", "С нарушениями 2", "Вернулись вовремя 1"]);
    expect(wrapper.text()).toContain("обновляется каждые 30 секунд");
  });

  it("filters by department", async () => {
    const { wrapper } = await mounted({ "/api/lunch/board": [200, board()] });

    await wrapper.get("select").setValue("Бухгалтерия");

    expect(wrapper.findAll(".board-list__name").map((name) => name.text())).toEqual(["Поздний Пётр", "Вовремя Вера"]);
  });

  it("opens a past day without the live block", async () => {
    const past = board({ day: "2026-10-07", entries: [UNRETURNED] });
    const { spy, wrapper } = await mounted({ "/api/lunch/board": [200, board()], "/api/lunch/board?day=2026-10-07": [200, past] });

    await wrapper.get("input[type=date]").setValue("2026-10-07");
    await wrapper.get("input[type=date]").trigger("change");
    await flushPromises();

    expect(wasRequested(spy, "/api/lunch/board?day=2026-10-07", "GET")).toBe(true);
    expect(wrapper.text()).toContain("Архив за ср, 07.10");
    expect(wrapper.findAll(".board-list__title").map((title) => title.text())).toEqual(["С нарушениями 1", "Вернулись вовремя 0"]);
    expect(wrapper.text()).toContain("Сегодня");
  });

  it("explains a day without lunches", async () => {
    const { wrapper } = await mounted({ "/api/lunch/board": [200, board({ entries: [] })] });

    expect(wrapper.text()).toContain("Сегодня ещё никто не уходил на обед");
  });

  it("offers a retry when the board cannot be loaded", async () => {
    const { wrapper } = await mounted({ "/api/lunch/board": [403, { detail: "Табло доступно HR и администратору" }] });

    expect(wrapper.get("[role=alert]").text()).toContain("Табло доступно HR и администратору");
  });
});
