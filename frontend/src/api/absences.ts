import { request } from "./http";

export type AbsenceKind = "vacation" | "sick" | "other";

export interface AbsenceForm {
  first: string;
  last: string;
  kind: AbsenceKind;
  note: string;
}

export interface Absence extends AbsenceForm {
  id: number;
  person_id: number;
  name: string;
  login: string;
}

export const fetchAbsences = (from: string, to: string) => request<Absence[]>("GET", `/absences?date_from=${from}&date_to=${to}`);
export const addAbsence = (form: AbsenceForm & { account_id: number }) => request<Absence>("POST", "/absences", form);
export const changeAbsence = (id: number, form: AbsenceForm) => request<Absence>("PUT", `/absences/${id}`, form);
export const removeAbsence = (id: number) => request<void>("DELETE", `/absences/${id}`);
