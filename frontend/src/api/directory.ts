import { request } from "./http";

export type DirectoryMode = "ldaps" | "starttls" | "plain";

export interface DirectorySettings {
  enabled: boolean;
  servers: string;
  mode: DirectoryMode;
  port: number | null;
  ca_certificate: string;
  bind_user: string;
  has_bind_password: boolean;
  base_dn: string;
  group_dn: string;
  session_days: number;
}

export interface DirectoryForm extends Omit<DirectorySettings, "has_bind_password"> {
  bind_password: string;
}

export interface CheckResult {
  ok: boolean;
  message: string;
}

export const fetchDirectory = () => request<DirectorySettings>("GET", "/directory");
export const saveDirectory = (form: DirectoryForm) => request<DirectorySettings>("PUT", "/directory", form);
export const checkDirectory = () => request<CheckResult>("POST", "/directory/check");
export const fetchDirectoryStatus = () => request<{ enabled: boolean }>("GET", "/directory/public");

export type SyncStatus = "done" | "skipped" | "guarded" | "failed";

export interface SyncReport {
  finished_at: string | null;
  status: SyncStatus | null;
  message: string;
  created: number;
  updated: number;
  deactivated: number;
  skipped: number;
}

export const fetchSyncReport = () => request<SyncReport>("GET", "/directory/sync");
export const runSync = () => request<SyncReport>("POST", "/directory/sync");
