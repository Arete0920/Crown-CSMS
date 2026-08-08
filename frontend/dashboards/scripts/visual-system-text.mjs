export function maskCssCommentsPreservingLayout(text) {
  const output = text.split('');
  let quote = null;
  let escaped = false;
  let index = 0;

  while (index < text.length) {
    const char = text[index];
    const next = text[index + 1];

    if (quote) {
      if (escaped) {
        escaped = false;
      } else if (char === '\\') {
        escaped = true;
      } else if (char === quote) {
        quote = null;
      }
      index += 1;
      continue;
    }

    if (char === '"' || char === "'") {
      quote = char;
      index += 1;
      continue;
    }

    if (char === '/' && next === '*') {
      let cursor = index;
      let closed = false;

      while (cursor < text.length) {
        const current = text[cursor];
        const following = text[cursor + 1];
        if (current !== '\n') output[cursor] = ' ';

        if (current === '*' && following === '/') {
          output[cursor + 1] = ' ';
          cursor += 2;
          closed = true;
          break;
        }
        cursor += 1;
      }

      index = closed ? cursor : text.length;
      continue;
    }

    index += 1;
  }

  return output.join('');
}
