import { Grid, Stack } from '@mui/material';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import GradebookSnapshotCard from '../components/dashboard/gradebook/GradebookSnapshotCard.jsx';
import GradebookAlertsPanel from '../components/dashboard/gradebook/GradebookAlertsPanel.jsx';
import TeacherPostingQueueCard from '../components/dashboard/gradebook/TeacherPostingQueueCard.jsx';
import PageState from '../components/states/PageState.jsx';
import WidgetState from '../components/states/WidgetState.jsx';

export default function GradebookDashboard() {
  return (
    <CrownLayout
      title="Gradebook Dashboard"
      subtitle="Assignment completion, grading health, academic risk, and teacher posting status"
    >
      <PageState>
        <Stack spacing={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <WidgetState>
                <GradebookSnapshotCard />
              </WidgetState>
            </Grid>
            <Grid item xs={12} md={8}>
              <WidgetState>
                <GradebookAlertsPanel />
              </WidgetState>
            </Grid>
            <Grid item xs={12}>
              <WidgetState>
                <TeacherPostingQueueCard />
              </WidgetState>
            </Grid>
          </Grid>
        </Stack>
      </PageState>
    </CrownLayout>
  );
}
