const AUTOFILL_SELECTORS = [":autofill", ":-webkit-autofill"];

function matchesSafely(element: HTMLElement, selector: string): boolean {
  try {
    return element.matches(selector);
  } catch {
    return false;
  }
}

export function isAutofilled(element: HTMLElement | null): boolean {
  return element !== null && AUTOFILL_SELECTORS.some((selector) => matchesSafely(element, selector));
}
