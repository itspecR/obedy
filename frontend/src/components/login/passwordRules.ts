export const MIN_LENGTH = 10;
export const MAX_LENGTH = 128;

export interface PasswordRule {
  key: "length" | "digits" | "login" | "match";
  text: string;
  error: string;
  met: boolean;
}

export function passwordRules(next: string, repeat: string, login: string): PasswordRule[] {
  const lowered = next.toLowerCase();
  const ownLogin = login.trim().toLowerCase();
  return [
    {
      key: "length",
      text: `От ${MIN_LENGTH} до ${MAX_LENGTH} символов`,
      error: `Пароль должен быть от ${MIN_LENGTH} до ${MAX_LENGTH} символов`,
      met: next.length >= MIN_LENGTH && next.length <= MAX_LENGTH,
    },
    {
      key: "digits",
      text: "Не только цифры",
      error: "Пароль не может состоять только из цифр",
      met: next.length > 0 && !/^\d+$/.test(next),
    },
    {
      key: "login",
      text: "Не содержит логин",
      error: "Пароль не должен содержать логин",
      met: next.length > 0 && (ownLogin.length < 4 || !lowered.includes(ownLogin)),
    },
    { key: "match", text: "Пароли совпадают", error: "Пароли не совпадают", met: next.length > 0 && next === repeat },
  ];
}

export function firstProblem(rules: PasswordRule[]): string {
  return rules.find((rule) => !rule.met)?.error ?? "";
}
