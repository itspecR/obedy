import { request } from "./http";

export interface SetupStatus {
  configured: boolean;
  needs_admin: boolean;
}

export interface DatabaseForm {
  code: string;
  host: string;
  port: string;
  name: string;
  user: string;
  password: string;
  trust_certificate: boolean;
}

export interface ProbeResult {
  ok: boolean;
  message: string;
  has_data: boolean;
}

export interface FirstAdmin {
  login: string;
  password: string;
}

export const fetchSetupStatus = () => request<SetupStatus>("GET", "/setup/status");
export const checkDatabase = (form: DatabaseForm) => request<ProbeResult>("POST", "/setup/check", form);
export const saveDatabase = (form: DatabaseForm) => request<ProbeResult>("POST", "/setup/database", form);
export const createFirstAdmin = (code: string) => request<FirstAdmin>("POST", "/setup/admin", { code });
