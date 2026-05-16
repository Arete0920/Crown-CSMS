import { discoverCrownSurfaceInventory, writeInventoryFile } from './crown-surface-discovery.mjs';

const inventory = discoverCrownSurfaceInventory();
const inventoryPath = writeInventoryFile(inventory);

console.log(`CROWN TEST INVENTORY WRITTEN: ${inventoryPath}`);
console.log(JSON.stringify(inventory.summary, null, 2));
