/**
 * Garde mount SDG — SpatialImpactController (sans navigateur / sans API).
 * Exécution : node tests/unit/test_spatial_impact_sdg_mount_guard.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const assert = require('assert');
const vm = require('vm');

const CONTROLLER = path.resolve(
  __dirname,
  '../../dashboard/modules/decision-experience/spatial-impact-controller.js',
);

function loadController(options = {}) {
  const mountCalls = [];
  const fetchCalls = [];
  const mapStub = { id: 'map' };
  const layerStub = { clearLayers() {} };
  const programCode = Object.prototype.hasOwnProperty.call(options, 'programCode')
    ? options.programCode
    : null;

  const document = {
    querySelector(sel) {
      if (sel === '#dxl-title') return { textContent: '' };
      if (sel === '#dxl-section-impact') {
        return {
          innerHTML: '',
          insertAdjacentHTML() {},
        };
      }
      if (sel === '#dxl-section-why' || sel === '#dxl-section-context') {
        return { innerHTML: '' };
      }
      if (sel === '#dxl-map') {
        return {
          closest() {
            return {
              querySelectorAll() {
                return [];
              },
            };
          },
          before() {},
        };
      }
      if (sel === '#ux-legend-dxl') return null;
      return null;
    },
    createElement(tag) {
      return {
        tagName: tag,
        className: '',
        innerHTML: '',
        textContent: '',
      };
    },
  };

  const SERVICE_LABELS = {
    impact: 'Impact',
    needs: 'Needs',
    explain: 'Explain',
    coverage: 'Coverage',
    decisionCase: 'DecisionCase',
    statistics: 'Statistics',
    map: 'Carte NSME',
  };

  const sandbox = {
    console,
    document,
    location: { protocol: 'http:', hostname: 'localhost' },
    setTimeout,
    fetch() {
      return Promise.reject(new Error('no network in unit test'));
    },
    performance: { now: () => Date.now() },
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;

  sandbox.DxlCore = {
    state: { layer: layerStub, programCode, services: {} },
    SERVICE_LABELS,
    escapeHtml: (v) => String(v ?? ''),
    formatNumber: (v) => String(v ?? ''),
    ensureMap: () => mapStub,
    softErrorHtml: () => '<p>err</p>',
    softLoadingHtml: () => '<p>load</p>',
    emptyService(key) {
      return {
        status: 'loading',
        data: null,
        error: null,
        ms: null,
        url: null,
        httpStatus: null,
        service: key,
        label: SERVICE_LABELS[key] || key,
      };
    },
    async tracedFetch(path, serviceKey) {
      fetchCalls.push({ path, serviceKey });
      return {
        ok: true,
        data: { _stub: serviceKey, asset: { site_name: 'Stub', program_code: 'sites_40' } },
        error: null,
        ms: 1,
        url: path,
        httpStatus: 200,
      };
    },
    renderServicesPanel() {},
    setStatus() {},
    renderExecutiveSummary() {},
    renderImpact() {},
    renderRisks() {},
    renderTraceability() {},
    renderRecommendation() {},
    renderActions() {},
  };

  sandbox.SpatialDecisionGraph = {
    loadAndMount(map, type, assetId, programCode) {
      mountCalls.push({ map, type, assetId, programCode });
      return Promise.resolve({ nodes: [], edges: [] });
    },
  };

  vm.runInNewContext(fs.readFileSync(CONTROLLER, 'utf8'), sandbox, {
    filename: 'spatial-impact-controller.js',
  });

  return {
    ctrl: sandbox.SpatialImpactController,
    mountCalls,
    fetchCalls,
    guard: sandbox.SpatialImpactController._sdgMountGuard,
  };
}

function loadedServices(assetId) {
  const svc = (key, data) => ({
    status: 'loaded',
    data,
    error: null,
    ms: 1,
    url: `/${key}`,
    httpStatus: 200,
    service: key,
    label: key,
  });
  return {
    impact: svc('impact', { impact: {}, asset: { site_name: `Site ${assetId}` } }),
    needs: svc('needs', { asset: { site_name: `Site ${assetId}`, program_code: 'sites_40' }, matches: [] }),
    explain: svc('explain', { summary: 'ok' }),
    coverage: svc('coverage', null),
    decisionCase: svc('decisionCase', { asset: { site_name: `Site ${assetId}`, program_code: 'sites_40' } }),
    statistics: svc('statistics', { matches_total: 0 }),
  };
}

async function testLoadDataOmitsMapFetchKeepsFiveAndSdg() {
  // Sans program_code : comportement historique
  const { ctrl, mountCalls, fetchCalls, guard } = loadController({ programCode: null });
  const gen = guard.startLoadGeneration();
  await ctrl.loadData('site', '41', gen);

  const paths = fetchCalls.map((c) => c.path);
  assert.strictEqual(fetchCalls.length, 5, `attendu 5 fetches, obtenu ${fetchCalls.length}: ${paths.join(', ')}`);
  assert.ok(!paths.some((p) => p.includes('/spatial-matching/map')), 'ne doit plus fetch /spatial-matching/map');
  assert.ok(!paths.some((p) => p.includes('program_code=')), 'sans programCode : aucune URL ne doit l’ajouter');

  const expected = [
    '/api/spatial-matching/assets/41/needs?limit=100',
    '/api/spatial-matching/assets/41/impact',
    '/api/spatial-matching/assets/41/explain',
    '/api/spatial-matching/statistics',
    '/api/decision/case/41?asset_type=site&include_spatial_evidence=false',
  ];
  for (const path of expected) {
    assert.ok(paths.includes(path), `endpoint manquant: ${path}`);
  }
  const casePath = paths.find((p) => p.includes('/api/decision/case/'));
  assert.ok(
    casePath && casePath.includes('include_spatial_evidence=false'),
    `decisionCase doit forcer include_spatial_evidence=false, obtenu: ${casePath}`,
  );
  assert.ok(!casePath.includes('include_spatial_evidence=true'));

  // Rendu carte toujours via SDG (pas via payload NSME map)
  ctrl.renderWorkspace(loadedServices('41'), '41', gen);
  assert.strictEqual(mountCalls.length, 1);
  assert.strictEqual(mountCalls[0].assetId, '41');
  console.log('OK loadData sans program_code: 5 fetches historiques, SDG préservé');
}

async function testLoadDataPropagatesProgramCode() {
  const { ctrl, mountCalls, fetchCalls, guard } = loadController({ programCode: 'sites_40' });
  const gen = guard.startLoadGeneration();
  await ctrl.loadData('site', '30', gen);

  const paths = fetchCalls.map((c) => c.path);
  assert.strictEqual(fetchCalls.length, 5);

  const needs = paths.find((p) => p.includes('/needs'));
  const impact = paths.find((p) => p.includes('/impact'));
  const explain = paths.find((p) => p.includes('/explain'));
  const stats = paths.find((p) => p.includes('/statistics'));
  const decisionCase = paths.find((p) => p.includes('/decision/case/'));

  assert.ok(needs.includes('program_code=sites_40'), `needs: ${needs}`);
  assert.ok(impact.includes('program_code=sites_40'), `impact: ${impact}`);
  assert.ok(explain.includes('program_code=sites_40'), `explain: ${explain}`);
  assert.ok(decisionCase.includes('program_code=sites_40'), `decisionCase: ${decisionCase}`);
  assert.ok(decisionCase.includes('include_spatial_evidence=false'));
  assert.strictEqual(stats, '/api/spatial-matching/statistics', 'statistics inchangé');
  assert.ok(!stats.includes('program_code'));

  // Titre : decisionCase avec même identité programme que SDG
  const services = loadedServices('30');
  services.decisionCase.data.asset.site_name = 'BAKI';
  services.decisionCase.data.asset.program_code = 'sites_40';
  ctrl.renderWorkspace(services, '30', gen);
  assert.strictEqual(mountCalls.length, 1);
  assert.strictEqual(mountCalls[0].assetId, '30');
  assert.strictEqual(mountCalls[0].programCode, 'sites_40');
  console.log('OK loadData avec program_code=sites_40 sur needs/impact/explain/case ; SDG + stats OK');
}

function testSameAssetSixPaintsOneMount() {
  const { ctrl, mountCalls, guard } = loadController();
  const gen = guard.startLoadGeneration();
  const services = loadedServices('41');
  for (let i = 0; i < 6; i += 1) {
    ctrl.renderWorkspace(services, '41', gen);
  }
  assert.strictEqual(mountCalls.length, 1, `attendu 1 mount, obtenu ${mountCalls.length}`);
  assert.strictEqual(mountCalls[0].assetId, '41');
  console.log('OK same-asset 6 paints → 1 mount');
}

function testNewAssetAllowsRemount() {
  const { ctrl, mountCalls, guard } = loadController();
  const gen1 = guard.startLoadGeneration();
  ctrl.renderWorkspace(loadedServices('41'), '41', gen1);
  const gen2 = guard.startLoadGeneration();
  ctrl.renderWorkspace(loadedServices('42'), '42', gen2);
  assert.strictEqual(mountCalls.length, 2);
  assert.strictEqual(mountCalls[0].assetId, '41');
  assert.strictEqual(mountCalls[1].assetId, '42');
  console.log('OK new asset → remount autorisé');
}

function testRetryAllowsRemount() {
  const { ctrl, mountCalls, guard } = loadController();
  const gen1 = guard.startLoadGeneration();
  ctrl.renderWorkspace(loadedServices('41'), '41', gen1);
  // retry explicite = nouveau load() = nouvelle génération
  const gen2 = guard.startLoadGeneration();
  ctrl.renderWorkspace(loadedServices('41'), '41', gen2);
  assert.strictEqual(mountCalls.length, 2);
  assert.ok(mountCalls.every((c) => c.assetId === '41'));
  console.log('OK retry → remount autorisé');
}

function testStaleGenerationBlocked() {
  const { ctrl, mountCalls, guard } = loadController();
  const staleGen = guard.startLoadGeneration();
  const activeGen = guard.startLoadGeneration();
  // Génération active monte une fois
  ctrl.renderWorkspace(loadedServices('42'), '42', activeGen);
  // Réponse tardive de l’ancienne génération
  ctrl.renderWorkspace(loadedServices('41'), '41', staleGen);
  ctrl.renderWorkspace(loadedServices('41'), '41', staleGen);
  assert.strictEqual(mountCalls.length, 1);
  assert.strictEqual(mountCalls[0].assetId, '42');
  assert.strictEqual(guard.claimSdgMount(staleGen), false);
  console.log('OK stale generation → SDG non redéclenché');
}

async function main() {
  testSameAssetSixPaintsOneMount();
  testNewAssetAllowsRemount();
  testRetryAllowsRemount();
  testStaleGenerationBlocked();
  await testLoadDataOmitsMapFetchKeepsFiveAndSdg();
  await testLoadDataPropagatesProgramCode();
  console.log('ALL PASSED');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
