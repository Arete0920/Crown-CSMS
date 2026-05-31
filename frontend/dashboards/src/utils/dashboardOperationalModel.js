import { DATA_STATES, getOperationalCatalog } from '../config/operationalKpiCatalog';

function toNumber(value, fallback = 0) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '' && Number.isFinite(Number(value))) return Number(value);
  return fallback;
}

function formatCurrency(value) {
  const amount = toNumber(value);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatPercent(value) {
  const n = toNumber(value);
  const normalized = n > 1 ? n : n * 100;
  return `${Math.round(normalized)}%`;
}

function formatValue(value, format) {
  if (format === 'currency') return formatCurrency(value);
  if (format === 'percent') return formatPercent(value);
  if (format === 'days') return `${toNumber(value)} day${toNumber(value) === 1 ? '' : 's'}`;
  if (format === 'milliseconds') return `${toNumber(value)} ms`;
  return String(toNumber(value));
}

function getDetail(metric) {
  if (metric.detail) return metric.detail;
  if (metric.format === 'percent') return 'Operational performance ratio.';
  if (metric.format === 'currency') return 'Financial exposure requiring visibility.';
  if (metric.format === 'days') return 'Maximum age in current workflow stage.';
  return 'Current operating count.';
}

function isWarn(metric, value) {
  if (typeof metric.warnAbove === 'number') {
    return toNumber(value) > metric.warnAbove;
  }
  if (typeof metric.warnBelow === 'number') {
    return toNumber(value) < metric.warnBelow;
  }
  return false;
}

export function buildOperationalDashboardModel({
  moduleKey,
  raw = {},
  dataState = DATA_STATES.FALLBACK,
  sourceLabel,
}) {
  const catalog = getOperationalCatalog(moduleKey);

  if (!catalog) {
    return {
      metrics: [],
      priorities: [],
      statuses: [
        {
          label: 'Operational Catalog',
          state: `No catalog registered for ${moduleKey}`,
        },
      ],
      alerts: [
        {
          title: 'Dashboard operating model is not registered.',
          detail: `Add ${moduleKey} to MODULE_KPI_CATALOG.`,
          tone: 'warn',
        },
      ],
    };
  }

  const effectiveSourceLabel = sourceLabel || catalog.sourceLabel || 'Dashboard operating model';

  const metrics = catalog.metrics.map((metric) => {
    const rawValue = raw[metric.key];
    const value = rawValue === undefined || rawValue === null ? 0 : rawValue;

    return {
      label: metric.label,
      value: formatValue(value, metric.format),
      detail: getDetail(metric, value),
      accent: metric.accent || 'blue',
      dataState,
      sourceLabel: effectiveSourceLabel,
      tone: isWarn(metric, value) ? 'warn' : 'good',
    };
  });

  const priorities = (catalog.actions || [])
    .map((action) => {
      const metric = catalog.metrics.find((item) => item.key === action.key);
      const value = raw[action.key];
      const needsAction = metric ? isWarn(metric, value) : toNumber(value) > 0;

      return {
        title: action.title,
        detail: `${action.detail} Current value: ${formatValue(value, metric?.format || 'number')}.`,
        state: needsAction ? 'Action Required' : 'Stable',
        tone: needsAction ? 'warn' : 'good',
      };
    })
    .filter((item) => item.tone === 'warn');

  const statuses = [
    { label: 'Data Source', state: effectiveSourceLabel },
    { label: 'Data Truth', state: dataState },
    {
      label: 'Action Queue',
      state: priorities.length > 0 ? `${priorities.length} open action${priorities.length === 1 ? '' : 's'}` : 'Stable',
    },
  ];

  const alerts = dataState === DATA_STATES.LIVE
    ? []
    : [
      {
        title: `Dashboard is ${dataState}.`,
        detail: `Values are not fully live from ${effectiveSourceLabel}.`,
        tone: 'warn',
      },
    ];

  return { metrics, priorities, statuses, alerts };
}
