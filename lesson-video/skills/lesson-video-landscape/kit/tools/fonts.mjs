#!/usr/bin/env node
/**
 * 可靠地探测本机有哪些字体族：用「同一个字符串在不同 family 下的排版宽度」判断。
 * 拿一个肯定不存在的族名（__nope__）当对照组：宽度和对照组一样，说明这个族名没生效。
 */
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright-core');

const CANDIDATES = [
  'Noto Sans SC', 'Noto Serif SC', 'MiSans', 'Microsoft YaHei', 'Microsoft YaHei UI',
  'Segoe UI', 'Segoe UI Variable Display', 'Inter', 'HarmonyOS Sans SC', 'Alibaba PuHuiTi',
  'Source Han Sans SC', 'Source Han Sans', 'Cascadia Mono', 'JetBrains Mono', 'PingFang SC',
];

const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || undefined,
  args: ['--no-sandbox'],
});
const page = await browser.newPage();
await page.setContent('<html><body></body></html>');
const res = await page.evaluate(async (cands) => {
  await document.fonts.ready;
  const probe = (fam, weight) => {
    const s = document.createElement('span');
    s.style.cssText = `position:absolute;white-space:pre;font-size:64px;font-weight:${weight};`
      + `font-family:${fam === null ? '__nope__' : `"${fam}"`}, __nope__`;
    s.textContent = '滑动窗口 Ww 0123 il';
    document.body.appendChild(s);
    const w = s.getBoundingClientRect().width;
    s.remove();
    return w;
  };
  const base = { 400: probe(null, 400), 700: probe(null, 700) };
  const out = [`对照组(__nope__)  400:${base[400].toFixed(1)}  700:${base[700].toFixed(1)}`];
  for (const fam of cands) {
    const a = probe(fam, 400), b = probe(fam, 700);
    const ok400 = Math.abs(a - base[400]) > 0.5;
    const ok700 = Math.abs(b - base[700]) > 0.5;
    out.push(`${ok400 ? '有' : '无'}  ${fam.padEnd(28)} 400:${a.toFixed(1)}${ok400 ? '' : '(=控件)'}  700:${b.toFixed(1)}${ok700 ? '' : '(=控件)'}`);
  }
  return out;
}, CANDIDATES);
console.log(res.join('\n'));
await browser.close();
