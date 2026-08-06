import { useState } from "react";
import { Box, Stepper, Step, StepLabel, Button, Divider } from "@mui/material";

/**
 * CrownWizardStepper — MUI Stepper shell for linear multi-step flows.
 *
 * NOTE: This is the MUI Stepper wrapper.
 * For async multi-step wizard business logic use CrownWizard in
 * components/crown/CrownWizard.jsx which wires step components with shared
 * context and navigation helpers.
 *
 * Props:
 *   steps    — string[] of step labels shown in the progress stepper
 *   children — array of step panels, one per step
 *   onFinish — callback fired when the last step's "Finish" is clicked
 */
export default function CrownWizardStepper({ steps = [], children, onFinish }) {
  const [activeStep, setActiveStep] = useState(0);

  const panels = Array.isArray(children) ? children : [children];
  const isFirst = activeStep === 0;
  const isLast  = activeStep === steps.length - 1;

  function handleNext() {
    if (isLast) {
      onFinish?.();
    } else {
      setActiveStep((s) => s + 1);
    }
  }

  function handleBack() {
    setActiveStep((s) => Math.max(s - 1, 0));
  }

  return (
    <Box>
      <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
        {steps.map((label, index) => (
          <Step key={index}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Divider sx={{ mb: 3 }} />

      <Box sx={{ minHeight: 300 }}>
        {panels[activeStep] ?? null}
      </Box>

      <Divider sx={{ mt: 3 }} />

      <Box sx={{ display: "flex", justifyContent: "space-between", mt: 2 }}>
        <Button
          variant="outlined"
          disabled={isFirst}
          onClick={handleBack}
        >
          Back
        </Button>
        <Button
          variant="contained"
          onClick={handleNext}
        >
          {isLast ? "Finish" : "Continue"}
        </Button>
      </Box>
    </Box>
  );
}
