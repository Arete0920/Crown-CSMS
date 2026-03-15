import { useState } from "react";

/**
 * CrownWizard
 *
 * Generic multi-step container that passes a shared `context` / `setContext`
 * to each step, plus navigation helpers.
 *
 * @param {React.ComponentType[]} stepComponents   one component per step
 * @param {string[]}              stepLabels        display labels for step pills
 * @param {any}                   initialContext    initial shared state object
 */
export default function CrownWizard({
  stepComponents,
  stepLabels = [],
  initialContext = {},
  onContextChange,
  onStepChange,
}) {
  const [stepIndex, setStepIndex] = useState(0);
  const [context, setContext] = useState(initialContext);

  const totalSteps = stepComponents.length;
  const StepComponent = stepComponents[stepIndex];

  function goNext() {
    setStepIndex((i) => {
      const nextStep = Math.min(i + 1, totalSteps - 1);
      if (typeof onStepChange === 'function') {
        onStepChange(nextStep);
      }
      return nextStep;
    });
  }

  function goBack() {
    setStepIndex((i) => {
      const nextStep = Math.max(i - 1, 0);
      if (typeof onStepChange === 'function') {
        onStepChange(nextStep);
      }
      return nextStep;
    });
  }

  function applyContext(nextValue) {
    setContext((previous) => {
      const resolved = typeof nextValue === 'function' ? nextValue(previous) : nextValue;
      if (typeof onContextChange === 'function') {
        onContextChange(resolved);
      }
      return resolved;
    });
  }

  return (
    <StepComponent
      context={context}
      setContext={applyContext}
      stepIndex={stepIndex}
      totalSteps={totalSteps}
      steps={stepLabels}
      goNext={goNext}
      goBack={goBack}
      canGoBack={stepIndex > 0}
      canGoNext={stepIndex < totalSteps - 1}
      setStepIndex={setStepIndex}
    />
  );
}
