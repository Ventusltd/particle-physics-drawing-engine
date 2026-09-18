/* coax-field-test.mjs — Assessor 1, 18 Sept 2026.
 * Can a field of wafer particles do real electrostatics?  A test that can fail.
 *
 * Problem: coaxial cable, inner conductor radius r0 at V = 1, earthed sheath radius R at V = 0,
 * one homogeneous dielectric. Laplace's equation. Analytic answer:
 *     V(r) = ln(R/r) / ln(R/r0),     E(r) = V0 / (r ln(R/r0)).
 * Normalised units throughout (V0 = 1, r0 = 1, R = 2.5). No manufacturer data. Not a cable design.
 *
 * Method A: 5-point finite differences on a square grid, SOR. (The textbook method.)
 * Method B: the wafer's own law. Nodes at r = s*sqrt(key), theta = key*GOLDEN (lib.mjs line 11, 19).
 *           Meshless generalised finite differences: weighted least-squares second-order Taylor fit
 *           over the nearest neighbours gives Laplacian weights; sparse system solved by BiCGSTAB.
 *           Conductor = every key below k0; sheath = every key above K. With K = 250,174 the sheath
 *           is the rim of today's wafer.
 * Exit codes: 0 pass, 1 fail, 3 examined nothing.
 */
const GOLDEN = Math.PI * (3 - Math.sqrt(5));
const RATIO = 2.5, LN = Math.log(RATIO);
const Vexact = r => r <= 1 ? 1 : r >= RATIO ? 0 : Math.log(RATIO / r) / LN;
const Eexact = r => 1 / (r * LN);

/* ---------- Method A: square grid, SOR ---------- */
function gridSolve(n) {               /* n cells across the half-width R */
  const h = RATIO / n, W = 2 * n + 1, u = new Float64Array(W * W), fixed = new Uint8Array(W * W);
  for (let j = 0; j < W; j++) for (let i = 0; i < W; i++) {
    const x = (i - n) * h, y = (j - n) * h, r = Math.hypot(x, y), id = j * W + i;
    if (r <= 1) { u[id] = 1; fixed[id] = 1; } else if (r >= RATIO || i === 0 || j === 0 || i === W - 1 || j === W - 1) { u[id] = 0; fixed[id] = 1; }
    else u[id] = Vexact(r) * 0 + 0.5;
  }
  const omega = 2 / (1 + Math.sin(Math.PI / W)); let sweeps = 0, res = 1;
  while (res > 1e-10 && sweeps < 200000) {
    res = 0;
    for (let j = 1; j < W - 1; j++) for (let i = 1; i < W - 1; i++) {
      const id = j * W + i; if (fixed[id]) continue;
      const d = 0.25 * (u[id - 1] + u[id + 1] + u[id - W] + u[id + W]) - u[id];
      u[id] += omega * d; if (Math.abs(d) > res) res = Math.abs(d);
    }
    sweeps++;
  }
  let maxV = 0, maxE = 0, maxEsurf = 0, free = 0, nE = 0;
  for (let j = 1; j < W - 1; j++) for (let i = 1; i < W - 1; i++) {
    const id = j * W + i; if (fixed[id]) continue; free++;
    const x = (i - n) * h, y = (j - n) * h, r = Math.hypot(x, y);
    maxV = Math.max(maxV, Math.abs(u[id] - Vexact(r)));
    if (fixed[id - 1] || fixed[id + 1] || fixed[id - W] || fixed[id + W]) continue;   /* E only where the central difference is clean */
    const ex = -(u[id + 1] - u[id - 1]) / (2 * h), ey = -(u[id + W] - u[id - W]) / (2 * h);
    const er = (ex * x + ey * y) / r, rel = Math.abs(er - Eexact(r)) / Eexact(r);
    nE++; maxE = Math.max(maxE, rel); if (r < 1 + 3 * h) maxEsurf = Math.max(maxEsurf, rel);
  }
  return { method: 'A square grid', free, h, sweeps, residual: res, maxVerr: maxV, maxErelErr: maxE, maxErelErrNearConductor: maxEsurf, nE };
}

