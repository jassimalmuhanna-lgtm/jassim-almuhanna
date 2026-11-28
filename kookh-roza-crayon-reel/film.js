// كوخ روزا — 15 s vertical reel in the Crayon Picture Book style.
// One page (world coords 1080×1920); the camera moves over it. Timeline, layers, events, subtitles.
import { layer, clear, line, fill, dab, handCircle, ellipse, xf, smooth, CAM, BOIL, W, H, sx, sy, ws } from './crayon.js';
import { group, clearGroup, part } from './rig.js';
import { clamp, lerp, hash, mulberry, track, ss, eio, eo } from '/core/lib.js';

export const DUR = 15;
const K = {
  ink: '#0F5C63',    // all outlines: Kookh Roza dark teal (never black)
  peach: '#F2A9A0', mint: '#A9D9D6', mintL: '#BFE3E0', teal: '#2A8C8C',
  yellow: '#F5C63C', pink: '#EE8EA4', green: '#7DBB6E', brown: '#9A6B4F', cream: '#FFF4E2',
  white: '#FFFAEE',  // white wax: invisible until the night wash
};
const WASH_COL = [0.15, 0.19, 0.44];
const FONT = 'Baloo Bhaijaan 2';
const pr = (t, a, b) => clamp((t - a) / (b - a));

// ——— narration (Gemini TTS, voice Zephyr, played at 1.07×; t = start, d = length) ———
export const LINES = [
  { id: 'l1', t: 0.35, d: 5.97, text: 'بقرية عالي، كوخ صغير\nمليان ملابس مواليد من تركيا' },
  { id: 'l2', t: 7.25, d: 3.36, text: 'حياكم من ٤ لين ١٠ بالليل' },
  { id: 'l3', t: 11.05, d: 2.89, text: 'أو اطلبوا بالواتساب. كوخ روزا!' },
];
export const SUBS = LINES.map((L, i) => {
  const t0 = L.t - 0.1; let t1 = Math.max(t0 + 1.8, L.t + L.d + 0.6);
  const nx = LINES[i + 1]; t1 = nx ? Math.min(t1, nx.t - 0.25) : Math.min(t1, DUR - 0.05);
  return { t0, t1, text: L.text };
});

// ——— the page ———
const HOUSE = {
  chimney: [[640, 800], [640, 700], [688, 700], [688, 800], [640, 800]],
  roof: [[325, 885], [540, 688], [755, 885], [325, 885]],
  walls: [[365, 875], [715, 875], [715, 1150], [365, 1150], [365, 875]],
  door: [...ellipse(540, 1050, 42, 40, 16, Math.PI, Math.PI * 2), [582, 1150], [498, 1150], [498, 1050]],
  winL: handCircle(440, 965, 40, 21, 0.08, 40),
  winR: [[575, 925], [650, 925], [650, 1000], [575, 1000], [575, 925]],
};
const GROUND = (() => { const top = [], bot = []; for (let x = 20; x <= 1060; x += 40) { top.push([x, 1146 + 8 * Math.sin(x * 0.02) + 6 * hash(x)]); bot.push([x, 1188 + 6 * Math.sin(x * 0.031 + 1)]); } return [...top, ...bot.reverse()]; })();
const POLE = [[110, 1200, 1215, 1440], [970, 1200, 1215, 1440]];
const lineY = x => 1215 + 42 * Math.sin(Math.PI * clamp((x - 110) / 860));
const LINE_PTS = Array.from({ length: 44 }, (_, i) => { const x = 110 + 860 * i / 43; return [x, lineY(x)]; });
// clothes, drawn hanging from (0,0)
const ONESIE = [[-40, 0], [-75, 12], [-98, 46], [-72, 64], [-56, 48], [-56, 140], [-32, 172], [-9, 152], [9, 152], [32, 172], [56, 140], [56, 48], [72, 64], [98, 46], [75, 12], [40, 0], [20, 15], [0, 19], [-20, 15]];
const DRESS = [[-30, 0], [-27, 42], [-46, 62], [-86, 172], [86, 172], [46, 62], [27, 42], [30, 0], [13, 0], [10, 24], [-10, 24], [-13, 0]];
const TEE = [[-38, 0], [-82, 14], [-112, 56], [-84, 77], [-63, 54], [-61, 152], [61, 152], [63, 54], [84, 77], [112, 56], [82, 14], [38, 0], [18, 15], [0, 19], [-18, 15]];
const ITEMS = [
  { shape: ONESIE, x: 285, col: K.peach, t: 3.65, seed: 41 },
  { shape: DRESS, x: 540, col: K.teal, t: 4.45, seed: 52 },
  { shape: TEE, x: 795, col: K.mint, t: 5.25, seed: 63 },
];
function heartPts(cx, cy, s) { const out = []; for (let i = 0; i <= 40; i++) { const a = i / 40 * Math.PI * 2; out.push([cx + s * 16 * Math.pow(Math.sin(a), 3) / 16, cy - s * (13 * Math.cos(a) - 5 * Math.cos(2 * a) - 2 * Math.cos(3 * a) - Math.cos(4 * a)) / 16]); } return out; }
function starPts(cx, cy, r, rot = 0) { const out = []; for (let i = 0; i <= 10; i++) { const a = rot - Math.PI / 2 + i * Math.PI / 5; const rr = i % 2 ? r * 0.45 : r; out.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]); } return out; }

