import { readInventoryFile } from './crown-surface-discovery.mjs';

function fail(message) {
  console.error(`CROWN TEST INVENTORY FAIL: ${message}`);
  process.exit(1);
}

const inventory = readInventoryFile();
if (!inventory) {
  fail('docs/testing/crown-test-inventory.json is missing');
}

if (!Array.isArray(inventory.items)) {
  fail('inventory.items must be an array');
}

for (const [index, item] of inventory.items.entries()) {
  for (const field of ['kind', 'path', 'status', 'layer', 'owner', 'test_status', 'notes']) {
    if (!Object.prototype.hasOwnProperty.call(item, field)) {
      fail(`item ${index} is missing required field ${field}`);
    }
  }

  if (typeof item.release_blocking !== 'boolean') {
    fail(`item ${index} must include boolean release_blocking`);
  }
}

console.log(`CROWN TEST INVENTORY PASS: ${inventory.items.length} items`);
