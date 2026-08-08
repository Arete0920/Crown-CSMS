import { describe, expect, it } from 'vitest';
import { maskCssCommentsPreservingLayout } from '../../scripts/visual-system-text.mjs';

const COLOR = /#[0-9a-fA-F]{3,8}\b|\brgba?\([^)]*\)|\bhsla?\([^)]*\)/g;

function lineFor(text, index) {
  return text.slice(0, index).split('\n').length;
}

describe('visual-system CSS comment masking', () => {
  it('does not classify issue references in CSS comments as raw colors', () => {
    const source = [
      '/* canonical layout follow-up for issue #1913 */',
      '.card {',
      '  color: var(--crown-text);',
      '}',
    ].join('\n');

    const masked = maskCssCommentsPreservingLayout(source);

    expect([...masked.matchAll(COLOR)]).toEqual([]);
    expect(masked.length).toBe(source.length);
    expect(masked.split('\n')).toHaveLength(source.split('\n').length);
  });

  it('retains real CSS color literals and their original line numbers', () => {
    const source = [
      '/* issue #1913 should be ignored */',
      '.card {',
      '  color: #123abc;',
      '}',
    ].join('\n');

    const masked = maskCssCommentsPreservingLayout(source);
    const matches = [...masked.matchAll(COLOR)];

    expect(matches).toHaveLength(1);
    expect(matches[0][0]).toBe('#123abc');
    expect(lineFor(source, matches[0].index)).toBe(3);
  });

  it('also masks commented token and font declarations without changing offsets', () => {
    const tokenDeclaration = '--crown-' + 'fake: ' + '#' + 'abc;';
    const fontDeclaration = 'font-' + 'family: Comic Sans;';
    const source = `/* ${tokenDeclaration} ${fontDeclaration} */\n.card { display: block; }`;
    const masked = maskCssCommentsPreservingLayout(source);

    expect(masked).not.toContain('--crown-fake');
    expect(masked).not.toContain('Comic Sans');
    expect(masked.length).toBe(source.length);
  });

  it('preserves comment markers and visual literals inside quoted CSS strings', () => {
    const quotedColor = '#' + '123abc';
    const source = `.badge::before { content: "/* ${quotedColor} */"; }`;
    const masked = maskCssCommentsPreservingLayout(source);
    const matches = [...masked.matchAll(COLOR)];

    expect(masked).toBe(source);
    expect(matches).toHaveLength(1);
    expect(matches[0][0]).toBe(quotedColor);
  });

  it('preserves escaped quotes while deciding whether comment markers are real comments', () => {
    const marker = '/' + '* issue #1913 *' + '/';
    const source = `.badge::before { content: "quoted \\"${marker}\\" text"; }`;

    expect(maskCssCommentsPreservingLayout(source)).toBe(source);
  });
});
