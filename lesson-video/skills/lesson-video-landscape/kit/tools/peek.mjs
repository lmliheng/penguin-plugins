#!/usr/bin/env node
/**
 * 抽帧看一眼：不跑整条渲染，只在指定的秒数上截几张图，用来快速目视检查版式。
 *
 * 用法:
 *   PLAYWRIGHT_MODULE=<pw-core> CHROME_PATH=<chrome> \
 *   node tools/peek.mjs --dir lessons/ep02-window --at 8,40,120 --out .peek
 */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const LIB = path.join(HERE, '..', 'lib');
const pw = require(process.env.PLAYWRIGHT_MODULE || 'playwright-core');

const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };

const dir = path.resolve(arg('--dir', '.'));
const outDir = path.resolve(arg('--out', '.peek'));
const at = arg('--at', '').split(',').filter(Boolean).map(Number);
const lesson = JSON.parse(fs.readFileSync(path.join(dir, 'lesson.json'), 'utf8'));
const [W, H] = (lesson.meta?.size || '1080x1920').split('x').map(Number);
const defaultAt = lesson.scenes.map((s) => +(s.start + s.dur * 0.55).toFixed(1));
const times = at.length ? at : defaultAt;

fs.mkdirSync(outDir, { recursive: true });
const browser = await pw.chromium.launch({
  executablePath: process.env.CHROME_PATH || undefined,
  args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars', '--force-color-profile=srgb'],
});
const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const page = await ctx.newPage();
await page.addInitScript(`window.__LESSON__ = ${JSON.stringify(lesson)};`);
const localDeck = path.join(dir, 'deck.html');
const namedDeck = lesson.meta && lesson.meta.deck ? path.join(LIB, lesson.meta.deck) : null;
const deck = fs.existsSync(localDeck) ? localDeck
  : (namedDeck && fs.existsSync(namedDeck)) ? namedDeck
  : path.join(LIB, 'deck.html');
await page.goto(pathToFileURL(deck).href, { waitUntil: 'load' });
await page.evaluate(() => window.__init(window.__LESSON__));
await page.evaluate(() => document.fonts.ready);

for (const t of times) {
  await page.evaluate((tt) => window.seek(tt), t);
  const file = path.join(outDir, `t${String(t).replace('.', '_')}.jpg`);
  await page.screenshot({ path: file, type: 'jpeg', quality: 92 });
  console.log(`OK ${file}`);
}
await browser.close();
