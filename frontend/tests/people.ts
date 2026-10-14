import type { Me, Role } from "../src/api/auth";

export function me(role: Role, overrides: Partial<Me> = {}): Me {
  return {
    login: "petrova.aa",
    display_name: "Петрова Анна Андреевна",
    role,
    source: "local",
    must_change_password: false,
    weak_password: false,
    ...overrides,
  };
}
