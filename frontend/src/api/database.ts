import { request } from "./http";
import type { ConnectionForm, ProbeResult } from "./setup";

export type CurrentDatabase = Omit<ConnectionForm, "password">;

export const fetchDatabase = () => request<CurrentDatabase>("GET", "/database");
export const checkDatabaseChange = (form: ConnectionForm) => request<ProbeResult>("POST", "/database/check", form);
export const changeDatabase = (form: ConnectionForm) => request<ProbeResult>("PUT", "/database", form);
