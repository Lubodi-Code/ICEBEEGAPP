const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });
  await page.goto('http://localhost:5173/#/e/test2', { waitUntil: 'networkidle2', timeout: 30000 });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: 'shot_top.png' });
  await page.evaluate(() => window.scrollTo(0, 700));
  await new Promise(r => setTimeout(r, 600));
  await page.screenshot({ path: 'shot_scrolled.png' });
  await browser.close();
  console.log('done');
})().catch(e => { console.error(e); process.exit(1); });