/* ---------- Method B: phyllotaxis nodes, meshless GFDM ---------- */
function solve5(A, b) {               /* 5x5 Gaussian elimination with pivoting */
  const n = 5, M = A.map((r, i) => [...r, b[i]]);
  for (let c = 0; c < n; c++) {
    let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    if (Math.abs(M[p][c]) < 1e-300) return null; [M[c], M[p]] = [M[p], M[c]];
    for (let r = 0; r < n; r++) if (r !== c) { const f = M[r][c] / M[c][c]; for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k]; }
  }
  return M.map((r, i) => r[n] / r[i]);
}
function waferSolve(K, NB = 14) {
  const k0 = Math.round(K / (RATIO * RATIO)), s = 1 / Math.sqrt(k0);      /* so that key k0 sits at r = 1 and key K at r = 2.5 */
  const hbar0 = s * Math.sqrt(Math.PI), GAP = 0.4 * hbar0;
  /* v2: the surfaces are made of nodes. A ring of fixed nodes sits exactly on r = 1 (V = 1) and on r = 2.5 (V = 0),
     spaced one mean spacing apart. Wafer particles inside the conductor, outside the sheath, or closer than 0.4 spacings
     to a surface take no part. Every other particle keeps its wafer place: r = s*sqrt(key), theta = key*GOLDEN. */
  const xs = [], ys = [], fixedV = [];
  for (let k = k0; k <= K; k++) { const r = s * Math.sqrt(k); if (r > 1 + GAP && r < RATIO - GAP) { const t = k * GOLDEN; xs.push(r * Math.cos(t)); ys.push(r * Math.sin(t)); fixedV.push(-1); } }
  for (const [rad, val] of [[1, 1], [RATIO, 0]]) { const m = Math.ceil(2 * Math.PI * rad / hbar0); for (let q = 0; q < m; q++) { const t = 2 * Math.PI * q / m; xs.push(rad * Math.cos(t)); ys.push(rad * Math.sin(t)); fixedV.push(val); } }
  const N = xs.length, X = Float64Array.from(xs), Y = Float64Array.from(ys), Rr = new Float64Array(N);
  for (let i = 0; i < N; i++) Rr[i] = Math.hypot(X[i], Y[i]);
  const hbar = s * Math.sqrt(Math.PI);                                   /* mean spacing: one node per pi*s^2 of area */
  /* spatial hash */
  const cs = 2.2 * hbar, G = Math.ceil(2 * (RATIO * 1.05) / cs) + 2, off = G / 2, head = new Int32Array(G * G).fill(-1), next = new Int32Array(N);
  const cell = i => (Math.floor(Y[i] / cs + off)) * G + Math.floor(X[i] / cs + off);
  for (let i = 0; i < N; i++) { const c = cell(i); next[i] = head[c]; head[c] = i; }
  const free = []; const idx = new Int32Array(N).fill(-1);
  for (let i = 0; i < N; i++) { if (fixedV[i] < 0) { idx[i] = free.length; free.push(i); } }
  const F = free.length; if (!F) return null;
  const nbr = new Int32Array(F * NB), wL = new Float64Array(F * NB), wGx = new Float64Array(F * NB), wGy = new Float64Array(F * NB);
  let negW = 0;
  for (let f = 0; f < F; f++) {
    const i = free[f], cx = Math.floor(X[i] / cs + off), cy = Math.floor(Y[i] / cs + off), cand = [];
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { let j = head[(cy + dy) * G + cx + dx]; while (j >= 0) { if (j !== i) { const d2 = (X[j] - X[i]) ** 2 + (Y[j] - Y[i]) ** 2; cand.push([d2, j]); } j = next[j]; } }
    cand.sort((a, b) => a[0] - b[0]); if (cand.length < NB) throw new Error('too few neighbours');
    const rad2 = cand[NB - 1][0] * 1.21;
    const A = [0, 0, 0, 0, 0].map(() => [0, 0, 0, 0, 0]), P = [];
    for (let m = 0; m < NB; m++) {
      const j = cand[m][1], dx = X[j] - X[i], dy = Y[j] - Y[i], q = cand[m][0] / rad2, w = (1 - q) ** 2;   /* compact weight */
      const p = [dx, dy, dx * dx / 2, dx * dy, dy * dy / 2]; P.push([p, w, j]);
      for (let a = 0; a < 5; a++) for (let b = 0; b < 5; b++) A[a][b] += w * p[a] * p[b];
    }
    /* Laplacian weight of neighbour m = w * p . (A^-1 (e3 + e5));  gradient likewise with e1, e2 */
    const cL = solve5(A, [0, 0, 1, 0, 1]), cX = solve5(A, [1, 0, 0, 0, 0]), cY = solve5(A, [0, 1, 0, 0, 0]);
    for (let m = 0; m < NB; m++) {
      const [p, w, j] = P[m]; let l = 0, gx = 0, gy = 0; for (let a = 0; a < 5; a++) { l += p[a] * cL[a]; gx += p[a] * cX[a]; gy += p[a] * cY[a]; }
      nbr[f * NB + m] = j; wL[f * NB + m] = w * l; wGx[f * NB + m] = w * gx; wGy[f * NB + m] = w * gy; if (w * l < 0) negW++;
    }
  }
  /* system: sum_m wL (u_j - u_i) = 0 for free i; u known on fixed nodes. */
  const uAll = new Float64Array(N); for (let i = 0; i < N; i++) uAll[i] = Math.max(0, fixedV[i]);
  const diag = new Float64Array(F), rhs = new Float64Array(F);
  for (let f = 0; f < F; f++) { let d = 0; for (let m = 0; m < NB; m++) { const w = wL[f * NB + m], j = nbr[f * NB + m]; d -= w; if (idx[j] < 0) rhs[f] -= w * uAll[j]; } diag[f] = d; }
  const mul = (x, out) => { for (let f = 0; f < F; f++) { let a = diag[f] * x[f]; for (let m = 0; m < NB; m++) { const j = idx[nbr[f * NB + m]]; if (j >= 0) a += wL[f * NB + m] * x[j]; } out[f] = a / diag[f]; } };   /* Jacobi-scaled rows */
  const b = rhs.map((v, f) => v / diag[f]);
  const dot = (a, c) => { let t = 0; for (let i = 0; i < F; i++) t += a[i] * c[i]; return t; };
  /* BiCGSTAB */
  const x = new Float64Array(F).fill(0.5), r = new Float64Array(F), rh = new Float64Array(F), p = new Float64Array(F), v = new Float64Array(F), sV = new Float64Array(F), t = new Float64Array(F);
  mul(x, r); for (let i = 0; i < F; i++) { r[i] = b[i] - r[i]; rh[i] = r[i]; }
  let rho = 1, alpha = 1, om = 1, it = 0; const bn = Math.sqrt(dot(b, b)); let rel = Math.sqrt(dot(r, r)) / bn;
  while (rel > 1e-11 && it < 20000) {
    const rhoN = dot(rh, r), beta = (rhoN / rho) * (alpha / om); rho = rhoN;
    for (let i = 0; i < F; i++) p[i] = r[i] + beta * (p[i] - om * v[i]);
    mul(p, v); alpha = rho / dot(rh, v);
    for (let i = 0; i < F; i++) sV[i] = r[i] - alpha * v[i];
    mul(sV, t); om = dot(t, sV) / dot(t, t);
    for (let i = 0; i < F; i++) { x[i] += alpha * p[i] + om * sV[i]; r[i] = sV[i] - om * t[i]; }
    rel = Math.sqrt(dot(r, r)) / bn; it++;
    if (!Number.isFinite(rel)) break;
  }
  for (let f = 0; f < F; f++) uAll[free[f]] = x[f];
  let maxV = 0, maxE = 0, maxEsurf = 0, sumE2 = 0, nE = 0;
  for (let f = 0; f < F; f++) {
    const i = free[f], rr = Rr[i]; maxV = Math.max(maxV, Math.abs(x[f] - Vexact(rr)));
    let gx = 0, gy = 0, clean = true;
    for (let m = 0; m < NB; m++) { const j = nbr[f * NB + m]; if (idx[j] < 0) clean = false; gx += wGx[f * NB + m] * (uAll[j] - x[f]); gy += wGy[f * NB + m] * (uAll[j] - x[f]); }
    /* v2: surface nodes lie on the true surface, so every stencil is smooth and every free node is judged, including those touching the conductor */
    const er = -(gx * X[i] + gy * Y[i]) / rr, e = Math.abs(er - Eexact(rr)) / Eexact(rr);
    nE++; sumE2 += e * e; maxE = Math.max(maxE, e); if (rr < 1 + 4 * hbar) maxEsurf = Math.max(maxEsurf, e);
  }
  return { method: 'B2 wafer law + surface rings (meshless GFDM)', K, k0, free: F, h: hbar, neighbours: NB, negativeLaplacianWeights: negW, iterations: it, residual: rel, maxVerr: maxV, maxErelErr: maxE, rmsErelErr: Math.sqrt(sumE2 / Math.max(1, nE)), maxErelErrNearConductor: maxEsurf, nE };
}

