#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");
const sharp = require("sharp");

const ROOT = path.resolve(__dirname, "..");
const OUT_DIR = path.join(ROOT, "presentation");
const PPTX_PATH = path.join(OUT_DIR, "SuperAI6_IoT_Attack_Detection_Presentation_TH.pptx");
const NOTES_PATH = path.join(ROOT, "docs", "SuperAI6_Presentation_Speaker_Notes_TH.md");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "610686-วชิรวิทย์";
pptx.company = "Super AI Engineer Season 6";
pptx.subject = "The IoT Attack Detection Challenge";
pptx.title = "การตรวจจับการโจมตีบนเครือข่าย IoT";
pptx.lang = "th-TH";
pptx.theme = {
  headFontFace: "Tahoma",
  bodyFontFace: "Tahoma",
  lang: "th-TH",
};

const C = {
  navy: "081522",
  navy2: "10263A",
  navy3: "17344A",
  cyan: "2DD4BF",
  cyanDark: "0E8F87",
  lime: "B7F34A",
  orange: "FF8A4C",
  red: "FF5E68",
  white: "F8FCFD",
  light: "EEF5F6",
  panel: "DCE9EC",
  text: "17212B",
  muted: "657887",
  grid: "1D3A4C",
  gray: "A8BAC4",
};
const FONT = "Tahoma";
const W = 13.333;
const H = 7.5;
const notes = [];
const textSpecs = [];

function xmlEscape(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function charUnits(text) {
  let units = 0;
  for (const ch of text) {
    const code = ch.codePointAt(0);
    if ((code >= 0x0e31 && code <= 0x0e3a) || (code >= 0x0e47 && code <= 0x0e4e)) continue;
    if (ch === " ") units += 0.34;
    else if (/[MW@#%]/.test(ch)) units += 0.82;
    else if (/[A-Z0-9]/.test(ch)) units += 0.63;
    else if (/[.,:;|!]/.test(ch)) units += 0.3;
    else units += 0.56;
  }
  return units;
}

function breakToken(token, maxUnits) {
  const parts = [];
  let current = "";
  for (const ch of token) {
    if (current && charUnits(current + ch) > maxUnits) {
      parts.push(current);
      current = ch;
    } else {
      current += ch;
    }
  }
  if (current) parts.push(current);
  return parts;
}

function wrapText(text, maxUnits) {
  const output = [];
  for (const explicit of String(text).split("\n")) {
    if (!explicit) {
      output.push("");
      continue;
    }
    const tokens = explicit.split(/\s+/).flatMap((token) => charUnits(token) > maxUnits ? breakToken(token, maxUnits) : [token]);
    let line = "";
    for (const token of tokens) {
      const candidate = line ? `${line} ${token}` : token;
      if (line && charUnits(candidate) > maxUnits) {
        output.push(line);
        line = token;
      } else {
        line = candidate;
      }
    }
    output.push(line);
  }
  return output;
}

async function renderTextPng(spec) {
  const dpi = 180;
  const width = Math.max(4, Math.round(spec.w * dpi));
  const height = Math.max(4, Math.round(spec.h * dpi));
  const margin = Math.max(0, (spec.opts.margin ?? 0.05) * dpi);
  let fontPt = spec.opts.fontSize || 15;
  let lines = [];
  let fontPx = 0;
  let lineHeight = 0;
  for (let attempt = 0; attempt < 18; attempt += 1) {
    fontPx = fontPt * dpi / 72;
    const maxUnits = Math.max(1, (width - 2 * margin) / fontPx);
    lines = wrapText(spec.text, maxUnits);
    lineHeight = fontPx * 1.17;
    if (lines.length * lineHeight <= height - 2 * margin && lines.every((line) => charUnits(line) * fontPx <= width - 2 * margin + 2)) break;
    fontPt *= 0.92;
  }
  const totalHeight = lines.length * lineHeight;
  const valign = spec.opts.valign || "mid";
  let top = margin;
  if (valign === "mid") top = Math.max(margin, (height - totalHeight) / 2);
  if (valign === "bottom") top = Math.max(margin, height - margin - totalHeight);
  const align = spec.opts.align || "left";
  const x = align === "center" ? width / 2 : align === "right" ? width - margin : margin;
  const anchor = align === "center" ? "middle" : align === "right" ? "end" : "start";
  const weight = spec.opts.bold ? 700 : 400;
  const tspans = lines.map((line, index) =>
    `<tspan x="${x}" y="${top + fontPx * 0.88 + index * lineHeight}">${xmlEscape(line)}</tspan>`
  ).join("");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"><text text-anchor="${anchor}" font-family="Tahoma" font-size="${fontPx}" font-weight="${weight}" fill="#${spec.opts.color || C.text}">${tspans}</text></svg>`;
  return sharp(Buffer.from(svg)).png().toBuffer();
}

async function renderAllText() {
  const buffers = await Promise.all(textSpecs.map(renderTextPng));
  textSpecs.forEach((spec, index) => {
    spec.slide.addImage({
      data: `data:image/png;base64,${buffers[index].toString("base64")}`,
      x: spec.x, y: spec.y, w: spec.w, h: spec.h,
    });
  });
}

function addGrid(slide, dark = true) {
  const color = dark ? C.grid : "DCE8EB";
  for (let x = 0; x <= W; x += 0.67) {
    slide.addShape(pptx.ShapeType.line, { x, y: 0, w: 0, h: H, line: { color, transparency: dark ? 42 : 25, width: 0.35 } });
  }
  for (let y = 0; y <= H; y += 0.5) {
    slide.addShape(pptx.ShapeType.line, { x: 0, y, w: W, h: 0, line: { color, transparency: dark ? 42 : 25, width: 0.35 } });
  }
}

function addFooter(slide, page, dark = true) {
  const color = dark ? "A8C0CC" : C.muted;
  addText(slide, "SUPER AI ENGINEER SEASON 6  /  IoT ATTACK DETECTION", 0.48, 7.12, 5.8, 0.18, { fontSize: 7.5, bold: true, color, margin: 0 });
  addText(slide, String(page).padStart(2, "0"), 12.3, 7.06, 0.52, 0.25, { fontSize: 9, bold: true, color: dark ? C.cyan : C.cyanDark, align: "right", margin: 0 });
}

function baseSlide(title, kicker, { dark = true, page = 1 } = {}) {
  const slide = pptx.addSlide();
  slide.background = { color: dark ? C.navy : C.light };
  addGrid(slide, dark);
  slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: 0, w: 0.14, h: H, line: { color: C.cyan, transparency: 100 }, fill: { color: C.cyan },
  });
  addText(slide, kicker.toUpperCase(), 0.55, 0.34, 6.4, 0.25, { fontSize: 9, bold: true, color: dark ? C.cyan : C.cyanDark, margin: 0 });
  addText(slide, title, 0.52, 0.68, 12.1, 0.67, { fontSize: 26, bold: true, color: dark ? C.white : C.navy, margin: 0 });
  addFooter(slide, page, dark);
  return slide;
}

function addText(slide, text, x, y, w, h, opts = {}) {
  textSpecs.push({ slide, text: String(text), x, y, w, h, opts: { ...opts } });
}

function card(slide, x, y, w, h, { fill = C.navy2, line = C.navy3, radius = true } = {}) {
  slide.addShape(radius ? pptx.ShapeType.roundRect : pptx.ShapeType.rect, {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: fill }, line: { color: line, width: 1 },
    shadow: { type: "outer", color: "000000", opacity: 0.13, blur: 1, angle: 45, distance: 1 },
  });
}

