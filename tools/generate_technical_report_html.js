#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { marked } = require("marked");

const root = path.resolve(__dirname, "..");
const source = path.join(root, "docs", "SuperAI6_IoT_Attack_Detection_Report_TH.md");
const output = path.join(root, "docs", "SuperAI6_IoT_Attack_Detection_Report_TH.html");
const markdown = fs.readFileSync(source, "utf8");
const lines = markdown.split(/\r?\n/);
const start = lines.findIndex((line) => line.startsWith("# 1."));
if (start < 0) throw new Error("Report body start not found");

const toc = lines
  .filter((line) => /^# (?!รายงาน)/.test(line))
  .map((line) => line.slice(2).trim());

marked.setOptions({ gfm: true, breaks: false });
const body = marked.parse(lines.slice(start).join("\n"));
const hero = "assets/design_report_hero.png";

const html = `<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The IoT Attack Detection Challenge — Technical Report</title>
<style>
  :root { --navy:#081522; --navy2:#10263a; --cyan:#0e8f87; --lime:#9bd72d; --orange:#ff8a4c; --text:#17212b; --muted:#5f707c; --line:#d5e1e5; --light:#f2f6f7; }
  @page { size:A4; margin:17mm 16mm 18mm; }
  * { box-sizing:border-box; }
  html,body { margin:0; padding:0; color:var(--text); font-family:Tahoma,"Arial Unicode MS",sans-serif; font-size:10pt; line-height:1.55; }
  body { print-color-adjust:exact; -webkit-print-color-adjust:exact; }
  .cover { page-break-after:always; min-height:260mm; display:flex; flex-direction:column; justify-content:flex-end; }
  .hero { width:100%; height:145mm; object-fit:cover; margin-bottom:16mm; }
  .eyebrow { color:var(--cyan); font-size:9pt; font-weight:700; letter-spacing:.11em; text-transform:uppercase; }
  .cover h1 { page-break-before:auto; font-size:30pt; line-height:1.05; margin:4mm 0 5mm; color:#000; }
  .subtitle { max-width:130mm; color:var(--muted); font-size:13pt; line-height:1.35; }
  .meta { display:flex; justify-content:space-between; margin-top:12mm; color:var(--muted); font-size:9.5pt; }
  .score-row { display:grid; grid-template-columns:1fr 1fr; gap:5mm; margin-top:10mm; }
  .score { background:var(--navy2); color:white; padding:5mm; border-left:2mm solid var(--cyan); }
  .score:last-child { border-color:var(--lime); }
  .score small { color:#a9bdc7; display:block; font-weight:700; letter-spacing:.06em; }
  .score strong { display:block; font-size:22pt; color:#2dd4bf; line-height:1.1; margin-top:2mm; }
  .score:last-child strong { color:#b7f34a; }
  .toc { page-break-after:always; }
  .toc h1 { page-break-before:auto; }
  .toc ol { columns:2; column-gap:14mm; padding-left:6mm; }
  .toc li { break-inside:avoid; margin:0 0 2.5mm; color:var(--muted); }
  main h1 { page-break-before:always; font-size:22pt; line-height:1.15; margin:0 0 7mm; color:#000; border-top:1.5mm solid var(--cyan); padding-top:4mm; }
  main h1:first-child { page-break-before:auto; }
  h2 { font-size:15pt; line-height:1.25; margin:8mm 0 3mm; color:var(--cyan); break-after:avoid; }
  h3 { font-size:11.5pt; margin:6mm 0 2mm; color:var(--navy2); break-after:avoid; }
  p { margin:0 0 3.2mm; orphans:3; widows:3; text-align:justify; }
  ul,ol { margin:2mm 0 4mm 6mm; padding-left:5mm; }
  li { margin-bottom:1.5mm; }
  table { width:100%; border-collapse:collapse; margin:4mm 0 6mm; font-size:8.6pt; break-inside:avoid; }
  th { background:#000; color:white; text-align:left; padding:2.8mm; }
  td { padding:2.5mm; border:1px solid var(--line); vertical-align:top; }
  tbody tr:nth-child(even) td { background:var(--light); }
  blockquote { margin:5mm 0; padding:4mm 5mm; border-left:2mm solid var(--cyan); background:#e9f7f5; color:#075e59; font-weight:700; }
  pre { margin:4mm 0 6mm; padding:4mm; background:var(--navy2); color:#e8f2f5; border-radius:2mm; white-space:pre-wrap; font-size:8.2pt; break-inside:avoid; }
  code { font-family:"Courier New",monospace; color:#087f79; }
  pre code { color:inherit; }
  strong { color:#000; }
  .source-note { margin-top:12mm; padding-top:4mm; border-top:1px solid var(--line); color:var(--muted); font-size:8pt; }
</style>
</head>
<body>
<section class="cover">
  <img class="hero" src="${hero}" alt="IoT network visual">
  <div class="eyebrow">Super AI Engineer Season 6 / Design & Technical Report</div>
  <h1>The IoT Attack Detection Challenge</h1>
  <div class="subtitle">การตรวจจับการโจมตีบนเครือข่าย IoT ด้วย Protocol Rules, Stream Structure และ PCAP Evidence</div>
  <div class="score-row"><div class="score"><small>PUBLIC F1</small><strong>0.96267</strong></div><div class="score"><small>PRIVATE F1</small><strong>0.97198</strong></div></div>
  <div class="meta"><span>610686-วชิรวิทย์</span><span>กรกฎาคม 2569</span></div>
</section>
<section class="toc"><h1>สารบัญ</h1><ol>${toc.map((item) => `<li>${item}</li>`).join("")}</ol></section>
<main>${body}<p class="source-note">อ้างอิง: เอกสารโจทย์ SuperAI6, Kaggle submission history และ artifacts ใน repository</p></main>
</body>
</html>`;

fs.writeFileSync(output, html, "utf8");
console.log(`output=${output}`);

