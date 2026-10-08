function normalize(text: string): string {
  return text.toLowerCase().replaceAll("ё", "е");
}

export function matchesQuery(query: string, fields: string[]): boolean {
  const text = normalize(fields.join(" "));
  return normalize(query)
    .split(/\s+/)
    .filter(Boolean)
    .every((word) => text.includes(word));
}