// white-wax sky: stars and a crescent, hidden until the wash
const R = mulberry(2026);
const STARS = []; while (STARS.length < 46) { const x = 40 + R() * 1000, y = 60 + R() * 600; if (y > 400 && y < 650 && x > 120 && x < 960) continue; if (Math.hypot(x - 900, y - 170) < 90) continue; if (y > 640 && x > 300 && x < 780) continue; STARS.push({ x, y, r: 5 + R() * 7, big: R() < 0.28, seed: 300 + STARS.length, rot: R() }); }
const MOON = { x: 905, y: 165, r: 62 };
const HOURS = { text: 'من ٤ لين ١٠ بالليل', x: 540, y: 585, size: 80 };
const BANDS = [
  { y0: -220, y1: 1178, t0: 6.95, t1: 8.9, dir: 1, seed: 1 },
];
const X0 = -280, X1 = 1360;
function bandFront(b, t) { const u = clamp((t - b.t0) / (b.t1 - b.t0)); const e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; const v = 0.15 * u + 0.85 * e; return b.dir > 0 ? lerp(X0, X1, v) : lerp(X1, X0, v); }
const washReach = (x, y) => { for (const b of BANDS) if (y >= b.y0 && y <= b.y1) { const u = b.dir > 0 ? (x - X0) / (X1 - X0) : (X1 - x) / (X1 - X0); return b.t0 + (b.t1 - b.t0) * clamp(u * 0.85 + 0.05); } return 99; };

// ——— camera: world centre + zoom ———
const camT = track([
  [0, [540, 985, 1.55]], [3.0, [540, 1005, 1.64]], [3.55, [330, 1180, 1.62]], [6.15, [770, 1195, 1.62]],
  [6.95, [540, 850, 1.0]], [10.6, [540, 870, 1.02]], [12.0, [540, 960, 1.0]], [15, [540, 960, 1.0]],
]);

