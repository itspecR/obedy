import type { Role, Source } from "./auth";
import { request } from "./http";

export type StaffStatus = "active" | "blocked" | "gone";

export interface StaffMember {
  id: number;
  login: string;
  full_name: string;
  department: string;
  position: string;
  role: Role;
  source: Source;
  status: StaffStatus;
  track_lunch: boolean;
  can_track_lunch: boolean;
  last_login_at: string | null;
}

export const fetchStaff = () => request<StaffMember[]>("GET", "/staff");

export const changeRole = (id: number, role: Role) => request<StaffMember>("PUT", `/staff/${id}/role`, { role });
export const setTrackLunch = (id: number, track_lunch: boolean) => request<StaffMember>("PUT", `/staff/${id}/track-lunch`, { track_lunch });
export const setBlocked = (id: number, blocked: boolean) => request<StaffMember>("PUT", `/staff/${id}/blocked`, { blocked });

export interface Profile {
  full_name: string;
  department: string;
  position: string;
}

export interface LocalAccountForm extends Profile {
  login: string;
  role: Role;
}

export interface Issued {
  member: StaffMember;
  temporary_password: string;
}

export const createLocalAccount = (form: LocalAccountForm) => request<Issued>("POST", "/staff", form);
export const updateProfile = (id: number, profile: Profile) => request<StaffMember>("PUT", `/staff/${id}/profile`, profile);
export const resetPassword = (id: number) => request<Issued>("POST", `/staff/${id}/password`);
