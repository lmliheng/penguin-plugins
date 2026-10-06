/** 版式探针：把某一幕的 DOM 状态打出来，用来查可视化幕型哪里没按预期渲染。
 * 用法: node tools/probe_dump.mjs --dir lessons/_probe --scene 4 --at 39
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
const idx = parseInt(arg('--scene', '1'), 10) - 1;
const at = parseFloat(arg('--at', '0'));
const lesson = JSON.parse(fs.readFileSync(path.join(dir, 'lesson.json'), 'utf8'));
const [W, H] = (lesson.meta?.size || '1080x1920').split('x').map(Number);

const browser = await pw.chromium.launch({ executablePath: process.env.CHROME_PATH || undefined,
  args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars'] });
const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const page = await ctx.newPage();
await page.addInitScript(`window.__LESSON__ = ${JSON.stringify(lesson)};`);
await page.goto(pathToFileURL(path.join(LIB, lesson.meta.deck || 'deck.html')).href, { waitUntil: 'load' });
await page.evaluate(() => window.__init(window.__LESSON__));
await page.evaluate(() => document.fonts.ready);
await page.evaluate((t) => window.seek(t), at);

const info = await page.evaluate((i) => {
  const sc = document.querySelectorAll('.scene')[i];
  const out = { type: window.__LESSON__.scenes[i].type, html: sc.innerHTML.slice(0, 400) };
  const box = sc.querySelector('.gridwrap, .stkwrap, .treewrap, .gwrap, .grwrap, .viz');
  if (box) out.box = { cls: box.className, h: box.clientHeight, w: box.clientWidth };
  const inner = sc.querySelector('table.grid, .stk');
  if (inner) out.inner = { h: Math.round(inner.getBoundingClientRect().height), transform: inner.style.transform };
  if (sc.querySelector('.gridwrap')) {
    out.rows = [...sc.querySelectorAll('tr')].map((tr) => ({
      cells: [...tr.querySelectorAll('td.gc')].map((td) => `${td.dataset.r},${td.dataset.c}=${JSON.stringify(td.textContent)}|${td.className}`),
    }));
  }
  if (sc.querySelector('.treewrap')) {
    out.tree = { nodes: sc.querySelectorAll('.tnode').length, hid: sc.querySelectorAll('.tnode.hid').length, edges: sc.querySelectorAll('.tedge').length };
  }
  if (sc.querySelector('.gwrap')) out.graph = { nodes: sc.querySelectorAll('.gnode').length, seen: sc.querySelectorAll('.gnode.seen').length, q: sc.querySelectorAll('.qbar .qi').length };
  if (sc.querySelector('.stkwrap')) out.stack = { frames: sc.querySelectorAll('.frame').length, on: sc.querySelectorAll('.frame.on').length, top: sc.querySelectorAll('.frame.top').length };
  const els = [...sc.querySelectorAll('*')].map((n) => n.getBoundingClientRect());
  out.bottom = Math.round(Math.max(...els.map((r) => r.bottom)));
  return out;
}, idx);

console.log(JSON.stringify(info, null, 1));
await browser.close();
