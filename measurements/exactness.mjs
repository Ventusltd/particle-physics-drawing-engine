/* 03-exactness.mjs: test T2 of the 2030 stone, actually run.
   Truth is computed in 256-bit fixed point with BigInt: theta_true = 2*pi*frac(key*(3-sqrt5)/2).
   Each law's angle is converted EXACTLY (no rounding) to the same fixed point and compared on the circle. */
const B = 256n, ONE = 1n << B;
const isqrt = v => { let x = 1n << 300n; for (;;) { const y = (x + v / x) >> 1n; if (y >= x) return x; x = y; } };
const SQRT5 = isqrt(5n * ONE * ONE);                               /* sqrt(5) * 2^256 */
const INV_PHI2 = (3n * ONE - SQRT5) / 2n;                          /* (3 - sqrt5)/2 = 1/phi^2 */
const PI = BigInt('3141592653589793238462643383279502884197169399375105820974944592307816406286') * ONE / (10n ** 75n);
const TAU = 2n * PI;
const mod = (a, m) => ((a % m) + m) % m;
const fixOfDouble = d => { const dv = new DataView(new ArrayBuffer(8)); dv.setFloat64(0, d); const hi = dv.getUint32(0), lo = dv.getUint32(4); const e = (hi >>> 20) & 0x7ff; const m = (BigInt(hi & 0xfffff) << 32n) | BigInt(lo); const mant = e ? m | (1n << 52n) : m; const sh = BigInt((e || 1) - 1075) + B; const v = sh >= 0n ? mant << sh : mant >> -sh; return hi >>> 31 ? -v : v; };
const num = v => Number(v * (1n << 80n) / ONE) / 2 ** 80;          /* fixed point -> double, for printing small differences */
const wrap = v => { let d = mod(v, TAU); if (d > PI) d -= TAU; return num(d); };
const thetaTrue = k => (mod(BigInt(k) * INV_PHI2, ONE) * TAU) >> B;

const GOLDEN = Math.PI * (3 - Math.sqrt(5));
const G32 = Math.fround(GOLDEN);
const C32 = 2654435769;                     /* floor(2^32/phi), the stone's constant */
const C64 = 11400714819323198485n;          /* floor(2^64/phi) */
const RIM_PX = 1000;
const px = d => 2 * RIM_PX * Math.abs(Math.sin(d / 2));            /* chord at the rim of a 1,000-px-radius view */

console.log(`GOLDEN (f64) = ${GOLDEN}; exact golden angle - GOLDEN = ${num(((INV_PHI2 * TAU) >> B) - fixOfDouble(GOLDEN)).toExponential(3)} rad`);
console.log(`fround(GOLDEN) = ${G32}; fround(GOLDEN) - GOLDEN = ${(G32 - GOLDEN).toExponential(3)} rad per key`);
console.log(`prose constant 2.39996 - GOLDEN = ${(2.39996 - GOLDEN).toExponential(4)} rad per key; at key 250174: ${((2.39996 - GOLDEN) * 250174).toFixed(4)} rad`);
console.log(`2^32/phi = ${num((ONE * (1n << 32n) * 2n * ONE) / (ONE + SQRT5) )}; C32 = ${C32}; truncation = ${num((ONE * (1n << 32n) * 2n * ONE) / (ONE + SQRT5) - BigInt(C32) * ONE).toFixed(6)} of one unit in 2^32`);
const perSlot = num(((ONE * (1n << 32n) * 2n * ONE) / (ONE + SQRT5) - BigInt(C32) * ONE) * TAU >> (B + 32n));
console.log(`=> the whole-number law drifts from the true golden angle by ${perSlot.toExponential(4)} rad per slot (predicted)`);

const intFrac32 = k => (Math.imul(k | 0, C32 | 0) >>> 0);
function row(k) {
  const T = thetaTrue(k);
  const t64 = k * GOLDEN, t32 = Math.fround(Math.fround(k) * G32);
  const u = intFrac32(k);                                          /* frac(k/phi) * 2^32, exact integer */
  const thInt = ((ONE - (BigInt(u) << (B - 32n))) * TAU) >> B;      /* 2*pi*(1 - frac), exact */
  const thIntNo = ((BigInt(u) << (B - 32n)) * TAU) >> B;            /* 2*pi*frac: is it the mirror image? */
  const u64 = (BigInt(k) * C64) & ((1n << 64n) - 1n);
  const thInt64 = ((ONE - (u64 << (B - 64n))) * TAU) >> B;
  const thShader = Math.fround(Math.fround(6.283185307179586) * Math.fround(1 - u / 4294967296)); /* the int law finished in float32 */
  const e64 = wrap(fixOfDouble(t64) - T), e32 = wrap(fixOfDouble(t32) - T), eI = wrap(thInt - T), eI64 = wrap(thInt64 - T), eSh = wrap(fixOfDouble(thShader) - T);
  const mirror = wrap(thIntNo + T);
  return { key: k, 'f64 err rad': e64.toExponential(3), 'f64 px': px(e64).toExponential(2), 'f32 err rad': e32.toExponential(3), 'f32 px': px(e32).toFixed(3), 'int32 law err rad': eI.toExponential(3), 'int32 px': px(eI).toFixed(4), 'int32 law finished in f32, px': px(eSh).toFixed(4), 'int64 law err rad': eI64.toExponential(3), 'mirror test (2pi*frac + true) rad': mirror.toExponential(3), 'f32 ulp of product rad': (() => { const a = Math.abs(t32); let s = 1; while (Math.fround(a + s) !== a && s > 1e-12) s /= 2; return (s * 2); })() };
}
const KEYS = [1, 250174, 262143, 2 ** 24, 2 ** 31];
const rows = KEYS.map(row); console.table(rows);
console.log(`keys examined in the table: ${rows.length}`);

