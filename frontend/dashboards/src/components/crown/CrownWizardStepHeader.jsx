import "../../styles/crown-wizard.css";

/**
 * CrownWizardStepHeader
 *
 * @param {string}   title
 * @param {string}   subtitle
 * @param {number}   stepIndex   0-based current step
 * @param {number}   totalSteps
 * @param {string[]} steps       labels for each step
 */
export default function CrownWizardStepHeader({ title, subtitle, stepIndex, totalSteps, steps = [] }) {
  return (
    <div className="crown-wizard-header" style={{ flexDirection: "column" }}>
      <div>
        <h2 style={{ margin: 0, color: "var(--crown-text)" }}>{title}</h2>
        {subtitle && <p style={{ margin: "4px 0 0", color: "var(--crown-muted)", fontSize: 13 }}>{subtitle}</p>}
      </div>
      {steps.length > 0 && (
        <div className="crown-wizard-steps">
          {steps.map((label, i) => {
            const cls =
              i < stepIndex ? "crown-wizard-step-pill done"
              : i === stepIndex ? "crown-wizard-step-pill active"
              : "crown-wizard-step-pill";
            return (
              <span key={i} className={cls}>
                {i + 1}. {label}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