// ——— events (exported for the mix) ———
export const EV = [];
const ev = (t, type, o = {}) => EV.push({ t: +t.toFixed(3), type, ...o });
LINES.forEach(L => ev(L.t, 'voice', { id: L.id }));
ev(0, 'room');
[[0.0, 0.5, -0.2], [0.4, 0.5, 0.2], [0.8, 0.3, 0], [1.0, 0.35, -0.3], [1.3, 0.3, 0.4]].forEach(([t, d, pan]) => ev(t, 'scratch', { dur: d, pan }));
[[0.5, 0.8, -0.1], [1.1, 0.9, 0.1], [1.9, 0.5, 0], [2.0, 0.8, 0.3]].forEach(([t, d, pan]) => ev(t, 'scribble', { dur: d, pan }));
ev(2.25, 'pop', { pan: -0.3 });
ev(3.0, 'door', { pan: 0 });
ev(3.2, 'scratch', { dur: 0.6, pan: -0.5 });
ITEMS.forEach((it, i) => { ev(it.t, 'scratch', { dur: 0.35, pan: (it.x - 540) / 540 }); ev(it.t + 0.35, 'scribble', { dur: 0.5, pan: (it.x - 540) / 540 }); ev(it.t + 0.12, 'peg', { i, pan: (it.x - 540) / 540 }); ev(it.t + 0.4, 'glock', { i }); });
ev(6.35, 'silence', { dur: 0.6 });
BANDS.forEach(b => ev(b.t0, 'brush', { dur: b.t1 - b.t0, dir: b.dir }));
ev(6.85, 'dip');
STARS.forEach(s => { if (s.big) ev(washReach(s.x, s.y), 'glint', { pan: (s.x - 540) / 540 }); });
ev(washReach(MOON.x, MOON.y), 'glint', { pan: 0.7, big: 1 });
ev(8.6, 'pop', { pan: -0.2 }); ev(8.85, 'pop', { pan: 0.2 });
ev(11.25, 'write', { dur: 0.9, pan: 0 });
ev(11.45, 'write', { dur: 0.7, pan: 0.2 });
ev(12.0, 'write', { dur: 0.6, pan: -0.2 });
ev(13.9, 'end');
[['A', 0], ['B', 3.0], ['S', 6.35], ['C', 6.95], ['D', 10.8]].forEach(([id, t]) => ev(t, 'cue', { id }));

// ——— Arabic crayon lettering: whole words (Arabic letters must join), written right→left by a moving clip ———
function arText(L, str, x, y, o = {}) {
  const g = L.g, st = BOIL.step, seed = o.seed ?? 7, ba = o.boil ?? 1;
  const size = o.size ?? 56;
  g.save();
  g.font = `${o.weight ?? 700} ${size}px "${FONT}"`; g.textBaseline = 'alphabetic'; g.direction = o.ltr ? 'ltr' : 'rtl'; g.textAlign = 'center';
  const tw = g.measureText(str).width;
  const rv = o.reveal ?? 1; if (rv <= 0) { g.restore(); return tw; }
  if (rv < 1) { g.beginPath(); if (o.ltr) g.rect(x - tw / 2 - 20, y - size * 1.6, (tw + 40) * rv, size * 2.4); else g.rect(x + tw / 2 + 20 - (tw + 40) * rv, y - size * 1.6, (tw + 40) * rv, size * 2.4); g.clip(); }
  const jx = (hash(seed + st * 1.1) - .5) * 1.6 * ba, jy = (hash(seed + 3 + st * 2.3) - .5) * 1.6 * ba;
  const rot = (hash(seed * 1.9) - .5) * 0.02 + (hash(seed + st * .7) - .5) * 0.006 * ba;
  g.translate(x + jx, y + jy); g.rotate(rot);
  g.fillStyle = o.col || K.ink; g.globalAlpha = o.p ?? 1; g.fillText(str, 0, 0);
  if (o.stroke) { g.lineWidth = o.stroke; g.strokeStyle = o.col || K.ink; g.lineJoin = 'round'; g.globalAlpha = (o.p ?? 1) * 0.7; g.strokeText(str, 0, 0); }
  g.restore();
  return tw;
}
function measure(str, size, weight = 700) { const g = SUBK.g; g.save(); g.font = `${weight} ${size}px "${FONT}"`; g.direction = 'rtl'; const w = g.measureText(str).width; g.restore(); return w; }
// text in world coords (camera-relative position and size)
const arWorld = (L, str, x, y, o) => arText(L, str, sx(x), sy(y), { ...o, size: (o.size ?? 56) * CAM.s });

// ——— layers ———
const SKY = { f: layer(), l: layer() }, BG = { f: layer(), l: layer() }, HS = group(), WASH = layer(), TOP = layer(), SUBK = layer(), SUBT = layer();

