import { chromium } from "playwright";

const BASE = process.env.BASE_URL || process.env.SCREENSHOT_BASE || "http://127.0.0.1:8080";
const OUT = "docs/screenshots";

const PAGES = [
  { name: "portal", path: "/", waitFor: ".ai" },
];

const FORBIDDEN = [
  { label: "private IPv4", re: /\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b/ },
  { label: "tailnet IPv4", re: /\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b/ },
  { label: "email address", re: /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i },
  ...(process.env.SCRUB_PATTERNS || "").split(",").map(p => p.trim()).filter(Boolean).map(p => ({ label: `custom:${p}`, re: new RegExp(p, "i") })),
];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });

for (const pg of PAGES) {
  await page.goto(new URL(pg.path, BASE).toString(), { waitUntil: "networkidle" });
  if (pg.waitFor) await page.waitForSelector(pg.waitFor, { timeout: 20000 });
  await page.waitForTimeout(1200);
  const path = `${OUT}/${pg.name}.png`;
  await page.screenshot({ path, fullPage: true });
  const content = await page.content();
  for (const f of FORBIDDEN) {
    if (f.re.test(content)) { console.error(`SCRUB-GUARD: ${f.label} leaked onto ${pg.name}`); process.exit(1); }
  }
  console.log(`saved ${path}`);
}

await browser.close();
