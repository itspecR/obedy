const stack: symbol[] = [];

export function enterModal(): symbol {
  const token = Symbol("modal");
  stack.push(token);
  return token;
}

export function leaveModal(token: symbol): void {
  const index = stack.indexOf(token);
  if (index >= 0) {
    stack.splice(index, 1);
  }
}

export function isTopModal(token: symbol): boolean {
  return stack[stack.length - 1] === token;
}