function drawHouse(t) {
  const C = HS;
  const lo = (d, seed, w = 7) => ({ col: K.ink, w, p: 0.95, seed, draw: d });
  part(C, HOUSE.chimney, { col: K.peach, p: 0.9, draw: pr(t, 1.25, 1.6), seed: 9, gap: 9 }, lo(pr(t, 1.2, 1.4), 9, 6));
  part(C, HOUSE.roof, { col: K.peach, p: 0.92, draw: pr(t, 0.5, 1.3), seed: 10, gap: 9.5, cross: true, crossP: 0.5 }, lo(pr(t, 0.0, 0.5), 10, 8.5));
  part(C, HOUSE.walls, { col: K.mint, p: 0.9, draw: pr(t, 1.1, 2.0), seed: 11, gap: 10, ang: 0.4 }, lo(pr(t, 0.4, 0.9), 11, 8));
  // door: closed until 3.0, then a new drawing: open, with warm light inside
  const open = t >= 3.0;
  if (!open) part(C, HOUSE.door, { col: K.teal, p: 0.95, draw: pr(t, 1.9, 2.4), seed: 12, gap: 7 }, lo(pr(t, 0.8, 1.1), 12, 6.5));
  else {
    part(C, HOUSE.door, { col: K.yellow, p: 0.95, seed: 13, gap: 7 }, lo(1, 13, 6.5));
    const leaf = [[498, 1018], [458, 1032], [458, 1156], [498, 1150], [498, 1018]];
    part(C, leaf, { col: K.teal, p: 0.95, seed: 14, gap: 6, ang: 1.4 }, lo(1, 14, 6));
    dab(C.f, 468, 1095, 4, { col: K.ink, p: 1, seed: 15 });
  }
  if (!open) dab(C.f, 570, 1102, 4.5, { col: K.ink, p: 1, seed: 16 });
  // windows: light up at night (colouring = the lights coming on)
  const lit1 = pr(t, 8.6, 9.0), lit2 = pr(t, 8.85, 9.25);
  part(C, HOUSE.winL, lit1 > 0 ? { col: K.yellow, p: 0.95, draw: lit1, seed: 17, gap: 6 } : { col: K.cream, p: 0.7, draw: pr(t, 1.0, 1.3), seed: 17, gap: 6 }, lo(pr(t, 1.0, 1.25), 17, 5.5));
  part(C, HOUSE.winR, lit2 > 0 ? { col: K.yellow, p: 0.95, draw: lit2, seed: 18, gap: 6 } : { col: K.cream, p: 0.7, draw: pr(t, 1.05, 1.35), seed: 18, gap: 6 }, lo(pr(t, 1.05, 1.3), 18, 5.5));
  line(C.l, [[612, 925], [612, 1000]], lo(pr(t, 1.3, 1.4), 19, 4.5)); line(C.l, [[575, 962], [650, 962]], lo(pr(t, 1.35, 1.45), 20, 4.5));
  if (t > 2.2) fill(C.f, heartPts(440, 968, 1.35), { col: K.pink, p: 1, draw: pr(t, 2.2, 2.45), seed: 21, gap: 3.5, w: 5, over: 1 });
}

function drawGround(t) {
  fill(BG.f, GROUND, { col: K.green, p: 0.9, draw: pr(t, 2.0, 2.8), seed: 30, gap: 8, ang: 1.2 });
  [[150, 1150], [235, 1158], [820, 1152], [930, 1160], [1010, 1150]].forEach(([x, y], i) => { if (t > 2.4 + i * 0.07) { dab(BG.f, x, y - 14, 9, { col: i % 2 ? K.pink : K.yellow, p: 1, seed: 31 + i }); line(BG.l, [[x, y - 4], [x + 2, y + 18]], { col: K.ink, w: 3.5, p: 0.9, seed: 40 + i, draw: 1 }); } });
}

