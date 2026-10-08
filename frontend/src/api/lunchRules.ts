import { request } from "./http";

export interface RulesForm {
  limit_minutes: number;
  workdays: string;
  day_end: string;
  window_enabled: boolean;
  window_start: string;
  window_end: string;
}

export interface LunchRules extends RulesForm {
  updated_at: string;
  min_limit_minutes: number;
  max_limit_minutes: number;
}

export const fetchLunchRules = () => request<LunchRules>("GET", "/lunch/rules");
export const saveLunchRules = (form: RulesForm) => request<LunchRules>("PUT", "/lunch/rules", form);