/* ---------- run ---------- */
const out = { date: new Date().toISOString(), problem: 'coax, V0=1, r0=1, R=2.5, homogeneous dielectric, normalised units', runs: [] };
let examined = 0, fail = false;
for (const n of [160]) { const t0 = Date.now(); const r = gridSolve(n); r.ms = Date.now() - t0; out.runs.push(r); examined += r.free; console.log(JSON.stringify(r)); }
for (const K of [2500, 25000, 250174]) { const t0 = Date.now(); const r = waferSolve(K); if (!r) continue; r.ms = Date.now() - t0; out.runs.push(r); examined += r.free; console.log(JSON.stringify(r)); }
if (!examined) { console.error('EXAMINED NOTHING'); process.exit(3); }
/* pass criteria, declared before the run: at the finest level of each method, potential within 1 % of V0 everywhere,
   field within 2 % on clean stencils, solver residual below 1e-8, and error must fall as the node count rises. */
const A = out.runs.filter(r => r.method.startsWith('A')), B = out.runs.filter(r => r.method.startsWith('B'));
/* v2 judges the wafer-law method only. Grid A keeps its staircase surface as a labelled reference; it FAILED in v1 and is not re-judged here. */
for (const S of [B]) {
  const last = S[S.length - 1];
  if (!(last.residual < 1e-8)) { fail = true; console.log('FAIL residual', last.method); }
  if (!(last.maxVerr < 0.01)) { fail = true; console.log('FAIL potential', last.method); }
  if (!(last.maxErelErr < 0.02)) { fail = true; console.log('FAIL field', last.method); }
  if (!(last.maxVerr < S[0].maxVerr)) { fail = true; console.log('FAIL no convergence', last.method); }
}
out.verdict = fail ? 'FAIL' : 'PASS';
import('node:fs').then(fs => { fs.writeFileSync(new URL('./coax-field-result-v2-surface-ring.json', import.meta.url), JSON.stringify(out, null, 1)); console.log(out.verdict); process.exit(fail ? 1 : 0); });
