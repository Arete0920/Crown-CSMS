import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, '..', '..');

const ROOT_SKIP = new Set(['.git', '.venv', 'venv', '.pytest_cache', '__pycache__', 'node_modules', 'dist', 'build', '.mypy_cache', '.ruff_cache']);
const BACKEND_SKIP = new Set(['tests', 'quarantine_old_tests', 'scripts', 'scripts_old', 'migrations', 'signals', 'integrations_real', '__pycache__']);
const WIZARD_SKIP_NAME = /(test|spec|story|mock|fixture|sample|log|csv)$/i;
const COMPONENT_SKIP_NAME = /(^index$|^types$|^constants$|^helpers$|^utils$|test|spec|story|mock)/i;

function walkDir(dirPath) {
  const results = [];
  if (!fs.existsSync(dirPath)) {
    return results;
  }

  for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {
    if (entry.name.startsWith('.') && entry.name !== '.github') {
      continue;
    }
    const fullPath = path.join(dirPath, entry.name);
    if (entry.isDirectory()) {
      results.push(...walkDir(fullPath));
      continue;
    }
    results.push(fullPath);
  }

  return results;
}

function toRepoPath(fullPath) {
  return path.relative(root, fullPath).split(path.sep).join('/');
}

function fileExists(fullPath) {
  try {
    return fs.statSync(fullPath).isFile();
  } catch {
    return false;
  }
}

function discoverBackendModuleDirectories() {
  const backendRoot = path.join(root, 'backend');
  if (!fs.existsSync(backendRoot)) {
    return [];
  }

  const entries = [];
  for (const entry of fs.readdirSync(backendRoot, { withFileTypes: true })) {
    if (!entry.isDirectory() || BACKEND_SKIP.has(entry.name) || entry.name.startsWith('_')) {
      continue;
    }

    const fullPath = path.join(backendRoot, entry.name);
    const hasPython = walkDir(fullPath).some((candidate) => candidate.endsWith('.py'));
    if (hasPython) {
      entries.push({
        kind: 'backend_module_directory',
        name: entry.name,
        path: toRepoPath(fullPath),
        status: 'unknown',
        layer: 'module',
        owner: 'unknown',
        test_status: 'missing',
        release_blocking: true,
        notes: 'Auto-generated from discovered repository surface; requires owner classification.',
      });
    }
  }

  return entries;
}

function createInventoryItem(kind, fullPath, layer) {
  return {
    kind,
    name: path.basename(fullPath),
    path: toRepoPath(fullPath),
    status: 'unknown',
    layer,
    owner: 'unknown',
    test_status: 'missing',
    release_blocking: true,
    notes: 'Auto-generated from discovered repository surface; requires owner classification.',
  };
}

function addWizardFileCandidate(candidates, fullPath, layer = 'addon') {
  candidates.push(createInventoryItem('wizard_like_file', fullPath, layer));
}

function shouldIncludeWizardReleaseDoc(fullPath) {
  const repoPath = toRepoPath(fullPath);
  const basename = path.basename(fullPath);
  if (!/\.(md|json|csv|txt|yml|yaml|ps1|py|js|jsx|ts|tsx)$/i.test(repoPath)) {
    return false;
  }
  if (basename === 'README.md') {
    return false;
  }
  const content = fs.readFileSync(fullPath, 'utf8');
  return repoPath.toLowerCase().includes('wizard') || content.toLowerCase().includes('wizard');
}

function shouldIncludeWizardCodeFile(fullPath) {
  const repoPath = toRepoPath(fullPath);
  const lowered = repoPath.toLowerCase();
  const basename = path.basename(fullPath);
  const underWizardSurface = repoPath.split('/').some((segment) => segment.toLowerCase().endsWith('_wizard') || segment.toLowerCase() === 'wizards');
  if (!underWizardSurface) {
    return false;
  }
  if (!/\.(py|js|jsx|ts|tsx|mjs|cjs|md|json|ps1|txt|yml|yaml)$/i.test(repoPath)) {
    return false;
  }
  if (WIZARD_SKIP_NAME.test(basename) || lowered.includes('/node_modules/') || lowered.includes('/.venv/') || lowered.includes('/venv/')) {
    return false;
  }
  return true;
}

function discoverWizardLikeFiles() {
  const candidates = [];

  for (const fullPath of walkDir(root)) {
    const repoPath = toRepoPath(fullPath);
    const lowered = repoPath.toLowerCase();

    if (lowered.includes('/docs/release/') || lowered.startsWith('docs/release/')) {
      if (!shouldIncludeWizardReleaseDoc(fullPath)) {
        continue;
      }
      addWizardFileCandidate(candidates, fullPath, 'addon');
      continue;
    }

    if (!shouldIncludeWizardCodeFile(fullPath)) {
      continue;
    }

    addWizardFileCandidate(candidates, fullPath, 'addon');
  }

  return candidates;
}

function discoverFrontendComponentFiles() {
  const roots = [path.join(root, 'frontend')];
  const candidates = [];

  for (const baseRoot of roots) {
    if (!fs.existsSync(baseRoot)) {
      continue;
    }

    for (const fullPath of walkDir(baseRoot)) {
      const repoPath = toRepoPath(fullPath);
      const lowered = repoPath.toLowerCase();
      const extOk = /\.(js|jsx|ts|tsx|mjs|cjs)$/i.test(repoPath);
      if (!extOk) {
        continue;
      }

      const isDashboardComponent = lowered.includes('frontend/dashboards/src/components/');
      const isFrontendComponent = lowered.includes('frontend/src/components/');
      if (!isDashboardComponent && !isFrontendComponent) {
        continue;
      }

      const basename = path.basename(repoPath).replace(/\.(js|jsx|ts|tsx|mjs|cjs)$/i, '');
      if (COMPONENT_SKIP_NAME.test(basename)) {
        continue;
      }

      candidates.push({
        kind: 'frontend_component_file',
        name: path.basename(fullPath),
        path: repoPath,
        status: 'unknown',
        layer: 'core',
        owner: 'unknown',
        test_status: 'missing',
        release_blocking: true,
        notes: 'Auto-generated from discovered repository surface; requires owner classification.',
      });
    }
  }

  return candidates;
}

export function discoverCrownSurfaceInventory() {
  const items = [
    ...discoverWizardLikeFiles(),
    ...discoverBackendModuleDirectories(),
    ...discoverFrontendComponentFiles(),
  ];

  items.sort((left, right) => {
    if (left.kind !== right.kind) {
      return left.kind.localeCompare(right.kind);
    }
    return left.path.localeCompare(right.path);
  });

  return {
    generated_at_utc: new Date().toISOString(),
    summary: {
      wizard_like_file_count: items.filter((item) => item.kind === 'wizard_like_file').length,
      backend_module_directory_count: items.filter((item) => item.kind === 'backend_module_directory').length,
      frontend_component_file_count: items.filter((item) => item.kind === 'frontend_component_file').length,
      discovered_surface_count: items.length,
    },
    items,
  };
}

export function getInventoryPath() {
  return path.join(root, 'docs', 'testing', 'crown-test-inventory.json');
}

export function writeInventoryFile(inventory) {
  const inventoryPath = getInventoryPath();
  fs.mkdirSync(path.dirname(inventoryPath), { recursive: true });
  fs.writeFileSync(inventoryPath, `${JSON.stringify(inventory, null, 2)}\n`, 'utf8');
  return inventoryPath;
}

export function readInventoryFile() {
  const inventoryPath = getInventoryPath();
  if (!fileExists(inventoryPath)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(inventoryPath, 'utf8'));
}
