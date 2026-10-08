import type { Role } from "../../api/auth";
import type { StaffMember, StaffStatus } from "../../api/staff";
import { ROLE_LABELS } from "../../roles";
import type { Tone } from "../ui/tone";

export type RoleFilter = Role | "all";
export type StatusFilter = StaffStatus | "all";

export interface StaffFilter {
  query: string;
  role: RoleFilter;
  status: StatusFilter;
}

export const EMPTY_FILTER: StaffFilter = { query: "", role: "all", status: "all" };

export const STATUS_LABELS: Record<StaffStatus, string> = {
  active: "Активен",
  blocked: "Заблокирован",
  gone: "Нет в домене",
};

export const STATUS_TONES: Record<StaffStatus, Tone> = {
  active: "ok",
  blocked: "alarm",
  gone: "neutral",
};

export const ROLE_OPTIONS: { value: RoleFilter; label: string }[] = [
  { value: "all", label: "Все" },
  ...(Object.entries(ROLE_LABELS) as [Role, string][]).map(([value, label]) => ({ value, label })),
];

export const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "Все" },
  { value: "active", label: "Активные" },
  { value: "blocked", label: "Заблокированные" },
  { value: "gone", label: "Нет в домене" },
];

export function displayName(member: StaffMember): string {
  return member.full_name || member.login;
}

function normalize(text: string): string {
  return text.toLowerCase().replaceAll("ё", "е");
}

function searchable(member: StaffMember): string {
  return normalize([member.full_name, member.login, member.department, member.position].join(" "));
}

export function matches(member: StaffMember, filter: StaffFilter): boolean {
  const words = normalize(filter.query).split(/\s+/).filter(Boolean);
  const text = searchable(member);
  return (
    (filter.role === "all" || member.role === filter.role) &&
    (filter.status === "all" || member.status === filter.status) &&
    words.every((word) => text.includes(word))
  );
}

export function filterStaff(members: StaffMember[], filter: StaffFilter): StaffMember[] {
  return members.filter((member) => matches(member, filter));
}