function metric(slide, x, y, w, label, value, accent, sub = "", dark = true) {
  card(slide, x, y, w, 1.18, { fill: dark ? C.navy2 : "FFFFFF", line: dark ? C.navy3 : "D7E4E8" });
  slide.addShape(pptx.ShapeType.rect, { x, y, w: 0.08, h: 1.18, fill: { color: accent }, line: { color: accent, transparency: 100 } });
  addText(slide, label, x + 0.22, y + 0.12, w - 0.38, 0.23, { fontSize: 8.5, bold: true, color: dark ? C.gray : C.muted });
  addText(slide, value, x + 0.2, y + 0.37, w - 0.35, 0.48, { fontSize: 23, bold: true, color: accent });
  if (sub) addText(slide, sub, x + 0.22, y + 0.88, w - 0.38, 0.18, { fontSize: 8, color: dark ? C.gray : C.muted });
}

function chip(slide, text, x, y, w, color = C.cyan, dark = true) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h: 0.34, fill: { color, transparency: dark ? 82 : 72 }, line: { color, width: 1 },
  });
  addText(slide, text, x + 0.05, y + 0.03, w - 0.1, 0.27, { fontSize: 8.5, bold: true, color: dark ? C.white : C.navy, align: "center" });
}

function arrow(slide, x, y, w, color = C.cyan) {
  slide.addShape(pptx.ShapeType.chevron, { x, y, w, h: 0.34, fill: { color }, line: { color, transparency: 100 } });
}

function finalize(slide, title, note) {
  const full = `สไลด์: ${title}\n\n${note}`;
  slide.addNotes(full);
  notes.push({ title, note });
}

// 1 — Cover
{
  const slide = pptx.addSlide();
  slide.background = { color: C.navy };
  addGrid(slide, true);
  slide.addShape(pptx.ShapeType.rect, { x: 8.15, y: 0, w: 5.18, h: 7.5, fill: { color: C.navy2 }, line: { color: C.navy2 } });
  slide.addShape(pptx.ShapeType.chevron, { x: 8.15, y: 0, w: 2.1, h: 7.5, rotate: 180, fill: { color: C.navy3, transparency: 18 }, line: { color: C.navy3, transparency: 100 } });
  const nodes = [[9.2,1.2],[11.1,0.9],[12.25,2.2],[10.1,3.0],[12.0,4.2],[10.8,5.55],[9.0,6.0]];
  const edges = [[0,1],[1,2],[0,3],[3,2],[3,4],[3,5],[5,4],[5,6]];
  for (const [a,b] of edges) slide.addShape(pptx.ShapeType.line,{x:nodes[a][0],y:nodes[a][1],w:nodes[b][0]-nodes[a][0],h:nodes[b][1]-nodes[a][1],line:{color:C.cyan,width:2,transparency:15}});
  nodes.forEach((n,i)=>slide.addShape(pptx.ShapeType.ellipse,{x:n[0]-0.09,y:n[1]-0.09,w:0.18,h:0.18,fill:{color:i===2||i===5?C.lime:C.cyan},line:{color:C.white,width:0.5}}));
  addText(slide, "THE IoT ATTACK\nDETECTION CHALLENGE", 0.72, 1.05, 7.55, 1.6, { fontSize: 31, bold: true, color: C.white });
  addText(slide, "จาก Normal-only data สู่ detector ที่อธิบายได้", 0.75, 2.88, 6.9, 0.45, { fontSize: 18, color: C.cyan });
  addText(slide, "Protocol Rules  ×  Stream Structure  ×  PCAP Evidence", 0.75, 3.46, 6.65, 0.32, { fontSize: 12, bold: true, color: C.gray });
  metric(slide, 0.75, 4.28, 2.58, "PUBLIC F1", "0.96267", C.cyan, "best selected submission");
  metric(slide, 3.56, 4.28, 2.58, "PRIVATE F1", "0.97198", C.lime, "final leaderboard");
  addText(slide, "610686-วชิรวิทย์", 0.77, 6.15, 3.8, 0.32, { fontSize: 14, bold: true, color: C.white });
  addText(slide, "Super AI Engineer Season 6  /  19 กรกฎาคม 2569", 0.77, 6.54, 5.8, 0.24, { fontSize: 9, color: C.gray });
  finalize(slide, "เปิดเรื่อง", "โจทย์นี้มีข้อมูลฝึกเป็น Normal ทั้งหมด จึงไม่ใช่ classification แบบทั่วไป แนวทางของผมใช้ความหมายของ TCP และ MQTT สร้าง detector ที่อธิบายได้ แล้วตรวจสมมติฐานด้วย stream structure, PCAP และ controlled leaderboard experiments ผลสุดท้ายได้ Public 0.96267 และ Private 0.97198");
}

// 2 — Challenge setup
{
  const slide = baseSlide("โจทย์ยากตรงไหน?", "01 / problem framing", { dark: false, page: 2 });
  card(slide, 0.65, 1.55, 3.55, 3.8, { fill: "FFFFFF", line: "CADCE1" });
  addText(slide, "TRAIN", 0.93, 1.83, 1.0, 0.25, { fontSize: 10, bold: true, color: C.cyanDark });
  addText(slide, "100,000", 0.92, 2.22, 2.6, 0.6, { fontSize: 31, bold: true, color: C.navy });
  addText(slide, "records", 2.8, 2.46, 0.9, 0.22, { fontSize: 10, color: C.muted });
  slide.addShape(pptx.ShapeType.ellipse, { x: 1.2, y: 3.1, w: 2.45, h: 1.2, fill: { color: C.cyan, transparency: 12 }, line: { color: C.cyanDark, width: 1.5 } });
  addText(slide, "NORMAL เท่านั้น", 1.34, 3.47, 2.16, 0.35, { fontSize: 17, bold: true, color: C.navy, align: "center" });
  addText(slide, "ไม่มี Attack label ให้เรียนรู้", 0.93, 4.65, 2.9, 0.28, { fontSize: 11, color: C.red, bold: true });
  arrow(slide, 4.47, 3.1, 0.6, C.orange);
  card(slide, 5.25, 1.55, 3.55, 3.8, { fill: "FFFFFF", line: "CADCE1" });
  addText(slide, "TEST", 5.52, 1.83, 1.0, 0.25, { fontSize: 10, bold: true, color: C.orange });
  addText(slide, "10,000", 5.51, 2.22, 2.6, 0.6, { fontSize: 31, bold: true, color: C.navy });
  addText(slide, "records", 7.33, 2.46, 0.9, 0.22, { fontSize: 10, color: C.muted });
  slide.addShape(pptx.ShapeType.ellipse, { x: 5.78, y: 3.03, w: 1.18, h: 1.18, fill: { color: C.cyan, transparency: 12 }, line: { color: C.cyanDark, width: 1.2 } });
  slide.addShape(pptx.ShapeType.ellipse, { x: 6.65, y: 3.48, w: 1.38, h: 1.38, fill: { color: C.red, transparency: 8 }, line: { color: C.red, width: 1.2 } });
  addText(slide, "Normal", 5.85, 3.39, 1.0, 0.25, { fontSize: 11, bold: true, color: C.navy, align: "center" });
  addText(slide, "Attack", 6.82, 3.94, 1.0, 0.25, { fontSize: 11, bold: true, color: C.white, align: "center" });
  card(slide, 9.15, 1.55, 3.48, 3.8, { fill: C.navy, line: C.navy3 });
  addText(slide, "โจทย์จริง", 9.47, 1.87, 2.2, 0.3, { fontSize: 12, bold: true, color: C.cyan });
  addText(slide, "ONE-CLASS\nANOMALY DETECTION", 9.45, 2.36, 2.82, 1.0, { fontSize: 23, bold: true, color: C.white });
  addText(slide, "เป้าหมายไม่ใช่หา packet แปลกที่สุด\nแต่ต้องแยก rare-normal ออกจาก attack", 9.47, 3.67, 2.72, 0.78, { fontSize: 12, color: C.gray });
  metric(slide, 9.43, 4.58, 2.9, "BASELINE AUTOENCODER", "0.62303", C.orange, "Public F1 จากผู้จัด", true);
  chip(slide, "F1 = balance ของ Precision + Recall", 3.98, 5.85, 5.25, C.cyanDark, false);
  finalize(slide, "โจทย์ยากตรงไหน", "Train 100,000 แถวเป็น Normal ทั้งหมด ส่วน test 10,000 แถวมีทั้ง Normal และ Attack เราจึงเรียน decision boundary จาก label สองคลาสไม่ได้ Rare-normal และ attack บางชนิดมี packet shape ใกล้กันมาก ทำให้ anomaly score เดี่ยวไม่พอ");
}

