import type { Absence, AbsenceForm, AbsenceKind } from "../../api/absences";
import { firstOfMonth, monthOf, shiftDay, shiftMonth } from "../../format/calendar";
import { formatFullDay } from "../../format/dateTime";
import type { Period } from "../stats/period";

export const NOTE_LIMIT = 200;

export const KIND_LABELS: Record<AbsenceKind, string> = {
  vacation: "Отпуск",
  sick: "Больничный",
  other: "Другое",
};

export const KIND_OPTIONS = (Object.keys(KIND_LABELS) as AbsenceKind[]).map((value) => ({ value, label: KIND_LABELS[value] }));

export function wholeMonth(today: string): Period {
  const month = monthOf(today);
  return { from: firstOfMonth(month), to: shiftDay(firstOfMonth(shiftMonth(month, 1)), -1) };
}

export function rangeText(first: string, last: string): string {
  return first === last ? formatFullDay(first) : `${formatFullDay(first)} — ${formatFullDay(last)}`;
}

export function blankForm(day: string): AbsenceForm {
  return { first: day, last: day, kind: "vacation", note: "" };
}

export function formOf(absence: Absence): AbsenceForm {
  return { first: absence.first, last: absence.last, kind: absence.kind, note: absence.note };
}

export function formProblem(form: AbsenceForm): string {
  if (!form.first || !form.last) {
    return "Укажите даты «с» и «по»";
  }
  return form.last < form.first ? "Дата «по» не может быть раньше даты «с»" : "";
}