function drawLine(t) {
  POLE.forEach(([x, y0, , y1], i) => line(BG.l, [[x, y0 - 30], [x + 3, y1]], { col: K.brown, w: 10, p: 0.95, seed: 50 + i, draw: pr(t, 3.0 + i * 0.12, 3.35 + i * 0.12) }));
  line(BG.l, LINE_PTS, { col: K.ink, w: 4.5, p: 0.9, seed: 55, draw: pr(t, 3.2, 3.8), taper: 0.05 });
  ITEMS.forEach((it, i) => {
    if (t < it.t) return;
    const top = lineY(it.x) + 2;
    const sway = Math.sin((t - it.t) * 2.4 + i) * 0.035 * Math.exp(-(t - it.t) * 0.4) + (hash(it.seed) - .5) * 0.06;
    const P = xf(it.shape, { x: it.x, y: top, r: sway });
    fill(BG.f, P, { col: it.col, p: 0.92, draw: pr(t, it.t + 0.3, it.t + 0.8), seed: it.seed, gap: 7.5, w: 9, ang: 0.9 });
    line(BG.l, [...P, P[0], P[1]], { col: K.ink, w: 6, p: 0.95, seed: it.seed + 1, draw: pr(t, it.t, it.t + 0.35) });
    // details: heart on the onesie, sash on the dress, star on the tee
    if (t > it.t + 0.75) {
      if (i === 0) fill(BG.f, xf(heartPts(0, 80, 1.6), { x: it.x, y: top, r: sway }), { col: K.pink, p: 1, seed: 70, gap: 3.5, w: 5, over: 1 });
      if (i === 1) fill(BG.f, xf([[-46, 62], [46, 62], [50, 80], [-50, 80]], { x: it.x, y: top, r: sway }), { col: K.peach, p: 1, seed: 71, gap: 4, w: 6, over: 1 });
      if (i === 2) fill(BG.f, xf(starPts(0, 85, 26), { x: it.x, y: top, r: sway }), { col: K.yellow, p: 1, seed: 72, gap: 3.5, w: 5, over: 1 });
    }
    // two pegs
    [-28, 28].forEach((dx, k) => { if (i === 1) dx *= 0.6; const pg = xf([[dx - 6, -12], [dx + 6, -12], [dx + 6, 14], [dx - 6, 14]], { x: it.x, y: top, r: sway }); fill(BG.f, pg, { col: K.brown, p: 1, seed: 80 + i * 2 + k, gap: 3, w: 5, over: 0.5 }); });
  });
}

function drawSky() {
  for (const s of STARS) {
    if (s.big) fill(SKY.f, starPts(s.x, s.y, s.r * 1.9, s.rot), { col: K.white, p: 1, seed: s.seed, gap: 3, w: 5, over: 0.5, boil: 0.3 });
    else dab(SKY.f, s.x, s.y, s.r * 0.6, { col: K.white, p: 1, seed: s.seed, gap: 3, w: 4, over: 0.5, boil: 0.25 });
  }
  // crescent: a disc minus an offset disc
  const out = handCircle(MOON.x, MOON.y, MOON.r, 91, 0, 48).slice(0, 48);
  const cres = out.filter(([x, y]) => Math.hypot(x - (MOON.x + 34), y - (MOON.y - 18)) > MOON.r * 0.86);
  const inner = []; for (let i = 0; i <= 30; i++) { const a = i / 30 * Math.PI * 2; const x = MOON.x + 34 + Math.cos(a) * MOON.r * 0.86, y = MOON.y - 18 + Math.sin(a) * MOON.r * 0.86; if (Math.hypot(x - MOON.x, y - MOON.y) < MOON.r) inner.push([x, y]); }
  fill(SKY.f, moonPoly(), { col: K.white, p: 1, seed: 92, gap: 3.5, w: 6, over: 0.5, boil: 0.3 });
  // the opening hours, in white wax
  arWorld(SKY.f, HOURS.text, HOURS.x, HOURS.y, { size: HOURS.size, col: K.white, p: 0.7, seed: 95, boil: 0.4, weight: 800, stroke: 3 });
}
function moonPoly() {
  const N = 180, C = [MOON.x, MOON.y], r = MOON.r, O = [MOON.x + r * 0.5, MOON.y - r * 0.32], r2 = r * 0.84;
  const ring = (c, rr) => Array.from({ length: N }, (_, i) => { const a = i / N * Math.PI * 2; return [c[0] + Math.cos(a) * rr, c[1] + Math.sin(a) * rr]; });
  const arc = (pts, keep) => { const k = pts.map(keep); let s0 = k.findIndex((v, i) => v && !k[(i - 1 + N) % N]); const out = []; for (let i = 0; i < N; i++) { const j = (s0 + i) % N; if (!k[j]) break; out.push(pts[j]); } return out; };
  const outer = arc(ring(C, r), ([x, y]) => Math.hypot(x - O[0], y - O[1]) > r2);
  let inner = arc(ring(O, r2), ([x, y]) => Math.hypot(x - C[0], y - C[1]) < r);
  const e = outer[outer.length - 1]; if (Math.hypot(inner[0][0] - e[0], inner[0][1] - e[1]) > Math.hypot(inner[inner.length - 1][0] - e[0], inner[inner.length - 1][1] - e[1])) inner = inner.reverse();
  return [...outer, ...inner];
}