// 3 — Threat landscape
{
  const slide = baseSlide("5 รูปแบบการโจมตี — 3 ชั้นของพฤติกรรม", "02 / threat landscape", { dark: true, page: 3 });
  const attacks = [
    ["01", "Dictionary", "CONNECT / credential", C.orange],
    ["02", "Invalid Subscription", "SUBSCRIBE · SUBACK", C.red],
    ["03", "Will Payload", "CONNECT flags / payload", C.lime],
    ["04", "Publish Attack", "PUBLISH length / burst", C.cyan],
    ["05", "SYN Flood", "TCP SYN / ACK state", "65A7FF"],
  ];
  attacks.forEach((a, i) => {
    const x = 0.62 + i * 2.48;
    card(slide, x, 1.65, 2.2, 3.63, { fill: i % 2 ? C.navy3 : C.navy2, line: a[3] });
    slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.61, y: 1.98, w: 0.98, h: 0.98, fill: { color: a[3], transparency: 8 }, line: { color: C.white, transparency: 50 } });
    addText(slide, a[0], x + 0.66, 2.22, 0.88, 0.36, { fontSize: 17, bold: true, color: C.navy, align: "center" });
    addText(slide, a[1], x + 0.22, 3.2, 1.76, 0.68, { fontSize: 15, bold: true, color: C.white, align: "center" });
    addText(slide, a[2], x + 0.24, 4.1, 1.72, 0.52, { fontSize: 10, color: C.gray, align: "center" });
  });
  const layers = [["TCP", "flags · window · stream", "65A7FF"], ["MQTT", "message · QoS · payload", C.cyan], ["CONTEXT", "sequence · frequency · capture", C.lime]];
  layers.forEach((l, i) => chip(slide, `${l[0]}  /  ${l[1]}`, 1.1 + i * 4.05, 5.84, 3.6, l[2], true));
  addText(slide, "Detector ต้องมองทั้ง packet format และพฤติกรรมข้าม packet", 2.55, 6.42, 8.25, 0.33, { fontSize: 13, bold: true, color: C.white, align: "center" });
  finalize(slide, "ภูมิทัศน์การโจมตี", "การโจมตีห้ากลุ่มไม่ได้อยู่ในระดับเดียวกัน Dictionary และ Will Payload สะท้อน CONNECT fields, Invalid Subscription และ Publish อยู่ระดับ MQTT transaction ส่วน SYN Flood อยู่ระดับ TCP state ดังนั้น detector ต้องรวม features หลายชั้น");
}

// 4 — Feature map
{
  const slide = baseSlide("23 features — แปลง field ให้เป็นสัญญาณ", "03 / feature engineering", { dark: false, page: 4 });
  const groups = [
    { x: 0.65, w: 3.75, title: "FRAME", accent: C.orange, big: "2", items: ["frame.len", "frame.protocols"], note: "packet shape + protocol stack" },
    { x: 4.58, w: 3.75, title: "TCP", accent: "4F9BFF", big: "7", items: ["stream / initial RTT", "payload length / window", "SYN · RST · ACK"], note: "connection state + stack signature" },
    { x: 8.5, w: 4.17, title: "MQTT", accent: C.cyanDark, big: "14", items: ["message type / QoS", "CONNECT flags / keep-alive", "credential · topic · message length"], note: "application semantics" },
  ];
  groups.forEach((g) => {
    card(slide, g.x, 1.55, g.w, 4.7, { fill: "FFFFFF", line: "CBDDE2" });
    slide.addShape(pptx.ShapeType.rect, { x: g.x, y: 1.55, w: g.w, h: 0.11, fill: { color: g.accent }, line: { color: g.accent } });
    addText(slide, g.title, g.x + 0.3, 1.9, 1.6, 0.28, { fontSize: 11, bold: true, color: g.accent });
    addText(slide, g.big, g.x + 0.26, 2.25, 1.1, 0.77, { fontSize: 38, bold: true, color: C.navy });
    addText(slide, "features", g.x + 1.16, 2.68, 1.2, 0.22, { fontSize: 10, color: C.muted });
    g.items.forEach((item, idx) => {
      slide.addShape(pptx.ShapeType.ellipse, { x: g.x + 0.32, y: 3.35 + idx * 0.54, w: 0.12, h: 0.12, fill: { color: g.accent }, line: { color: g.accent } });
      addText(slide, item, g.x + 0.57, 3.19 + idx * 0.54, g.w - 0.86, 0.35, { fontSize: 11, color: C.text });
    });
    addText(slide, g.note, g.x + 0.3, 5.55, g.w - 0.6, 0.34, { fontSize: 9, bold: true, color: C.muted, align: "center" });
  });
  addText(slide, "Missing MQTT fields = packet ไม่มี MQTT layer  ไม่ใช่ข้อมูลเสีย", 3.1, 6.55, 7.2, 0.28, { fontSize: 11, bold: true, color: C.cyanDark, align: "center" });
  finalize(slide, "แผนที่ features", "ผมแบ่ง 23 features เป็นสามกลุ่ม Frame, TCP และ MQTT จุดสำคัญคือ missing values ใน MQTT ไม่ควรเติมแบบไม่มีบริบท เพราะหลาย packet เป็น TCP control packet ที่ไม่มี MQTT layer อยู่แล้ว TCP stream ใช้เป็นบริบทภายใน capture แต่ห้ามถือเป็น identity ข้ามไฟล์");
}

