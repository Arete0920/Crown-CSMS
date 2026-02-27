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
export default function CrownWizard({ stepComponents, stepLabels = [], initialContext = {} }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [context, setContext] = useState(initialContext);

  const totalSteps = stepComponents.length;
  const StepComponent = stepComponents[stepIndex];

  function goNext() {
    setStepIndex((i) => Math.min(i + 1, totalSteps - 1));
  }

  function goBack() {
    setStepIndex((i) => Math.max(i - 1, 0));
  }

  return (
    <StepComponent
      context={context}
      setContext={setContext}
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
