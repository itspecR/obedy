import { request } from "./http";

export type Role = "employee" | "hr" | "admin";
export type Source = "local" | "domain";

export interface Me {
  login: string;
  display_name: string;
  role: Role;
  source: Source;
  must_change_password: boolean;
  weak_password: boolean;
}

export interface Credentials {
  login: string;
  password: string;
}

export const fetchMe = () => request<Me>("GET", "/auth/me");
export const login = (credentials: Credentials) => request<Me>("POST", "/auth/login", credentials);
export const logout = () => request<void>("POST", "/auth/logout");
export const changePassword = (new_password: string, current_password?: string) =>
  request<Me>("POST", "/auth/change-password", current_password === undefined ? { new_password } : { new_password, current_password });