// 5 — Core insight
{
  const slide = baseSlide("Core insight: “ความแปลก” ต้องมีเหตุผลจากโปรโตคอล", "04 / design principle", { dark: true, page: 5 });
  addText(slide, "ANOMALY SCORE", 0.72, 1.65, 3.2, 0.3, { fontSize: 10, bold: true, color: C.gray });
  addText(slide, "ไม่เท่ากับ", 4.5, 2.54, 1.2, 0.34, { fontSize: 14, bold: true, color: C.orange, align: "center" });
  addText(slide, "ATTACK PROBABILITY", 6.12, 1.65, 3.4, 0.3, { fontSize: 10, bold: true, color: C.gray });
  card(slide, 0.72, 2.12, 3.62, 2.2, { fill: C.navy2, line: C.orange });
  addText(slide, "Rare Normal", 1.05, 2.48, 2.9, 0.46, { fontSize: 23, bold: true, color: C.orange, align: "center" });
  addText(slide, "packet หายาก แต่ถูกต้อง", 1.1, 3.22, 2.8, 0.3, { fontSize: 12, color: C.gray, align: "center" });
  card(slide, 5.86, 2.12, 3.62, 2.2, { fill: C.navy2, line: C.red });
  addText(slide, "Valid-looking Attack", 6.17, 2.48, 3.0, 0.46, { fontSize: 21, bold: true, color: C.red, align: "center" });
  addText(slide, "packet ถูก format แต่ผิดบริบท", 6.13, 3.22, 3.1, 0.3, { fontSize: 12, color: C.gray, align: "center" });
  card(slide, 10.1, 1.63, 2.55, 3.22, { fill: C.cyan, line: C.cyan });
  addText(slide, "คำตอบ", 10.42, 1.95, 1.9, 0.3, { fontSize: 11, bold: true, color: C.navy, align: "center" });
  addText(slide, "RULE\nANCHORS", 10.33, 2.47, 2.1, 0.86, { fontSize: 24, bold: true, color: C.navy, align: "center" });
  addText(slide, "+ stream context\n+ falsification", 10.43, 3.65, 1.9, 0.62, { fontSize: 12, bold: true, color: C.navy, align: "center" });
  const steps = [["01", "Protocol meaning"], ["02", "Normal exclusion"], ["03", "Stream structure"], ["04", "PCAP evidence"]];
  steps.forEach((s,i)=>{
    const x=0.86+i*3.08;
    chip(slide, s[0], x, 5.45, 0.55, i===3?C.lime:C.cyan, true);
    addText(slide, s[1], x+0.72, 5.42, 2.05, 0.34, {fontSize:11,bold:true,color:C.white});
  });
  addText(slide, "High-precision anchors ก่อน  แล้วค่อยเพิ่ม Recall", 3.1, 6.28, 7.15, 0.34, { fontSize: 16, bold: true, color: C.lime, align: "center" });
  finalize(slide, "Core insight", "Autoencoder หรือ isolation model มักให้คะแนนสูงกับ rare-normal และอาจพลาด attack ที่ใช้ packet format ปกติ ผมจึงใช้ protocol rules เป็น high-precision anchors แล้วค่อยเพิ่ม recall ผ่าน stream structure และ evidence gates");
}

// 6 — Pipeline
{
  const slide = baseSlide("Pipeline: จาก Normal profile ถึงไฟล์ส่ง", "05 / end-to-end workflow", { dark: false, page: 6 });
  const xs = [0.55, 2.73, 4.91, 7.09, 9.27, 11.45];
  const data = [
    ["01", "PROFILE", "เรียนค่าที่เกิดใน Normal", C.cyanDark],
    ["02", "RULES", "TCP + MQTT signatures", C.orange],
    ["03", "CORRECT", "ตัด hard false positives", C.red],
    ["04", "STRUCTURE", "ตรวจความครบ stream", "4F9BFF"],
    ["05", "EVIDENCE", "CSV + PCAP falsifier", C.cyanDark],
    ["06", "SUBMIT", "schema + checksum", C.lime],
  ];
  data.forEach((d,i)=>{
    card(slide,xs[i],1.9,1.65,3.52,{fill:"FFFFFF",line:d[3]});
    slide.addShape(pptx.ShapeType.ellipse,{x:xs[i]+0.46,y:2.24,w:0.73,h:0.73,fill:{color:d[3]},line:{color:d[3]}});
    addText(slide,d[0],xs[i]+0.51,2.42,0.63,0.25,{fontSize:13,bold:true,color:i===5?C.navy:C.white,align:"center"});
    addText(slide,d[1],xs[i]+0.18,3.27,1.29,0.33,{fontSize:11,bold:true,color:C.navy,align:"center"});
    addText(slide,d[2],xs[i]+0.18,3.88,1.29,0.84,{fontSize:9.5,color:C.muted,align:"center"});
    if(i<data.length-1) arrow(slide,xs[i]+1.72,3.33,0.37,C.cyanDark);
  });
  card(slide,1.05,5.88,11.2,0.72,{fill:C.navy,line:C.navy});
  addText(slide,"หลักควบคุม",1.34,6.08,1.25,0.25,{fontSize:10,bold:true,color:C.cyan});
  addText(slide,"ทุก candidate = delta จาก immutable baseline  /  เปลี่ยนแถวน้อย  /  อธิบาย changed Id ได้",2.72,6.01,8.9,0.38,{fontSize:13,bold:true,color:C.white,align:"center"});
  finalize(slide, "Pipeline", "Pipeline เริ่มจาก normal profile แล้วรวมกฎ protocol ตัด false positive ตรวจ stream และใช้ source evidence ก่อนส่ง ทุก submission เป็น delta จาก baseline ที่ไม่แก้ทับ พร้อม changed Id list และ checksum ทำให้ย้อนกลับได้");
}

