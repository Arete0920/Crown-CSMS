import { Grid, Stack, Typography } from '@mui/material';
import FoodServiceSnapshotCard from '../components/dashboard/foodservice/FoodServiceSnapshotCard';
import FoodServiceAlertsPanel from '../components/dashboard/foodservice/FoodServiceAlertsPanel';
import FoodServiceQueueCard from '../components/dashboard/foodservice/FoodServiceQueueCard';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';

const FOOD_SERVICE_KPI = [
  { label: 'Meals Served Today', value: '—', dataSource: 'FoodService' },
  { label: 'Free & Reduced', value: '—', dataSource: 'Finance' },
  { label: 'Allergy Alerts', value: '—', dataSource: 'Health' },
  { label: 'Balance Owed', value: '—', dataSource: 'Finance' }
];

export default function FoodServiceDashboard() {
  return (
    <Stack spacing={3}>
      <div>
        <Typography variant="h4" fontWeight={700}>
          Food Service Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Meal volume, low balances, inventory warnings, allergens, and kitchen task flow.
        </Typography>
      </div>

      <KpiStrip cards={FOOD_SERVICE_KPI} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <FoodServiceSnapshotCard />
        </Grid>
        <Grid item xs={12} md={8}>
          <FoodServiceAlertsPanel />
        </Grid>
        <Grid item xs={12}>
          <FoodServiceQueueCard />
        </Grid>
      </Grid>
    </Stack>
  );
}