function drawWash(t) {
  const g = WASH.g; g.save();
  g.setTransform(CAM.s, 0, 0, CAM.s, W / 2 - CAM.x * CAM.s, H / 2 - CAM.y * CAM.s);
  for (const b of BANDS) {
    if (t < b.t0) continue;
    const f = bandFront(b, t);
    const top = [], bot = [];
    for (let x = X0; x <= X1; x += 40) {
      top.push([x, b.y0 + 10 * (Math.sin(x * 0.006 + b.seed) + 0.6 * Math.sin(x * 0.017 + b.seed * 3)) + 10 * hash(x * 0.37 + b.seed)]);
      bot.push([x, b.y1 + 8 * (Math.sin(x * 0.009 + b.seed * 2) + 0.5 * Math.sin(x * 0.023 + b.seed)) + 6 * hash(x * 0.71 + b.seed)]);
    }
    const frontX = y => f + b.dir * 60 * Math.sin(clamp((y - b.y0) / (b.y1 - b.y0)) * Math.PI) + 10 * Math.sin(y * 0.05);
    g.save(); g.beginPath();
    if (b.dir > 0) { g.moveTo(X0 - 50, b.y0 - 200); for (let y = b.y0 - 200; y <= b.y1 + 200; y += 20) g.lineTo(frontX(y), y); g.lineTo(X0 - 50, b.y1 + 200); }
    else { g.moveTo(X1 + 50, b.y0 - 200); for (let y = b.y0 - 200; y <= b.y1 + 200; y += 20) g.lineTo(frontX(y), y); g.lineTo(X1 + 50, b.y1 + 200); }
    g.closePath(); g.clip();
    const shape = new Path2D(); top.forEach(([x, y], i) => i ? shape.lineTo(x, y) : shape.moveTo(x, y)); for (let i = bot.length - 1; i >= 0; i--) shape.lineTo(bot[i][0], bot[i][1]); shape.closePath();
    g.fillStyle = '#000'; g.globalAlpha = 0.8; g.fill(shape);
    g.save(); g.clip(shape);
    const Rb = mulberry(b.seed * 97);
    for (let k = 0; k < 26; k++) { const y = b.y0 + Rb() * (b.y1 - b.y0); g.globalAlpha = 0.05 + Rb() * 0.07; g.fillRect(X0, y, X1 - X0, 2 + Rb() * 5); }
    if (t < b.t1) { const fx = frontX((b.y0 + b.y1) / 2); g.globalAlpha = 0.22; g.fillRect(b.dir > 0 ? fx - 90 : fx, b.y0 - 40, 90, b.y1 - b.y0 + 80); }
    g.restore(); g.restore();
  }
  g.restore();
}

