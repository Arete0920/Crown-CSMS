import { useInRouterContext, useLocation } from 'react-router';
import { HelpTooltip } from './HelpTooltip';

// Map only fixed page identifiers. Never forward URLs containing record IDs or query values.
const contexts = [
  [/^\/(admissions|admissions-dashboard)(\/|$)/, '/admissions', 'admissions'],
  [/^\/(billing|billing-dashboard|billing-setup|finance|finance-dashboard)(\/|$)/, '/billing', 'billing'],
  [/^\/(financial-aid|financial-aid-dashboard|financial-aid-wizard|jireh)(\/|$)/, '/financial-aid', 'financial_aid'],
  [/^\/(onboarding|implementation|implementation-success-dashboard)(\/|$)/, '/onboarding', 'onboarding'],
];

function RoutedHelp() {
  const { pathname } = useLocation();
  const match = contexts.find(([pattern]) => pattern.test(pathname));
  const context = match ? { route_path: match[1], module: match[2] } : { route_path: '/dashboard' };
  return <HelpTooltip key={context.route_path} context={context} />;
}

export default function SolomonContextHelp() {
  const inRouter = useInRouterContext();
  return inRouter ? <RoutedHelp /> : <HelpTooltip context={{ route_path: '/dashboard' }} />;
}
