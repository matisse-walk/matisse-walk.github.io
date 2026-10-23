// Render print.html to booklet/matisse-montparnasse.pdf (A5 landscape, from the page's own @page size).
// Usage: python -m http.server 8765   (in the repo root), then   node tools/render_booklet.js [port]
const { chromium } = require('playwright');
const path = require('path');
const port = process.argv[2] || '8765';
const out = path.join(__dirname, '..', 'booklet', 'matisse-montparnasse.pdf');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  const errors = []; p.on('pageerror', e => errors.push(e.message));
  await p.goto(`http://127.0.0.1:${port}/print.html?` + Date.now(), { waitUntil: 'networkidle', timeout: 120000 });
  await p.waitForFunction(() => document.body.dataset.ready === '1', { timeout: 60000 });
  await p.waitForTimeout(1500);
  await p.emulateMedia({ media: 'print' });
  await p.pdf({ path: out, preferCSSPageSize: true, printBackground: true });
  console.log('pages', await p.$$eval('.page', e => e.length), 'errors', JSON.stringify(errors));
  await b.close();
})().catch(e => { console.log('FAILED', e.message); process.exit(1); });