// 7 — Rules
{
  const slide = baseSlide("Rule engine — 6 anchors ที่อธิบายได้", "06 / protocol detector", { dark: true, page: 7 });
  const rules = [
    ["UNSEEN WINDOW", "tcp.window_size ไม่เคยพบใน train", C.cyan],
    ["NEW SHAPE", "frame.len + window ใหม่ และไม่ใช่ PUBLISH", "4F9BFF"],
    ["SYN FLOOD", "len=54 · win=512 · SYN=1 · ACK=0", C.red],
    ["DICTIONARY", "CONNECT + keep-alive 60 / 3600", C.orange],
    ["SUBSCRIPTION", "MQTT type 8 / 9", C.lime],
    ["PUBLISH", "MQTT type 3 + msg length 19 / 44", C.cyan],
  ];
  rules.forEach((r,i)=>{
    const col=i%2,row=Math.floor(i/2);
    const x=0.7+col*6.18,y=1.55+row*1.63;
    card(slide,x,y,5.82,1.28,{fill:row%2?C.navy3:C.navy2,line:r[2]});
    addText(slide,String(i+1).padStart(2,"0"),x+0.23,y+0.28,0.55,0.42,{fontSize:19,bold:true,color:r[2],align:"center"});
    slide.addShape(pptx.ShapeType.line,{x:x+0.94,y:y+0.24,w:0,h:0.8,line:{color:r[2],width:2}});
    addText(slide,r[0],x+1.18,y+0.18,1.82,0.32,{fontSize:11,bold:true,color:r[2]});
    addText(slide,r[1],x+1.18,y+0.57,4.2,0.42,{fontSize:12.5,color:C.white});
  });
  addText(slide,"OR เพื่อเพิ่ม Recall",1.24,6.55,2.6,0.3,{fontSize:12,bold:true,color:C.cyan});
  addText(slide,"+",4.02,6.52,0.35,0.3,{fontSize:18,bold:true,color:C.gray,align:"center"});
  addText(slide,"EXCLUSION เพื่อรักษา Precision",4.6,6.55,3.65,0.3,{fontSize:12,bold:true,color:C.orange});
  addText(slide,"=",8.48,6.52,0.35,0.3,{fontSize:18,bold:true,color:C.gray,align:"center"});
  addText(slide,"F1 สูงและตรวจสอบได้",8.98,6.55,2.95,0.3,{fontSize:12,bold:true,color:C.lime});
  finalize(slide, "Rule engine", "หกกฎหลักครอบคลุม novelty ของ TCP stack, packet shape, SYN flood, dictionary CONNECT, invalid subscription และ publish signature การรวมด้วย OR เพิ่ม recall แต่ต้องมี exclusion rules แยกต่างหากเพื่อไม่ให้ false positive สะสม");
}

// 8 — Corrections
{
  const slide = baseSlide("Precision corrections — คะแนนสูงเพราะรู้ว่าอะไรต้องไม่เลือก", "07 / hard negatives", { dark: false, page: 8 });
  card(slide,0.65,1.58,5.75,4.95,{fill:"FFFFFF",line:"D0E0E4"});
  addText(slide,"REMOVE",0.98,1.92,1.25,0.3,{fontSize:11,bold:true,color:C.red});
  addText(slide,"PINGRESP hard negative",0.97,2.37,4.6,0.48,{fontSize:22,bold:true,color:C.navy});
  chip(slide,"frame.len = 56",1.0,3.18,1.5,C.red,false);
  chip(slide,"window = 253",2.67,3.18,1.5,C.red,false);
  chip(slide,"msgtype = 13",4.33,3.18,1.5,C.red,false);
  slide.addShape(pptx.ShapeType.line,{x:1.07,y:4.08,w:4.85,h:0,line:{color:"C8D9DE",width:1}});
  addText(slide,"Pseudo model ให้ attack probability ≈ 0.99",1.02,4.36,4.8,0.3,{fontSize:12,color:C.muted});
  addText(slide,"แต่ controlled probe ยืนยันว่าเป็น False Positive",1.02,4.85,4.8,0.34,{fontSize:13,bold:true,color:C.red});
  addText(slide,"Model confidence ≠ evidence",1.02,5.56,4.8,0.35,{fontSize:15,bold:true,color:C.navy});
  card(slide,6.72,1.58,5.92,4.95,{fill:C.navy,line:C.navy3});
  addText(slide,"ADD BACK",7.07,1.92,1.55,0.3,{fontSize:11,bold:true,color:C.lime});
  addText(slide,"PUBLISH capture family",7.06,2.37,4.78,0.48,{fontSize:22,bold:true,color:C.white});
  chip(slide,"msgtype = 3",7.08,3.18,1.45,C.cyan,true);
  chip(slide,"window = 256",8.7,3.18,1.5,C.cyan,true);
  chip(slide,"family-complete",10.37,3.18,1.7,C.lime,true);
  addText(slide,"ส่ง probe แบบแยกกลุ่ม",7.08,4.15,2.1,0.28,{fontSize:11,color:C.gray});
  addText(slide,"→",9.08,4.1,0.4,0.3,{fontSize:17,bold:true,color:C.cyan,align:"center"});
  addText(slide,"score เพิ่มต่อเนื่อง",9.55,4.15,2.15,0.28,{fontSize:11,color:C.gray});
  addText(slide,"Precision-first ไม่ใช่ conservative อย่างเดียว\nแต่คือเพิ่ม Recall เฉพาะกลุ่มที่พิสูจน์แล้ว",7.08,4.85,4.84,0.78,{fontSize:14,bold:true,color:C.white,align:"center"});
  finalize(slide, "Precision corrections", "ตัวอย่างสำคัญคือ PINGRESP window 253 ซึ่ง pseudo model มั่นใจว่าเป็น attack แต่ score probe บอกว่าเป็น false positive เราจึงลบทั้ง family ในทางกลับกัน PUBLISH window 256 ผ่าน probe หลายรอบ จึงเพิ่มกลับแบบ family-complete");
}

// 9 — Structural completion
{
  const slide = baseSlide("Structural completion — หา packet ที่หายจาก pattern", "08 / tcp stream reasoning", { dark: true, page: 9 });
  addText(slide,"SYN-flood stream coverage",0.72,1.53,3.2,0.3,{fontSize:11,bold:true,color:C.gray});
  addText(slide,"599 / 600",0.72,1.94,3.6,0.7,{fontSize:39,bold:true,color:C.cyan});
  addText(slide,"streams ในช่วง 0–599 ถูกครอบคลุม",0.75,2.72,3.7,0.32,{fontSize:12,color:C.gray});
  const startX=4.76;
  for(let i=0;i<20;i++){
    const missing=i===6;
    slide.addShape(pptx.ShapeType.roundRect,{x:startX+(i%10)*0.67,y:1.67+Math.floor(i/10)*0.68,w:0.48,h:0.48,fill:{color:missing?C.orange:C.cyan,transparency:missing?0:20},line:{color:missing?C.orange:C.cyan,width:1}});
  }
  addText(slide,"…",11.68,2.06,0.4,0.3,{fontSize:20,bold:true,color:C.gray,align:"center"});
  card(slide,0.72,3.63,11.9,2.25,{fill:C.navy2,line:C.orange});
  addText(slide,"STREAM 194",1.05,4.0,1.65,0.32,{fontSize:12,bold:true,color:C.orange});
  const px=3.05;
  for(let i=0;i<9;i++){
    slide.addShape(pptx.ShapeType.ellipse,{x:px+i*0.58,y:4.05,w:0.31,h:0.31,fill:{color:C.gray,transparency:25},line:{color:C.gray}});
    if(i<8) slide.addShape(pptx.ShapeType.line,{x:px+0.3+i*0.58,y:4.205,w:0.28,h:0,line:{color:C.gray,width:1}});
  }
  addText(slide,"9 packet normal template",3.05,4.63,5.0,0.28,{fontSize:10,color:C.gray,align:"center"});
  arrow(slide,8.43,4.05,0.65,C.orange);
  card(slide,9.35,3.94,2.72,1.15,{fill:C.orange,line:C.orange});
  addText(slide,"Id = 9816",9.67,4.16,2.08,0.34,{fontSize:18,bold:true,color:C.navy,align:"center"});
  addText(slide,"packet ส่วนเกินเพียงแถวเดียว",9.48,4.62,2.45,0.22,{fontSize:9,bold:true,color:C.navy,align:"center"});
  metric(slide,3.15,6.18,3.0,"PUBLIC BEFORE","0.96193",C.gray,"validated publish model");
  arrow(slide,6.36,6.58,0.58,C.lime);
  metric(slide,7.18,6.18,3.0,"PUBLIC AFTER","0.96230",C.lime,"+ Id 9816");
  finalize(slide, "Structural completion", "SYN-flood labels ครอบคลุม stream 0 ถึง 599 ยกเว้น 194 เมื่อตรวจ stream 194 พบ normal template 9 packets และ packet ส่วนเกินเพียง Id 9816 การเพิ่มแถวเดียวทำให้ Public เพิ่มจาก 0.96193 เป็น 0.96230");
}

