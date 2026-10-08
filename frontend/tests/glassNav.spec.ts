import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, ref } from "vue";
import { useGlassNav } from "../src/composables/useGlassNav";

const ITEM_HEIGHT = 40;
const LINKS = ["/overview", "/students", "/staff", "/programs", "/logs"];

function layout(nav: HTMLElement): void {
  Object.defineProperty(nav, "clientWidth", { value: 200, configurable: true });
  Object.defineProperty(nav, "clientHeight", { value: ITEM_HEIGHT * LINKS.length, configurable: true });
  nav.querySelectorAll<HTMLElement>(":scope > a").forEach((link, index) => {
    Object.defineProperty(link, "offsetTop", { value: index * ITEM_HEIGHT, configurable: true });
    Object.defineProperty(link, "offsetLeft", { value: 0, configurable: true });
    Object.defineProperty(link, "offsetWidth", { value: 200, configurable: true });
    Object.defineProperty(link, "offsetHeight", { value: ITEM_HEIGHT, configurable: true });
  });
}

function mountNav(activeIndex = 0) {
  const navigate = vi.fn();
  const current = ref(LINKS[activeIndex]);
  const Harness = defineComponent({
    setup() {
      const nav = ref<HTMLElement | null>(null);
      const glass = useGlassNav(nav, {
        items: ":scope > a",
        isActive: (item) => item.classList.contains("side__item--active"),
        select: (item) => navigate(item.getAttribute("href")),
        changes: () => current.value,
      });
      return () =>
        h(
          "nav",
          {
            ref: nav,
            onPointerdown: glass.on.down,
            onPointermove: glass.on.move,
            onPointerup: glass.on.up,
            onPointercancel: glass.on.up,
            onClickCapture: glass.on.click,
            onKeydown: glass.on.keydown,
          },
          LINKS.map((href) => h("a", { href, class: ["side__item", href === current.value ? "side__item--active" : ""] }, href)),
        );
    },
  });
  const wrapper = mount(Harness, { attachTo: document.body });
  layout(wrapper.element as HTMLElement);
  return { wrapper, navigate, link: (index: number) => wrapper.findAll("a")[index].element as HTMLElement };
}

let clock = 0;

function pointer(target: HTMLElement, type: string, y: number, pointerType = "mouse", after = 16): PointerEvent {
  clock += after;
  const event = new PointerEvent(type, { bubbles: true, cancelable: true, clientX: 100, clientY: y, pointerId: 1, pointerType, button: 0 });
  Object.defineProperty(event, "timeStamp", { value: clock });
  target.dispatchEvent(event);
  return event;
}

function slide(target: HTMLElement, from: number, to: number, pointerType = "mouse", step = 4): void {
  const direction = Math.sign(to - from);
  for (let y = from + direction * step; direction * (to - y) >= 0; y += direction * step) {
    pointer(target, "pointermove", y, pointerType);
  }
}

const middle = (index: number) => index * ITEM_HEIGHT + ITEM_HEIGHT / 2;

