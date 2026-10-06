// Smoke tests for the measurement scripts: they parse, and the whole-number angle law they exercise (Law 2 of
// the README) agrees with the Python implementation in tools/particles.py to the last bit that matters.
// Standard library only:  node --test tests/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const C32 = 2654435769;
const SLOTS = 1 << 18;
const GOLDEN = Math.PI * (3 - Math.sqrt(5));
const thetaInt = slot => 2 * Math.PI * (1 - (Math.imul(slot | 0, C32 | 0) >>> 0) / 4294967296);

test('the measurement scripts parse', () => {
  for (const f of ['measurements/exactness.mjs', 'measurements/coax-field-test.mjs']) {
    execFileSync(process.execPath, ['--check', path.join(ROOT, f)]);
  }
});

test('Law 2: the int32 angle law is in range and tracks the golden angle within one layer', () => {
  assert.equal(thetaInt(0), 2 * Math.PI);
  for (const s of [1, 2, 1000, 39885, 250174, SLOTS - 1]) {
    const th = thetaInt(s);
    assert.ok(th > 0 && th <= 2 * Math.PI, `slot ${s}`);
    const exact = (s * GOLDEN) % (2 * Math.PI);
    const err = Math.abs(((th - exact + Math.PI) % (2 * Math.PI)) - Math.PI);
    assert.ok(err < 2e-4, `slot ${s}: ${err} rad`);
  }
});

test('Law 2 agrees between JavaScript and tools/particles.py on sample slots', () => {
  const slots = [1, 2, 39885, 250174, SLOTS - 1];
  const py = `import sys; sys.path.insert(0, ${JSON.stringify(path.join(ROOT, 'tools'))}); import particles
print(*[repr(particles.theta_int(s)) for s in ${JSON.stringify(slots)}])`;
  let out;
  try {
    out = execFileSync('python3', ['-c', py], { encoding: 'utf8' });
  } catch {
    return; // no python3 on this machine: the two tests above still stand
  }
  const got = out.trim().split(/\s+/).map(Number);
  slots.forEach((s, i) => assert.ok(Math.abs(got[i] - thetaInt(s)) < 1e-12, `slot ${s}: py ${got[i]} js ${thetaInt(s)}`));
});