/* every slot of one 2^18 layer: worst disagreement between the int32 law and the running f64 law */
let worst = 0, at = 0, cnt = 0; for (let s = 1; s < 262144; s++) { const u = intFrac32(s); const a = 2 * Math.PI * (1 - u / 4294967296), b = s * GOLDEN; let d = (a - b) % (2 * Math.PI); if (d > Math.PI) d -= 2 * Math.PI; if (d < -Math.PI) d += 2 * Math.PI; if (Math.abs(d) > worst) { worst = Math.abs(d); at = s; } cnt++; }
console.log(`one layer: ${cnt} slots examined; worst |int32 law - f64 law| = ${worst.toExponential(4)} rad at slot ${at} = ${px(worst).toFixed(4)} px at a 1,000-px rim`);

/* the 64-bit constant with only 32-bit operations (what a WebGL2 shader can do): 16-bit limbs */
function mulhi32(a, b) { const a0 = a & 0xffff, a1 = a >>> 16, b0 = b & 0xffff, b1 = b >>> 16; const p00 = a0 * b0, p01 = a0 * b1, p10 = a1 * b0, p11 = a1 * b1; const mid = (p00 >>> 16) + (p01 & 0xffff) + (p10 & 0xffff); return (p11 + (p01 >>> 16) + (p10 >>> 16) + (mid >>> 16)) >>> 0; }
const CHI = Number(C64 >> 32n), CLO = Number(C64 & 0xffffffffn);
const top32 = s => ((Math.imul(s, CHI | 0) >>> 0) + mulhi32(s >>> 0, CLO)) >>> 0;
let bad = 0, tested = 0; for (let i = 0; i < 1000000; i++) { const s = (Math.imul(i, 2246822519) >>> 0); const want = Number(((BigInt(s) * C64) & ((1n << 64n) - 1n)) >> 32n); if (top32(s) !== want) bad++; tested++; }
console.log(`limb law: ${tested} slots examined across 0..2^32, top 32 bits of slot*C64 mod 2^64 by 16-bit limbs disagree with BigInt on ${bad}`);

/* continued fraction of C32/2^32: how long does it stay golden? */
{ let a = BigInt(C32), b = 1n << 32n, q = [], h0 = 0n, h1 = 1n, k0 = 1n, k1 = 0n, firstBad = -1, den = 0n; while (b) { const t = a / b; q.push(t); [h0, h1] = [h1, t * h1 + h0]; [k0, k1] = [k1, t * k1 + k0]; if (q.length > 1 && t !== 1n && firstBad < 0) { firstBad = q.length - 1; den = k0; } [a, b] = [b, a % b]; }
  console.log(`continued fraction of C32/2^32: ${q.length} terms: [${q.join(',')}]`);
  console.log(`first term that is not 1 is term ${firstBad}; the last all-golden convergent has denominator ${den}. Neighbours in the spiral are about 2*sqrt(pi*k) keys apart, so the lattice stops being golden near k = ${(Number(den) ** 2 / (4 * Math.PI)).toExponential(2)}`); }

/* packing far out: a thin sector of the annulus starting at key K, three laws */
function sector(K, law) {
  const SPAN = 8000000, HALF = 0.004, pts = [];
  const r0 = Math.sqrt(K), r1 = Math.sqrt(K + SPAN);
  for (let k = K; k < K + SPAN; k++) { let t; if (law === 'f64') t = (k * GOLDEN) % (2 * Math.PI); else if (law === 'f32') t = Math.fround(Math.fround(k) * G32) % (2 * Math.PI); else t = 2 * Math.PI * (1 - intFrac32(k) / 4294967296); if (t > Math.PI) t -= 2 * Math.PI; if (Math.abs(t) < HALF) { const r = Math.sqrt(k); pts.push(r * Math.cos(t) - r0, r * Math.sin(t)); } }
  const m = pts.length / 2, H = HALF * r0; let mn = Infinity, inner = 0; const nn = [];
  for (let i = 0; i < m; i++) { const x = pts[2 * i], y = pts[2 * i + 1]; if (x < 4 || x > r1 - r0 - 4 || Math.abs(y) > H - 4) continue; let b = Infinity; for (let j = 0; j < m; j++) if (j !== i) { const d = (pts[2 * j] - x) ** 2 + (pts[2 * j + 1] - y) ** 2; if (d < b) b = d; } nn.push(Math.sqrt(b)); inner++; }
  nn.sort((a, b) => a - b); return { K, law, inSector: m, interiorExamined: inner, nnMin: nn.length ? +nn[0].toFixed(4) : null, nnMedian: nn.length ? +nn[nn.length >> 1].toFixed(4) : null };
}
const sec = []; for (const K of [2 ** 18, 2 ** 24, 2 ** 28, 2 ** 31]) for (const law of ['f64', 'int32', 'f32']) sec.push(sector(K, law));
console.table(sec);