// 10 — Score progression
{
  const slide = baseSlide("Score progression — ทุกก้าวมีสมมติฐาน", "09 / controlled experiments", { dark: false, page: 10 });
  const vals=[0.54898,0.93152,0.95649,0.95834,0.96193,0.96230,0.96267];
  const labels=["FIRST","RULES","ROLLBACK","PUBLISH","COMPLETE","+9816","+1145"];
  const colors=[C.red,C.orange,C.cyanDark,"4F9BFF",C.cyanDark,C.cyanDark,C.lime];
  const x0=0.85,y0=5.85,maxH=3.8;
  vals.forEach((v,i)=>{
    const h=Math.max(0.55,(v-0.5)/0.5*maxH);
    const x=x0+i*1.72;
    slide.addShape(pptx.ShapeType.roundRect,{x,y:y0-h,w:1.08,h,fill:{color:colors[i],transparency:i===6?0:8},line:{color:colors[i],width:1}});
    addText(slide,v.toFixed(5),x-0.12,y0-h-0.42,1.32,0.28,{fontSize:10.5,bold:true,color:C.navy,align:"center"});
    addText(slide,labels[i],x-0.19,6.04,1.46,0.27,{fontSize:8.3,bold:true,color:C.muted,align:"center"});
  });
  slide.addShape(pptx.ShapeType.line,{x:0.72,y:5.86,w:11.9,h:0,line:{color:C.navy,width:1.2}});
  chip(slide,"broad novelty 0.91143 → ถูก rollback",0.82,1.43,3.33,C.red,false);
  chip(slide,"single-row structural probe",4.92,1.43,2.95,C.cyanDark,false);
  chip(slide,"payload evidence +0.00037",8.63,1.43,3.3,C.lime,false);
  addText(slide,"จาก 0.54898 → 0.96267",3.7,6.63,5.9,0.36,{fontSize:18,bold:true,color:C.navy,align:"center"});
  finalize(slide, "Score progression", "คะแนนไม่ได้เพิ่มเป็นเส้นตรง Broad novelty เคยทำให้คะแนนลดจึง rollback หลังจากนั้นใช้กลุ่มเล็กและ homogeneous มากขึ้น จาก rules, publish completion, structural Id 9816 และ payload Id 1145 จน Public สูงสุด 0.96267");
}

// 11 — PCAP scale
{
  const slide = baseSlide("PCAP evidence — ตรวจจริงมากกว่า 37 GB", "10 / source validation", { dark: true, page: 11 });
  metric(slide,0.72,1.55,2.75,"ATTACK PCAPS","313 / 313",C.red,"30.4 GB · scan สำเร็จครบ");
  metric(slide,3.72,1.55,2.75,"NORMAL PCAPS","49 / 49",C.cyan,"7.0 GB · falsifier corpus");
  metric(slide,6.72,1.55,2.75,"TCP PACKETS","260.9 M",C.lime,"รวม attack + normal");
  metric(slide,9.72,1.55,2.75,"EXACT MATCH","422",C.orange,"อยู่ใน positive เดิมทั้งหมด");
  addText(slide,"MULTI-PROFILE HASH",0.75,3.18,2.5,0.27,{fontSize:10,bold:true,color:C.gray});
  const profiles=["tcp_shape","packet","packet_stream","packet_rtt","packet_full"];
  profiles.forEach((p,i)=>{
    const x=0.75+i*2.42;
    card(slide,x,3.72,2.05,1.48,{fill:i===4?C.cyan:C.navy2,line:i===4?C.cyan:C.navy3});
    addText(slide,String(i+1).padStart(2,"0"),x+0.18,3.93,0.45,0.25,{fontSize:10,bold:true,color:i===4?C.navy:C.cyan});
    addText(slide,p,x+0.18,4.38,1.68,0.32,{fontSize:10.5,bold:true,color:i===4?C.navy:C.white,align:"center"});
  });
  addText(slide,"Attack support",1.12,5.93,2.0,0.3,{fontSize:12,bold:true,color:C.red,align:"center"});
  addText(slide,"+",3.25,5.91,0.4,0.3,{fontSize:18,bold:true,color:C.gray,align:"center"});
  addText(slide,"ไม่ชน Normal",3.82,5.93,2.0,0.3,{fontSize:12,bold:true,color:C.cyan,align:"center"});
  addText(slide,"+",5.98,5.91,0.4,0.3,{fontSize:18,bold:true,color:C.gray,align:"center"});
  addText(slide,"ผ่าน context",6.55,5.93,2.0,0.3,{fontSize:12,bold:true,color:C.lime,align:"center"});
  addText(slide,"=",8.73,5.91,0.4,0.3,{fontSize:18,bold:true,color:C.gray,align:"center"});
  addText(slide,"Candidate gate",9.25,5.93,2.2,0.3,{fontSize:12,bold:true,color:C.white,align:"center"});
  finalize(slide, "PCAP evidence", "ผมสแกน attack PCAP 313 ไฟล์และ normal PCAP 49 ไฟล์ รวมมากกว่า 37 GB หรือ 260.9 ล้าน TCP packets ใช้ hash หลาย profile ตั้งแต่ packet shape ถึง full features หลักคือ candidate ต้องมี attack support และไม่ชน normal corpus");
}