describe("glass menu drag", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.useRealTimers();
    document.body.innerHTML = "";
  });

  it("drags the pill with the mouse and opens the section it is dropped on", () => {
    const { navigate, link } = mountNav(0);
    pointer(link(0), "pointerdown", middle(0));
    slide(link(0), middle(0), middle(3));
    pointer(link(3), "pointerup", middle(3), "mouse", 200);
    expect(navigate).toHaveBeenCalledWith("/programs");
  });

  it("throws the pill further on a quick flick", () => {
    const { navigate, link } = mountNav(0);
    pointer(link(0), "pointerdown", middle(0));
    slide(link(0), middle(0), middle(1), "mouse", 12);
    pointer(link(1), "pointerup", middle(1), "mouse", 16);
    expect(navigate.mock.calls[0][0]).not.toBe("/students");
    expect(["/staff", "/programs", "/logs"]).toContain(navigate.mock.calls[0][0]);
  });

  it("does not throw when the pointer rests before release", () => {
    const { navigate, link } = mountNav(0);
    pointer(link(0), "pointerdown", middle(0));
    slide(link(0), middle(0), middle(1), "mouse", 12);
    pointer(link(1), "pointerup", middle(1), "mouse", 300);
    expect(navigate).toHaveBeenCalledWith("/students");
  });

  it("swallows the click that follows a drag", () => {
    const { link } = mountNav(0);
    pointer(link(0), "pointerdown", middle(0));
    slide(link(0), middle(0), middle(2));
    pointer(link(2), "pointerup", middle(2), "mouse", 200);
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    link(2).dispatchEvent(click);
    expect(click.defaultPrevented).toBe(true);
  });

  it("leaves a plain click to the link", () => {
    const { navigate, link } = mountNav(0);
    pointer(link(3), "pointerdown", middle(3));
    pointer(link(3), "pointerup", middle(3));
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    link(3).dispatchEvent(click);
    expect(navigate).not.toHaveBeenCalled();
    expect(click.defaultPrevented).toBe(false);
  });

  it("does not drag from an inactive item with the mouse", () => {
    const { navigate, link } = mountNav(0);
    pointer(link(2), "pointerdown", middle(2));
    slide(link(2), middle(2), middle(4));
    pointer(link(4), "pointerup", middle(4), "mouse", 200);
    vi.advanceTimersByTime(100);
    expect(navigate).not.toHaveBeenCalled();
  });

  it("does not grab an inactive item on a quick touch swipe", () => {
    const { navigate, link } = mountNav(0);
    pointer(link(2), "pointerdown", middle(2), "touch");
    pointer(link(2), "pointermove", middle(2) + 30, "touch");
    vi.advanceTimersByTime(400);
    pointer(link(3), "pointermove", middle(4), "touch");
    pointer(link(4), "pointerup", middle(4), "touch");
    expect(navigate).not.toHaveBeenCalled();
  });

  it("grabs an inactive item after a touch hold", () => {
    const { navigate, link } = mountNav(0);
    pointer(link(1), "pointerdown", middle(1), "touch");
    vi.advanceTimersByTime(300);
    slide(link(1), middle(1), middle(3), "touch");
    pointer(link(3), "pointerup", middle(3), "touch", 200);
    expect(navigate).toHaveBeenCalledWith("/programs");
  });

  it("grabs the active item at once on touch", () => {
    const { navigate, link } = mountNav(0);
    pointer(link(0), "pointerdown", middle(0), "touch");
    slide(link(0), middle(0), middle(2), "touch");
    pointer(link(2), "pointerup", middle(2), "touch", 200);
    expect(navigate).toHaveBeenCalledWith("/staff");
  });

  it("moves focus through the menu with the arrow keys", () => {
    const { link } = mountNav(0);
    link(0).focus();
    link(0).dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
    expect(document.activeElement).toBe(link(1));
    link(1).dispatchEvent(new KeyboardEvent("keydown", { key: "End", bubbles: true }));
    expect(document.activeElement).toBe(link(4));
    link(4).dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
    expect(document.activeElement).toBe(link(0));
  });

  it("lets the next plain click through right after a drag", () => {
    const { link } = mountNav(0);
    pointer(link(0), "pointerdown", middle(0));
    slide(link(0), middle(0), middle(2));
    pointer(link(2), "pointerup", middle(2), "mouse", 200);
    pointer(link(3), "pointerdown", middle(3), "mouse", 300);
    pointer(link(3), "pointerup", middle(3));
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    link(3).dispatchEvent(click);
    expect(click.defaultPrevented).toBe(false);
  });

  it("pulls the pill to an inactive item held with the mouse and opens it on release", () => {
    const { navigate, link } = mountNav(0);
    pointer(link(2), "pointerdown", middle(2));
    vi.advanceTimersByTime(200);
    pointer(link(2), "pointerup", middle(2), "mouse", 200);
    expect(navigate).toHaveBeenCalledWith("/staff");
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    link(2).dispatchEvent(click);
    expect(click.defaultPrevented).toBe(true);
  });
});
