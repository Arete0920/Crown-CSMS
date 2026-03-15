import { navItems } from '../components/navigation/navItems';
import dashboardRegistry from './dashboardRegistry';

export function getNavigationSurface() {
  return {
    navItems,
    dashboardRegistry,
  };
}
