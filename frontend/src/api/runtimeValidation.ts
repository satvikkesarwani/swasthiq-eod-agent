function assertSafeIntegers(value: unknown, path = "$"): void {
  if (typeof value === "number" && Number.isInteger(value) && !Number.isSafeInteger(value)) {
    throw new Error(`Unsafe integer in API response at ${path}.`);
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => assertSafeIntegers(item, `${path}[${index}]`));
    return;
  }
  if (typeof value === "object" && value !== null) {
    for (const [key, nested] of Object.entries(value)) {
      assertSafeIntegers(nested, `${path}.${key}`);
    }
  }
}

export function validateApiPayload<T>(payload: T): T {
  assertSafeIntegers(payload);
  return payload;
}
