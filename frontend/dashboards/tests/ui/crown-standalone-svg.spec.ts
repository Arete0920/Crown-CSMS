import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { expect, test } from '@playwright/test';

const baseURL = process.env.VITE_DEV_BASE_URL ?? 'http://localhost:4173';
const proofDir = join(process.cwd(), 'crown-svg-proof');
const variants = [
  { name: 'crown-logo-mark-square', background: '#ffffff' },
  { name: 'crown-logo-monochrome-royal', background: '#ffffff' },
  { name: 'crown-logo-monochrome-white', background: '#071e43' },
];

test.describe('CROWN standalone SVG image-context render proof', () => {
  for (const variant of variants) {
    test(`${variant.name} renders nonempty artwork as an HTML image`, async ({ page }) => {
      const assetURL = `${baseURL}/brand/crown/logo/${variant.name}.svg`;
      const response = await page.request.get(assetURL);
      expect(response.status()).toBe(200);
      expect(response.headers()['content-type']).toContain('image/svg+xml');

      await page.goto(`${baseURL}/build.json`, { waitUntil: 'domcontentloaded' });
      await page.setContent(`<!doctype html><html><body style="margin:0;padding:24px;background:${variant.background}"><img id="crown-logo" alt="CROWN approved brand variant" src="/brand/crown/logo/${variant.name}.svg" width="400" style="display:block;max-width:100%"></body></html>`);
      const image = page.locator('#crown-logo');
      await expect.poll(() => image.evaluate((el) => (el as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
      const opaquePixels = await image.evaluate((el) => {
        const img = el as HTMLImageElement;
        const canvas = document.createElement('canvas');
        canvas.width = 160;
        canvas.height = 160;
        const context = canvas.getContext('2d', { willReadFrequently: true });
        if (!context) throw new Error('Canvas 2D not available for image inspection');
        context.drawImage(img, 0, 0, 160, 160);
        const pixels = context.getImageData(0, 0, 160, 160).data;
        let visible = 0;
        for (let i = 3; i < pixels.length; i += 4) {
          if (pixels[i] > 32) visible++;
        }
        return visible;
      });
      expect(opaquePixels).toBeGreaterThan(100);
      mkdirSync(proofDir, { recursive: true });
      await page.screenshot({ path: join(proofDir, `${variant.name}.png`), fullPage: true });
    });
  }
});
