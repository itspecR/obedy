import { mount } from "@vue/test-utils";
import { createPinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, nextTick, ref } from "vue";
import { isSoftwareRenderer, softwareRendering } from "../src/device/renderer";

const STORAGE_KEY = "obedy.light-mode";

function fakeGl(renderer: string): WebGLRenderingContext {
  const debug = { UNMASKED_RENDERER_WEBGL: 0x9246 };
  return {
    RENDERER: 0x1f01,
    getExtension: (name: string) => (name === "WEBGL_debug_renderer_info" ? debug : null),
    getParameter: () => renderer,
  } as unknown as WebGLRenderingContext;
}

function canvasReturns(value: WebGLRenderingContext | null): void {
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(value as never);
}

async function freshLightMode(weak: boolean) {
  vi.resetModules();
  vi.doMock("../src/device/renderer", () => ({ softwareRendering: () => weak, prefersLessTransparency: () => false }));
  const module = await import("../src/composables/useLightMode");
  module.initLightMode();
  await nextTick();
  return module;
}

function lightClass(): boolean {
  return document.documentElement.classList.contains("light-mode");
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.doUnmock("../src/device/renderer");
  localStorage.clear();
  document.documentElement.classList.remove("light-mode");
});

describe("renderer detection", () => {
  it("recognises software renderers by name", () => {
    expect(isSoftwareRenderer("ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero)), SwiftShader driver)")).toBe(true);
    expect(isSoftwareRenderer("ANGLE (Microsoft, Microsoft Basic Render Driver Direct3D11)")).toBe(true);
    expect(isSoftwareRenderer("llvmpipe (LLVM 15.0.7, 256 bits)")).toBe(true);
    expect(isSoftwareRenderer("ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11)")).toBe(false);
    expect(isSoftwareRenderer("ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11)")).toBe(false);
  });

  it("treats a browser without WebGL as a weak device", () => {
    canvasReturns(null);
    expect(softwareRendering()).toBe(true);
  });

  it("reads the renderer name from WebGL", () => {
    canvasReturns(fakeGl("ANGLE (Microsoft, Microsoft Basic Render Driver Direct3D11)"));
    expect(softwareRendering()).toBe(true);
    canvasReturns(fakeGl("ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11)"));
    expect(softwareRendering()).toBe(false);
  });

  it("treats a failing WebGL check as a weak device", () => {
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(softwareRendering()).toBe(true);
  });
});

describe("light mode", () => {
  it("turns on by itself on a weak device and can be switched off", async () => {
    const { useLightMode } = await freshLightMode(true);
    expect(lightClass()).toBe(true);
    useLightMode().choose("off");
    await nextTick();
    expect(lightClass()).toBe(false);
    expect(localStorage.getItem(STORAGE_KEY)).toBe("off");
  });

  it("stays off on a capable device until switched on", async () => {
    const { useLightMode } = await freshLightMode(false);
    expect(lightClass()).toBe(false);
    useLightMode().choose("on");
    await nextTick();
    expect(lightClass()).toBe(true);
  });

  it("remembers the choice between visits", async () => {
    localStorage.setItem(STORAGE_KEY, "on");
    const { useLightMode } = await freshLightMode(false);
    expect(useLightMode().preference.value).toBe("on");
    expect(lightClass()).toBe(true);
  });

  it("ignores an unknown stored value", async () => {
    localStorage.setItem(STORAGE_KEY, "maybe");
    const { useLightMode } = await freshLightMode(false);
    expect(useLightMode().preference.value).toBe("auto");
  });
});

describe("glass pill in light mode", () => {
  let frames: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    frames = vi.spyOn(window, "requestAnimationFrame");
  });

  it("jumps to the new item without frame-by-frame animation", async () => {
    await freshLightMode(true);
    const { useGlassPill } = await import("../src/composables/useGlassPill");
    let glass: ReturnType<typeof useGlassPill> | null = null;
    const Harness = defineComponent({
      setup() {
        const track = ref<HTMLElement | null>(null);
        glass = useGlassPill(track);
        return () => h("nav", { ref: track }, [h("a", { id: "first" }, "1"), h("a", { id: "second" }, "2")]);
      },
    });
    const wrapper = mount(Harness, { attachTo: document.body });
    const [first, second] = wrapper.findAll("a").map((link) => link.element as HTMLElement);
    glass!.place(first);
    glass!.place(second);
    expect(frames).not.toHaveBeenCalled();
    expect(glass!.pill.shown).toBe(true);
    wrapper.unmount();
  });
});

describe("light mode choice in the profile", () => {
  it("shows the current state and switches the mode", async () => {
    await freshLightMode(true);
    const { default: ProfileDialog } = await import("../src/components/shell/ProfileDialog.vue");
    const me = { id: 1, login: "ivanov", display_name: "Иванов Иван", role: "employee", source: "domain", must_change_password: false };
    const wrapper = mount(ProfileDialog, { props: { me: me as never }, global: { plugins: [createPinia()] } });
    expect(wrapper.text()).toContain("Сейчас включён: браузер рисует без видеокарты");
    await wrapper.findAll("[role=radio]").find((option) => option.text() === "Выключен")!.trigger("click");
    expect(lightClass()).toBe(false);
    expect(wrapper.text()).not.toContain("Сейчас включён");
    wrapper.unmount();
  });
});
