export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

const SELF_HANDLED_401 = new Set(["/auth/me", "/auth/login"]);
let unauthorizedHandler: (() => void) | null = null;

export function onUnauthorized(handler: () => void): void {
  unauthorizedHandler = handler;
}

const NETWORK_ERROR = "Нет связи с сервером. Проверьте подключение и попробуйте ещё раз";
const UNKNOWN_ERROR = "Что-то пошло не так. Попробуйте ещё раз";
const INVALID_INPUT = "Проверьте заполненные поля: какое-то значение указано неверно";

async function readDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (Array.isArray(body.detail)) {
      return INVALID_INPUT;
    }
    return typeof body.detail === "string" ? body.detail : UNKNOWN_ERROR;
  } catch {
    return UNKNOWN_ERROR;
  }
}

export async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const json = body === undefined ? {} : { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  return send<T>(method, path, json);
}

export async function upload<T>(path: string, form: FormData): Promise<T> {
  return send<T>("POST", path, { body: form });
}

async function send<T>(method: string, path: string, init: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, { method, credentials: "same-origin", cache: "no-store", ...init });
  } catch {
    throw new ApiError(0, NETWORK_ERROR);
  }
  if (!response.ok) {
    if (response.status === 401 && !SELF_HANDLED_401.has(path)) {
      unauthorizedHandler?.();
    }
    throw new ApiError(response.status, await readDetail(response));
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

export function errorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}
