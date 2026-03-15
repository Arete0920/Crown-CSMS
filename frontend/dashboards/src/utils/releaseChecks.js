import { getBuildInfo } from './buildInfo';
import dashboardRegistry from '../config/dashboardRegistry';
import { navItems } from '../components/navigation/navItems';

export function evaluateStaticReleaseChecks() {
  const build = getBuildInfo();

  const sidebarPaths = navItems.map((item) => item.href).filter(Boolean);
  const registryPaths = dashboardRegistry.map((item) => item.path).filter(Boolean);

  return {
    'build-sha': build.buildSha !== 'missing',
    'build-tag': build.buildTag !== 'missing',
    'api-base-url': build.apiBaseUrl !== 'missing',
    'sidebar-unique': new Set(sidebarPaths).size === sidebarPaths.length,
    'registry-unique': new Set(registryPaths).size === registryPaths.length,
  };
}