// 12 — Falsification cases
{
  const slide = baseSlide("Evidence ต้องหักล้างได้ — 2 แถว 2 ผลลัพธ์", "11 / falsification", { dark: false, page: 12 });
  card(slide,0.67,1.55,5.85,4.85,{fill:"FFF5F3",line:C.red});
  addText(slide,"REJECT",0.98,1.89,1.2,0.28,{fontSize:10,bold:true,color:C.red});
  addText(slide,"Id = 8150",0.97,2.35,2.6,0.48,{fontSize:25,bold:true,color:C.navy});
  addText(slide,"พบ attack packet-shape support\nแต่ไม่มี full / RTT context",0.99,3.05,4.8,0.72,{fontSize:14,color:C.muted});
  metric(slide,1.0,4.05,2.35,"BEFORE","0.96230",C.gray,"Public F1",false);
  arrow(slide,3.52,4.46,0.55,C.red);
  metric(slide,4.25,4.05,1.98,"AFTER","0.96196",C.red,"ลดลง",false);
  addText(slide,"ข้อสรุป: packet shape เดี่ยวไม่พอ",1.02,5.54,4.95,0.36,{fontSize:14,bold:true,color:C.red,align:"center"});
  card(slide,6.82,1.55,5.84,4.85,{fill:"F2FAEA",line:C.lime});
  addText(slide,"ACCEPT",7.12,1.89,1.2,0.28,{fontSize:10,bold:true,color:C.cyanDark});
  addText(slide,"Id = 1145",7.11,2.35,2.6,0.48,{fontSize:25,bold:true,color:C.navy});
  addText(slide,"payload family ใน attack-heavy stream\nผ่าน residual precision gate",7.13,3.05,4.8,0.72,{fontSize:14,color:C.muted});
  metric(slide,7.13,4.05,2.35,"BEFORE","0.96230",C.gray,"Public F1",false);
  arrow(slide,9.65,4.46,0.55,C.lime);
  metric(slide,10.38,4.05,1.98,"AFTER","0.96267",C.cyanDark,"เพิ่มขึ้น",false);
  addText(slide,"ข้อสรุป: เก็บกฎและ feature twin",7.15,5.54,4.95,0.36,{fontSize:14,bold:true,color:C.cyanDark,align:"center"});
  addText(slide,"ระบบที่ดีไม่ได้แค่หา evidence — ต้องยอมทิ้งสมมติฐานเมื่อผลจริงขัดแย้ง",1.55,6.64,10.25,0.32,{fontSize:13,bold:true,color:C.navy,align:"center"});
  finalize(slide, "Falsification", "Id 8150 ดูดีจาก packet shape แต่คะแนนลด จึง reject ทันที ส่วน Id 1145 ผ่าน residual gate และทำให้คะแนนเพิ่ม สิ่งสำคัญคือ evidence pipeline ต้องหักล้างสมมติฐานได้ ไม่ใช่สะสมเหตุผลสนับสนุนอย่างเดียว");
}

// 13 — Public/private gap
{
  const slide = baseSlide("Public ดีที่สุด ≠ Private ดีที่สุด", "12 / model selection", { dark: true, page: 13 });
  card(slide,0.72,1.58,5.62,4.72,{fill:C.navy2,line:C.cyan});
  addText(slide,"SELECTED BY PUBLIC",1.06,1.94,2.5,0.28,{fontSize:10,bold:true,color:C.cyan});
  addText(slide,"payload + Id 1145",1.05,2.4,4.3,0.43,{fontSize:21,bold:true,color:C.white});
  metric(slide,1.06,3.22,2.18,"PUBLIC","0.96267",C.cyan,"ดีที่สุด",true);
  metric(slide,3.58,3.22,2.18,"PRIVATE","0.97198",C.lime,"final selected",true);
  addText(slide,"Public สูงกว่า v8  +0.00074",1.08,4.77,4.55,0.3,{fontSize:12,color:C.gray});
  card(slide,6.95,1.58,5.62,4.72,{fill:C.navy3,line:C.lime});
  addText(slide,"PRIVATE-STABLE ALTERNATIVE",7.29,1.94,3.1,0.28,{fontSize:10,bold:true,color:C.lime});
  addText(slide,"v8 micro best",7.28,2.4,4.3,0.43,{fontSize:21,bold:true,color:C.white});
  metric(slide,7.29,3.22,2.18,"PUBLIC","0.96193",C.cyan,"ต่ำกว่าเล็กน้อย",true);
  metric(slide,9.81,3.22,2.18,"PRIVATE","0.97232",C.lime,"สูงกว่า +0.00034",true);
  addText(slide,"Private สูงกว่า selected file",7.31,4.77,4.55,0.3,{fontSize:12,color:C.gray});
  addText(slide,"เลือกโมเดลจาก protocol evidence + stability + stress test  ไม่ใช่ Public score อย่างเดียว",1.18,6.64,11.0,0.36,{fontSize:14,bold:true,color:C.lime,align:"center"});
  finalize(slide, "Public–Private gap", "ไฟล์ Public สูงสุดได้ Private 0.97198 แต่ v8 ที่ Public ต่ำกว่าเล็กน้อยกลับได้ Private 0.97232 นี่คือ sampling variance ของ split 50/50 และเหตุผลที่ไม่ควรเลือกโมเดลจาก Public score เพียงตัวเดียว");
}

// 14 — Final result
{
  const slide = baseSlide("ผลสุดท้าย — สูงกว่า baseline ชัดเจน", "13 / leaderboard result", { dark: false, page: 14 });
  const bars=[
    ["Organizer baseline",0.65030,C.gray],
    ["Our selected file",0.97198,C.cyanDark],
    ["Private rank 2",0.97879,C.orange],
    ["Private rank 1",0.98149,C.lime],
  ];
  bars.forEach((b,i)=>{
    const y=1.72+i*1.05;
    addText(slide,b[0],0.78,y,2.25,0.32,{fontSize:11,bold:i===1,color:C.navy});
    slide.addShape(pptx.ShapeType.roundRect,{x:3.15,y:y+0.02,w:8.55,h:0.42,fill:{color:"D8E5E9"},line:{color:"D8E5E9"}});
    slide.addShape(pptx.ShapeType.roundRect,{x:3.15,y:y+0.02,w:8.55*b[1],h:0.42,fill:{color:b[2]},line:{color:b[2]}});
    addText(slide,b[1].toFixed(5),11.83,y-0.02,0.85,0.38,{fontSize:11,bold:true,color:b[2],align:"right"});
  });
  metric(slide,0.8,6.0,3.35,"PRIVATE GAIN VS BASELINE","+0.32168",C.cyanDark,"0.65030 → 0.97198",false);
  metric(slide,4.98,6.0,3.35,"GAP TO RANK 1","0.00951",C.orange,"ยังมีพื้นที่จาก flow context",false);
  metric(slide,9.15,6.0,3.35,"POSITIVE LABELS","2,811",C.lime,"จาก 10,000 records",false);
  addText(slide,"คะแนน 0.97198 อยู่ในกลุ่ม tie หลังสองคะแนนสูงสุด",3.28,5.22,6.7,0.36,{fontSize:14,bold:true,color:C.navy,align:"center"});
  finalize(slide, "ผลสุดท้าย", "ไฟล์ที่เลือกได้ Private 0.97198 สูงกว่า baseline ผู้จัด 0.65030 มาก คะแนนสูงสุด 0.98149 และอันดับสอง 0.97879 จากนั้นมีหลายทีมที่ 0.97198 รวมทีมของเรา ช่องว่างจากอันดับหนึ่ง 0.00951");
}

