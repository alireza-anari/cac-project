import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = dirname(fileURLToPath(import.meta.url));
const cli = join(root, 'node_modules/@redocly/cli/bin/cli.js');
const fixture = () => ({
  openapi: '3.1.1', info: { title: 'Synthetic lint fixture', version: '1' },
  security: [],
  paths: { '/items': { get: {
    operationId: 'getItems', summary: 'Get synthetic items',
    responses: {
      '200': { description: 'OK', content: { 'application/json': {
        schema: { type: ['string', 'null'] },
      } } },
      '400': { description: 'Bad request' },
    },
  } } },
});
function lint(doc, profile) {
  const dir = mkdtempSync(join(tmpdir(), 'cac-lint-'));
  try {
    const path = join(dir, 'fixture.json');
    writeFileSync(path, JSON.stringify(doc));
    const config = profile === 'spec' ? ['--config', join(root, 'spec.yaml')] : ['--config', join(root, 'redocly.yaml')];
    const result = spawnSync(process.execPath, [cli, 'lint', path, ...config, '--format', 'json'], {
      encoding: 'utf8', timeout: 60000,
      env: { ...process.env, REDOCLY_TELEMETRY: 'off' },
    });
    assert.ifError(result.error);
    assert.equal(result.signal, null);
    return result;
  } finally { rmSync(dir, { recursive: true, force: true }); }
}
for (const profile of ['spec', 'recommended']) {
  test(`${profile}: accepts OpenAPI 3.1.1 nullable type array`, () => {
    const r = lint(fixture(), profile);
    assert.equal(r.status, 0, r.stdout + r.stderr);
  });
  test(`${profile}: rejects an invalid schema type`, () => {
    const d = fixture();
    d.paths['/items'].get.responses['200'].content['application/json'].schema.type = 'not-a-json-schema-type';
    const r = lint(d, profile);
    assert.equal(r.status, 1, r.stdout + r.stderr);
    assert.match(r.stdout + r.stderr, /struct/);
  });
  test(`${profile}: rejects an unresolved local reference`, () => {
    const d = fixture();
    d.paths['/items'].get.responses['200'].content['application/json'].schema = { $ref: '#/components/schemas/Absent' };
    const r = lint(d, profile);
    assert.equal(r.status, 1, r.stdout + r.stderr);
    assert.match(r.stdout + r.stderr, /no-unresolved-refs/);
  });
  test(`${profile}: rejects duplicate operation IDs`, () => {
    const d = fixture();
    d.paths['/other'] = structuredClone(d.paths['/items']);
    const r = lint(d, profile);
    assert.equal(r.status, 1, r.stdout + r.stderr);
    assert.match(r.stdout + r.stderr, /operation-operationId-unique/);
  });
}
test('recommended: reports missing summary as an error', () => {
  const d = fixture(); delete d.paths['/items'].get.summary;
  const r = lint(d, 'recommended');
  assert.equal(r.status, 1, r.stdout + r.stderr);
  assert.match(r.stdout + r.stderr, /operation-summary/);
});
