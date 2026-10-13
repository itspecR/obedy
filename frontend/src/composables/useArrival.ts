let arriving = false;

export function markArrival(): void {
  arriving = true;
}

export function takeArrival(): boolean {
  const arrived = arriving;
  arriving = false;
  return arrived;
}
