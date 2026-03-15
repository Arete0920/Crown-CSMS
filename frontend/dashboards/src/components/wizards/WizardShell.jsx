import {
  Box,
  Button,
  Paper,
  Stack,
  Step,
  StepLabel,
  Stepper,
  Typography,
} from '@mui/material';

export default function WizardShell({
  title,
  subtitle,
  steps = [],
  activeStep = 0,
  onBack,
  onNext,
  onSubmit,
  onSaveDraft,
  nextDisabled = false,
  backDisabled = false,
  submitting = false,
  isLastStep = false,
  children,
}) {
  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            {title}
          </Typography>
          {subtitle ? (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {subtitle}
            </Typography>
          ) : null}
        </Box>

        <Paper elevation={1} sx={{ p: 3, borderRadius: 3 }}>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((step) => (
              <Step key={step.key}>
                <StepLabel>{step.label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Paper>

        <Paper elevation={1} sx={{ p: 3, borderRadius: 3 }}>
          {children}
        </Paper>

        <Paper elevation={1} sx={{ p: 2.5, borderRadius: 3 }}>
          <Stack direction="row" spacing={2} justifyContent="space-between" alignItems="center">
            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                onClick={onBack}
                disabled={backDisabled || activeStep === 0 || submitting}
              >
                Back
              </Button>

              {typeof onSaveDraft === 'function' ? (
                <Button variant="text" onClick={onSaveDraft} disabled={submitting}>
                  Save Draft
                </Button>
              ) : null}
            </Stack>

            <Stack direction="row" spacing={2}>
              {isLastStep ? (
                <Button
                  variant="contained"
                  onClick={onSubmit}
                  disabled={nextDisabled || submitting}
                >
                  {submitting ? 'Submitting...' : 'Submit'}
                </Button>
              ) : (
                <Button
                  variant="contained"
                  onClick={onNext}
                  disabled={nextDisabled || submitting}
                >
                  Next
                </Button>
              )}
            </Stack>
          </Stack>
        </Paper>
      </Stack>
    </Box>
  );
}
