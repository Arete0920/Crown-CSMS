import { discoverCrownSurfaceInventory, readInventoryFile } from './crown-surface-discovery.mjs';

function fail(message) {
  console.error(`CROWN DISCOVERED SURFACE COVERAGE FAIL: ${message}`);
  process.exit(1);
}

const discovered = discoverCrownSurfaceInventory();
const inventory = readInventoryFile();

if (!inventory || !Array.isArray(inventory.items)) {
  fail('inventory file missing or malformed');
}

const inventoryByKey = new Map(
  inventory.items.map((item) => [`${item.kind}::${item.path}`, item]),
);

const missing = discovered.items.filter((item) => !inventoryByKey.has(`${item.kind}::${item.path}`));

if (missing.length > 0) {
  const sample = missing.slice(0, 10).map((item) => `${item.kind} ${item.path}`).join('; ');
  fail(`inventory is missing ${missing.length} discovered surfaces. Sample: ${sample}`);
}

const classificationProblems = inventory.items.filter((item) => {
  return item.status === 'unknown' || item.layer === 'unknown' || item.owner === 'unknown' || item.test_status === 'missing';
});

if (classificationProblems.length > 0) {
  console.error(`CROWN DISCOVERED SURFACE COVERAGE FAIL: ${classificationProblems.length} inventory items still need classification`);
  process.exit(1);
}

console.log(`CROWN DISCOVERED SURFACE COVERAGE PASS: ${discovered.items.length} discovered surfaces covered`);
