import { Grid, Stack, Typography } from '@mui/material';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';
import AdvancementSnapshotCard from '../components/dashboard/advancement/AdvancementSnapshotCard';
import AdvancementCampaignPanel from '../components/dashboard/advancement/AdvancementCampaignPanel';
import AdvancementPipelineCard from '../components/dashboard/advancement/AdvancementPipelineCard';

const ADVANCEMENT_KPI = [
  { label: 'Campaign Total',    value: '—', trend: null, trendUp: null,
    definition: 'Total giving received across all active campaigns year-to-date.',
    dataSource: 'Advancement API', dataHref: '/advancement' },
  { label: 'Donors YTD',        value: '—', trend: null, trendUp: null,
    definition: 'Unique donors who have given at least once in the current fiscal year.',
    dataSource: 'Advancement API', dataHref: '/advancement' },
  { label: 'Pledge Outstanding', value: '—', trend: null, trendUp: null,
    definition: 'Total outstanding pledge balance yet to be collected.',
    dataSource: 'Advancement API', dataHref: '/advancement' },
  { label: 'Retention Rate',    value: '—', trend: null, trendUp: null,
    definition: 'Percentage of prior-year donors who gave again this year.',
    dataSource: 'Advancement API', dataHref: '/advancement' },
];

export default function AdvancementDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Advancement Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Giving health, campaign momentum, donor retention, church partnerships, and next actions.
        </Typography>
      </div>

      <KpiStrip cards={ADVANCEMENT_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <AdvancementSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <AdvancementCampaignPanel />
        </Grid>
        <Grid item xs={12}>
          <AdvancementPipelineCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
