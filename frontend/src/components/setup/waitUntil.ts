export const RESTART_POLL_MS = 2000;
export const RESTART_ATTEMPTS = 60;

const pause = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export async function waitUntil<T>(probe: () => Promise<T | null>): Promise<T> {
  for (let left = RESTART_ATTEMPTS; left > 0; left--) {
    await pause(RESTART_POLL_MS);
    const value = await probe().catch(() => null);
    if (value !== null) {
      return value;
    }
  }
  throw new Error("Сайт не перезапустился за 2 минуты. Проверьте сервер: sudo docker compose logs --tail=50 app");
}