// 15 — What failed
{
  const slide = baseSlide("สิ่งที่ลองแล้วไม่ใช้ — ความล้มเหลวที่ช่วยให้แม่นขึ้น", "14 / negative results", { dark: true, page: 15 });
  const fails=[
    ["BROAD NOVELTY","Public ลดถึง 0.91143","rare-normal ถูกมองเป็น attack",C.red],
    ["PSEUDO LABELS","มั่นใจผิดกับ PINGRESP","confidence ไม่ผ่าน hard-negative check",C.orange],
    ["EXTERNAL MODEL","เรียนรู้ TCP stack ของ source","domain shift แทน attack semantics","4F9BFF"],
    ["PACKET SHAPE","Id 8150 ทำ score ลด","ไม่มี flow / RTT context",C.cyan],
  ];
  fails.forEach((f,i)=>{
    const x=0.72+(i%2)*6.08,y=1.58+Math.floor(i/2)*2.28;
    card(slide,x,y,5.7,1.85,{fill:i%2?C.navy3:C.navy2,line:f[3]});
    addText(slide,f[0],x+0.28,y+0.25,2.5,0.27,{fontSize:10,bold:true,color:f[3]});
    addText(slide,f[1],x+0.28,y+0.67,4.96,0.36,{fontSize:16,bold:true,color:C.white});
    addText(slide,f[2],x+0.28,y+1.21,4.96,0.28,{fontSize:10.5,color:C.gray});
  });
  card(slide,2.22,6.15,8.9,0.62,{fill:C.lime,line:C.lime});
  addText(slide,"Negative result = ข้อมูลสำหรับออกแบบ precision gate รอบถัดไป",2.48,6.3,8.38,0.3,{fontSize:14,bold:true,color:C.navy,align:"center"});
  finalize(slide, "Negative results", "สี่แนวทางที่ไม่ใช้คือ broad novelty, pseudo labels ที่ไม่ผ่าน hard-negative check, external model ที่เจอ domain shift และ packet shape เดี่ยว ทุกความล้มเหลวถูกเก็บเป็น guardrail ไม่ให้ทำผิดซ้ำ");
}

// 16 — Next work
{
  const slide = baseSlide("งานต่อไป: จาก packet → flow → transaction", "15 / next high-compute iteration", { dark: false, page: 16 });
  const stages=[
    ["PACKET","features เดิม 23 ตัว",C.gray],
    ["FLOW","time · direction · state",C.cyanDark],
    ["MQTT TXN","CONNECT → PUBLISH",C.orange],
    ["ENSEMBLE","rules + grouped model",C.lime],
  ];
  stages.forEach((s,i)=>{
    const x=0.78+i*3.03;
    card(slide,x,1.69,2.53,2.22,{fill:i===0?"EDF2F4":"FFFFFF",line:s[2]});
    slide.addShape(pptx.ShapeType.ellipse,{x:x+0.88,y:1.98,w:0.78,h:0.78,fill:{color:s[2]},line:{color:s[2]}});
    addText(slide,String(i+1),x+0.98,2.18,0.58,0.25,{fontSize:14,bold:true,color:i===0?C.white:C.navy,align:"center"});
    addText(slide,s[0],x+0.25,3.0,2.03,0.3,{fontSize:11,bold:true,color:C.navy,align:"center"});
    addText(slide,s[1],x+0.25,3.43,2.03,0.25,{fontSize:9.5,color:C.muted,align:"center"});
    if(i<3) arrow(slide,x+2.62,2.65,0.31,C.cyanDark);
  });
  const checks=["group split ตาม capture file","inter-arrival + burst features","TCP transition / SYN-ACK ratio","MQTT sequence tokens","worst-fold F1 + calibration","normal-PCAP falsification"];
  checks.forEach((t,i)=>{
    const x=0.95+(i%3)*4.12,y=4.62+Math.floor(i/3)*0.78;
    slide.addShape(pptx.ShapeType.ellipse,{x,y:y+0.08,w:0.19,h:0.19,fill:{color:i<3?C.cyanDark:C.orange},line:{color:i<3?C.cyanDark:C.orange}});
    addText(slide,t,x+0.35,y,3.45,0.35,{fontSize:11,bold:true,color:C.navy});
  });
  card(slide,2.0,6.35,9.3,0.48,{fill:C.navy,line:C.navy});
  addText(slide,"Validation unit = capture/session  ไม่ใช่ random packet row",2.25,6.43,8.8,0.28,{fontSize:13,bold:true,color:C.lime,align:"center"});
  finalize(slide, "งานต่อไป", "รอบต่อไปต้องเปลี่ยนหน่วยวิเคราะห์จาก packet เป็น flow และ MQTT transaction สร้าง inter-arrival, direction, burst และ state transition สำคัญที่สุดคือต้อง split validation ตาม capture หรือ session ไม่ใช่ random rows เพื่อป้องกัน leakage");
}

// 17 — Closing
{
  const slide = pptx.addSlide();
  slide.background = { color: C.navy };
  addGrid(slide,true);
  addText(slide,"3 TAKEAWAYS",0.75,0.66,2.4,0.28,{fontSize:10,bold:true,color:C.cyan});
  addText(slide,"Detector ที่ชนะ ต้อง “อธิบายได้” และ “หักล้างได้”",0.73,1.1,10.8,0.62,{fontSize:28,bold:true,color:C.white});
  const takeaways=[
    ["01","Protocol first","ใช้ความหมาย TCP/MQTT เป็น precision anchors",C.cyan],
    ["02","Context matters","packet shape ต้องมี stream / transaction context",C.orange],
    ["03","Public is noisy","เลือกโมเดลจาก stability ไม่ใช่คะแนนเดียว",C.lime],
  ];
  takeaways.forEach((t,i)=>{
    const x=0.75+i*4.12;
    card(slide,x,2.35,3.72,2.22,{fill:i===1?C.navy3:C.navy2,line:t[3]});
    addText(slide,t[0],x+0.27,2.64,0.48,0.32,{fontSize:16,bold:true,color:t[3],align:"center"});
    addText(slide,t[1],x+0.89,2.58,2.45,0.37,{fontSize:16,bold:true,color:C.white});
    addText(slide,t[2],x+0.3,3.35,3.08,0.74,{fontSize:12,color:C.gray,align:"center"});
  });
  addText(slide,"Q & A",0.77,5.44,2.8,0.62,{fontSize:31,bold:true,color:C.cyan});
  addText(slide,"Public 0.96267  /  Private 0.97198",0.8,6.22,4.6,0.3,{fontSize:13,bold:true,color:C.lime});
  addText(slide,"Source: official challenge brief · Kaggle final results · reproducible Git artifacts",7.12,6.29,5.45,0.25,{fontSize:8.5,color:C.gray,align:"right"});
  addFooter(slide,17,true);
  finalize(slide, "สรุปและถามตอบ", "สรุปสามข้อ หนึ่ง ใช้ protocol meaning เป็น anchor สอง packet shape ต้องมี context สาม Public leaderboard มี noise จึงต้องเลือกจาก stability และ evidence ขอบคุณครับ พร้อมตอบคำถามเรื่องกฎ การทดลอง PCAP หรือการพัฒนาต่อ");
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.mkdirSync(path.dirname(NOTES_PATH), { recursive: true });
  const md = [
    "# Speaker Notes — The IoT Attack Detection Challenge",
    "",
    "ผู้บรรยาย: 610686-วชิรวิทย์",
    "",
    ...notes.flatMap((item, index) => [
      `## ${String(index + 1).padStart(2, "0")} — ${item.title}`,
      "",
      item.note,
      "",
    ]),
  ].join("\n");
  fs.writeFileSync(NOTES_PATH, md, "utf8");
  await renderAllText();
  await pptx.writeFile({ fileName: PPTX_PATH, compression: true });
  console.log(`slides=${pptx._slides.length}`);
  console.log(`pptx=${PPTX_PATH}`);
  console.log(`notes=${NOTES_PATH}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
