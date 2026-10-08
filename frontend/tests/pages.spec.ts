import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ChangePasswordPage from "../src/pages/ChangePasswordPage.vue";
import LunchPage from "../src/pages/LunchPage.vue";
import { useSession } from "../src/stores/session";
import { me } from "./people";

vi.mock("vue-router", () => ({ useRouter: () => ({ replace: vi.fn() }) }));

function changePageFor(weak: boolean) {
  useSession().me = me("admin", { must_change_password: true, weak_password: weak });
  return mount(ChangePasswordPage);
}

describe("ChangePasswordPage", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("does not ask the temporary password again", () => {
    expect(changePageFor(false).findAll("input")).toHaveLength(2);
  });

  it("asks the current password when it was found too weak", () => {
    expect(changePageFor(true).findAll("input")).toHaveLength(3);
  });
});

describe("LunchPage", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("greets the user and explains the empty state", () => {
    useSession().me = me("employee");
    const wrapper = mount(LunchPage);

    expect(wrapper.text()).toContain("Здравствуйте, Петрова Анна");
    expect(wrapper.text()).toContain("Отметка обеда пока не включена");
  });
});