// title and contact info, drawn on top at the end (after the wash, so they stay bright)
const INFO1 = '@rozahut.bh', INFO2 = 'واتساب 36660824 · عالي، البحرين';
function drawTop(t) {
  arWorld(TOP, 'كوخ روزا', 540, 352, { size: 150, col: K.yellow, p: 1, seed: 100, weight: 800, stroke: 5, reveal: pr(t, 11.25, 12.0) });
  arWorld(TOP, INFO1, 540, 475, { size: 60, col: K.cream, p: 1, seed: 101, weight: 700, ltr: true, stroke: 2, reveal: pr(t, 12.0, 12.6) });
  arWorld(TOP, INFO2, 540, 1500, { size: 46, col: K.ink, p: 1, seed: 102, weight: 700, stroke: 1.5, reveal: pr(t, 11.45, 12.15) });
}

// subtitles = the book's printed words, on a ragged patch of bare paper (screen coords)
const SUB_Y = 1585, SUB_SIZE = 50;
function drawSubs(t) {
  const S = SUBS.find(s => t >= s.t0 && t < s.t1); if (!S) return;
  const rows = S.text.split('\n');
  const rv = clamp((t - S.t0) / (0.35 * rows.length));
  const tw = Math.max(...rows.map(r => measure(r, SUB_SIZE)));
  const hh = rows.length * SUB_SIZE * 1.25;
  const g = SUBK.g; g.save(); g.fillStyle = '#000'; g.beginPath();
  const x0 = 540 - tw / 2 - 34, x1 = 540 + tw / 2 + 34, y0 = SUB_Y - hh / 2 - 18, y1 = SUB_Y + hh / 2 + 14;
  const pts = []; for (let i = 0; i <= 20; i++) pts.push([lerp(x0, x1, i / 20), y0 + (hash(i * 3.1 + S.t0) - .5) * 12]); for (let i = 20; i >= 0; i--) pts.push([lerp(x0, x1, i / 20), y1 + (hash(i * 5.7 + S.t0) - .5) * 12]);
  pts.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); g.closePath(); g.fill(); g.restore();
  rows.forEach((r, i) => arText(SUBT, r, 540, SUB_Y - hh / 2 + SUB_SIZE * 1.02 + i * SUB_SIZE * 1.25, { size: SUB_SIZE, col: K.ink, p: 1, seed: 11 + S.t0 * 3 + i, reveal: clamp(rv * rows.length - i), stroke: 1.2 }));
}

// texts the viewer must read (readcheck); subtitles are checked by their .srt
export const TEXTS = t => {
  const out = []; const box = (id, text, x, y, size, w) => { const s = CAM.s; out.push({ id, text, x0: sx(x) - w * s / 2, y0: sy(y) - size * s, x1: sx(x) + w * s / 2, y1: sy(y) + size * 0.4 * s }); };
  setCam(t);
  if (t >= 7.3) box('hours', HOURS.text, HOURS.x, HOURS.y, HOURS.size, 620);
  if (t >= 11.25) box('title', 'كوخ روزا', 540, 352, 150, 560);
  if (t >= 12.0) box('ig', INFO1, 540, 475, 60, 400);
  if (t >= 11.45) box('wa', INFO2, 540, 1500, 46, 760);
  return out;
};

function setCam(t) { const [x, y, s] = camT(t); CAM.x = x; CAM.y = y; CAM.s = s; }

export function frame(comp, t) {
  setCam(t);
  // calm the boil in the held night shot
  BOIL.amp = t > 9.3 && t < 11 ? 0.55 : 1;
  [SKY.f, SKY.l, BG.f, BG.l, WASH, TOP, SUBK, SUBT].forEach(clear); clearGroup(HS);
  drawSky(); drawGround(t); drawLine(t); drawHouse(t); drawWash(t); drawTop(t); drawSubs(t);
  comp.paperCam(CAM.x * 0.6, CAM.y * 0.6, CAM.s / 0.6);
  comp.begin();
  comp.crayon(SKY.f.c, { gain: 1 });
  comp.crayon(BG.f.c); comp.crayon(BG.l.c);
  if (t > BANDS[0].t0) comp.wash(WASH.c, { color: WASH_COL });
  comp.group(HS);                       // the shop is drawn after the wash: it stays warm and lit at night
  comp.crayon(TOP.c);
  comp.knock(SUBK.c); comp.crayon(SUBT.c);
  comp.finish({ vig: 0.22 });
}
