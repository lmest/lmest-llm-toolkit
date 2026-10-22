#!/usr/bin/env node
"use strict";

/* Render every .lmest-slide at 1920 × 1080 for visual QA. Requires Playwright. */
const fs = require("node:fs/promises");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

async function main() {
  const [, , inputArg, outputArg] = process.argv;
  if (!inputArg || !outputArg) {
    console.error("Usage: render_html_deck.cjs presentation/index.html output_render_dir");
    process.exitCode = 2;
    return;
  }
  const input = path.resolve(inputArg);
  const output = path.resolve(outputArg);
  await fs.access(input);
  await fs.mkdir(output, { recursive: true });
  for (const name of await fs.readdir(output)) {
    if (/^slide-\d{3}\.png$/.test(name)) await fs.rm(path.join(output, name));
  }

  let browser;
  try {
    const launchOptions = { headless: true };
    if (process.env.LMEST_CHROMIUM) launchOptions.executablePath = process.env.LMEST_CHROMIUM;
    browser = await chromium.launch(launchOptions);
  } catch (error) {
    throw new Error(`Playwright não conseguiu iniciar o Chromium. Use um runtime com navegador aprovado e instalado. Detalhe: ${error.message}`);
  }
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  try {
    const url = new URL(pathToFileURL(input).href);
    url.searchParams.set("slide", "1");
    await page.goto(url.href, { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    const slideCount = await page.locator(".lmest-slide").count();
    if (!slideCount) throw new Error("Nenhum elemento .lmest-slide foi encontrado.");
    const hasRuntime = await page.evaluate(() => Boolean(window.LMEstDeck && window.LMEstDeck.count));
    if (!hasRuntime) throw new Error("O runtime LMEst não carregou; confira o script lmest_presentation.js.");

    const brokenImages = await page.locator(".lmest-slide img").evaluateAll((images) => images
      .filter((image) => image.src && (!image.complete || image.naturalWidth === 0))
      .map((image) => image.getAttribute("src")));
    if (brokenImages.length) throw new Error(`Imagens ausentes ou inválidas: ${brokenImages.join(", ")}`);

    await page.addStyleTag({ content: "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}" });
    const stage = page.locator("#lmest-stage");
    for (let index = 1; index <= slideCount; index += 1) {
      await page.evaluate((number) => window.LMEstDeck.go(number), index);
      const file = path.join(output, `slide-${String(index).padStart(3, "0")}.png`);
      await stage.screenshot({ path: file, animations: "disabled" });
      console.log(file);
    }
    if (pageErrors.length) throw new Error(`Erros JavaScript: ${pageErrors.join(" | ")}`);
    console.log(`Renderizados ${slideCount} slides em 1920 × 1080.`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => { console.error(error.stack || String(error)); process.exitCode = 1; });
