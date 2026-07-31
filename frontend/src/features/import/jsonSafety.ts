export const MAX_JSON_DEPTH = 64;
export const MAX_JSON_NODES = 200_000;
export const MAX_SAFE_JSON_INTEGER = Number.MAX_SAFE_INTEGER;

type JsonSafetyOptions = {
  maxDepth?: number;
  maxNodes?: number;
};

function fail(message: string): never {
  throw new SyntaxError(message);
}

function lexicalDepth(text: string): number {
  let depth = 0;
  let maxDepth = 0;
  let inString = false;
  let escaped = false;
  for (const char of text) {
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (char === "\\") {
        escaped = true;
      } else if (char === "\"") {
        inString = false;
      }
      continue;
    }
    if (char === "\"") {
      inString = true;
    } else if (char === "{" || char === "[") {
      depth += 1;
      maxDepth = Math.max(maxDepth, depth);
    } else if (char === "}" || char === "]") {
      depth -= 1;
      if (depth < 0) {
        fail("JSON structure is malformed.");
      }
    }
  }
  return maxDepth;
}

function countNodes(value: unknown, maxNodes: number): void {
  const queue: unknown[] = [value];
  let count = 0;
  while (queue.length > 0) {
    const current = queue.shift();
    count += 1;
    if (count > maxNodes) {
      fail("JSON contains too many values.");
    }
    if (Array.isArray(current)) {
      for (const item of current as unknown[]) {
        queue.push(item);
      }
    } else if (typeof current === "object" && current !== null) {
      for (const item of Object.values(current)) {
        queue.push(item);
      }
    }
  }
}

function assertSafeJsonIntegers(value: unknown): void {
  const queue: unknown[] = [value];
  while (queue.length > 0) {
    const current = queue.shift();
    if (typeof current === "number" && Number.isInteger(current) && !Number.isSafeInteger(current)) {
      fail("JSON integer exceeds the safe range.");
    }
    if (Array.isArray(current)) {
      for (const item of current as unknown[]) {
        queue.push(item);
      }
    } else if (typeof current === "object" && current !== null) {
      for (const item of Object.values(current)) {
        queue.push(item);
      }
    }
  }
}

export function assertNoDuplicateJsonObjectKeys(text: string): void {
  const stack: Array<{ keys: Set<string>; container: "object" | "array"; expectingKey: boolean }> = [];
  let index = 0;
  let inString = false;
  let escaped = false;
  let tokenStart = -1;

  while (index < text.length) {
    const char = text[index];
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (char === "\\") {
        escaped = true;
      } else if (char === "\"") {
        inString = false;
        const top = stack[stack.length - 1];
        if (top?.container === "object" && top.expectingKey) {
          let cursor = index + 1;
          while (/\s/.test(text[cursor] ?? "")) {
            cursor += 1;
          }
          if (text[cursor] === ":") {
            const key = JSON.parse(text.slice(tokenStart, index + 1)) as string;
            if (top.keys.has(key)) {
              fail("JSON contains a duplicate object key.");
            }
            top.keys.add(key);
            top.expectingKey = false;
          }
        }
      }
      index += 1;
      continue;
    }

    if (char === "\"") {
      inString = true;
      escaped = false;
      tokenStart = index;
    } else if (char === "{") {
      stack.push({ keys: new Set(), container: "object", expectingKey: true });
    } else if (char === "[") {
      stack.push({ keys: new Set(), container: "array", expectingKey: false });
    } else if (char === "}") {
      stack.pop();
    } else if (char === "]") {
      stack.pop();
    } else if (char === ",") {
      const top = stack[stack.length - 1];
      if (top?.container === "object") {
        top.expectingKey = true;
      }
    }
    index += 1;
  }
}

export function parseStrictJson(text: string, options: JsonSafetyOptions = {}): unknown {
  const readableText = text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
  if (readableText.trim().length === 0) {
    fail("JSON text is empty.");
  }
  if (/\b(?:NaN|Infinity|-Infinity)\b/.test(readableText)) {
    fail("JSON cannot contain NaN or Infinity.");
  }
  if (lexicalDepth(readableText) > (options.maxDepth ?? MAX_JSON_DEPTH)) {
    fail("JSON structure is nested too deeply.");
  }
  assertNoDuplicateJsonObjectKeys(readableText);
  const parsed = JSON.parse(readableText) as unknown;
  countNodes(parsed, options.maxNodes ?? MAX_JSON_NODES);
  assertSafeJsonIntegers(parsed);
  return parsed;
}

export function stringifySafeJson(payload: unknown): string {
  assertSafeJsonIntegers(payload);
  return JSON.stringify(payload);
}
