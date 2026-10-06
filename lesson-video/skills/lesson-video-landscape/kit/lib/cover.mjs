#!/usr/bin/env node
/**
 * 把 covers/covers.json 渲染成抖音封面图：9:16（1080×1920，视频首图）与 3:4（1080×1440，主页封面）。
 *
 * 用法:
 *   PLAYWRIGHT_MODULE=<pw-core 路径> CHROME_PATH=<chrome.exe> \
 *   node lib/cover.mjs --data covers/covers.json --out covers/out [--sizes 1920,1440]
 */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const pw = require(process.env.PLAYWRIGHT_MODULE || 'playwright-core');
const CHROME = process.env.CHROME_PATH || '';

const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };

const dataFile = path.resolve(arg('--data', 'covers/covers.json'));
const outDir = path.resolve(arg('--out', 'covers/out'));
// 默认用深色封面模板；浅色演示版用 --template cover-light.html
const template = arg('--template', 'cover.html');
// 横屏系列：1080 -> 1920x1080（视频首图），1440 -> 1080x1440（主页 3:4）
const PRESETS = {
  1080: { W: 1920, H: 1080, cls: '16x9', name: '16x9' },
  1440: { W: 1080, H: 1440, cls: 'p34', name: '1080x1440' },
};
const sizes = arg('--sizes', '1080,1440').split(',')
  .map((s) => PRESETS[parseInt(s, 10)])
  .filter((p) => p !== undefined);
if (sizes.length === 0) throw new Error('--sizes 只认 1080（1920x1080）与 1440（1080x1440）');

const covers = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });

const browser = await pw.chromium.launch({
  executablePath: CHROME || undefined,
  args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars', '--force-color-profile=srgb'],
});

for (const c of covers) {
  for (const p of sizes) {
    const ctx = await browser.newContext({ viewport: { width: p.W, height: p.H }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    await page.addInitScript(`window.__COVER__ = ${JSON.stringify(c)};`);
    await page.goto(pathToFileURL(path.join(HERE, template)).href, { waitUntil: 'load' });
    await page.evaluate((s) => window.__init(window.__COVER__, s), p.cls);
    await page.evaluate(() => document.fonts.ready);
    const file = path.join(outDir, `${c.id}-${p.name}.png`);
    await page.screenshot({ path: file });
    await ctx.close();
    console.log(`OK ${file}  ${p.W}x${p.H}`);
  }
}

await browser.close();
