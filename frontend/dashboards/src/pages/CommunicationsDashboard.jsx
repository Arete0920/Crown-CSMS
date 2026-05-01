import { Grid, Stack } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import CommunicationsSnapshotCard from '../components/dashboard/communications/CommunicationsSnapshotCard.jsx';
import CommunicationsAlertsPanel from '../components/dashboard/communications/CommunicationsAlertsPanel.jsx';
import OutreachQueueCard from '../components/dashboard/communications/OutreachQueueCard.jsx';
import PageState from '../components/states/PageState.jsx';
import WidgetState from '../components/states/WidgetState.jsx';

export default function CommunicationsDashboard() {
  return (
    <CrownLayout
      title="Communications Dashboard"
      subtitle="Family threads, staff messaging, escalations, and outreach operations"
    >
      <PageState>
        <Stack spacing={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <WidgetState>
                <CommunicationsSnapshotCard />
              </WidgetState>
            </Grid>
            <Grid item xs={12} md={8}>
              <WidgetState>
                <CommunicationsAlertsPanel />
              </WidgetState>
            </Grid>
            <Grid item xs={12}>
              <WidgetState>
                <OutreachQueueCard />
              </WidgetState>
            </Grid>
          </Grid>
        </Stack>
      </PageState>
    </CrownLayout>
  );
}
