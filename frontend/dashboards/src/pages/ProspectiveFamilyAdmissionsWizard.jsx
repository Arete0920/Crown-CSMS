import { useEffect, useMemo, useState } from "react";
import CrownPublicLayout from "../components/crown/CrownPublicLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import CrownWizardStepHeader from "../components/crown/CrownWizardStepHeader.jsx";
import { useWizardDraft } from "../hooks/useWizardDraft";
import { fetchAdmissionsPublicConfig, submitAdmissionsIntake } from "../api/admissions";
import "../styles/crown-wizard.css";

const STEPS = [
  "Interest",
  "Inquiry",
  "Family Profile",
  "Student Profile",
  "Mission Alignment",
  "Documents",
  "Review",
  "Submit",
];

const CAMPUS_OPTIONS = [
  "Heritage Christian Academy",
  "North Campus",
  "South Campus",
  "Online Program",
];

const GRADE_OPTIONS = [
  "Pre-K",
  "K",
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "10",
  "11",
  "12",
];

const START_TERM_OPTIONS = ["2026-2027", "2027-2028", "2028-2029"];

const HEARD_ABOUT_OPTIONS = [
  "Church referral",
  "Current family",
  "Friend or colleague",
  "Social media",
  "Search engine",
  "Community event",
  "Other",
];

const TOUR_WINDOW_OPTIONS = [
  "Weekday mornings",
  "Weekday afternoons",
  "Evenings",
  "Flexible",
];

const INTERVIEW_MODE_OPTIONS = [
  "In person",
  "Video call",
  "Phone",
  "No preference",
];

const DEFAULT_APPLICATION_FEE_AMOUNT = Number(import.meta.env.VITE_ADMISSIONS_APPLICATION_FEE_USD || "85");
const FALLBACK_FEE_CONFIG = {
  required: Number.isFinite(DEFAULT_APPLICATION_FEE_AMOUNT) && DEFAULT_APPLICATION_FEE_AMOUNT > 0,
  amount: Number.isFinite(DEFAULT_APPLICATION_FEE_AMOUNT) ? DEFAULT_APPLICATION_FEE_AMOUNT : 0,
  currency: "USD",
};

const CHURCH_AFFILIATION_OPTIONS = [
  "Member at partnering church",
  "Member at non-partner church",
  "Attend regularly",
  "New to church community",
  "Prefer not to say",
  "Other",
];

const GUARDIAN_RELATIONSHIP_OPTIONS = [
  "Mother",
  "Father",
  "Stepmother",
  "Stepfather",
  "Grandparent",
  "Guardian",
  "Other",
];

const CURRENT_SCHOOL_OPTIONS = [
  "Public school",
  "Private school",
  "Christian school",
  "Charter school",
  "Homeschool",
  "First-time school enrollment",
  "Other",
];

function createLocalId(prefix) {
  const random = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`;
  return `${prefix}-${random}`;
}

function createGuardian(isPrimary = false) {
  return {
    id: createLocalId("guardian"),
    relationship: "",
    relationshipOther: "",
    guardianName: "",
    email: "",
    phone: "",
    isPrimary,
  };
}

function createStudent() {
  return {
    id: createLocalId("student"),
    firstName: "",
    lastName: "",
    gradeApplyingFor: "",
    currentSchool: "",
    currentSchoolOther: "",
    strengths: "",
    supportNeeds: "",
  };
}

const INITIAL_CONTEXT = {
  inquiry: {
    campus: "",
    startTerm: "",
    heardAbout: "",
    preferredTourWindow: "",
    preferredInterviewMode: "",
  },
  family: {
    guardians: [createGuardian(true)],
    churchAffiliation: "",
    churchAffiliationOther: "",
  },
  students: [createStudent()],
  mission: {
    covenantPartnership: false,
    discipleshipCommitment: false,
    serviceMindset: false,
    comments: "",
  },
  documents: {
    transcriptReady: false,
    recommendationsReady: false,
    pastorReferenceReady: false,
    immunizationReady: false,
  },
  attestations: {
    informationAccurate: false,
    missionPartnershipUnderstood: false,
    communicationOptIn: true,
  },
  applicationFee: {
    policyAccepted: false,
    waiverRequested: false,
  },
  submitted: false,
};

function isGuardianComplete(guardian) {
  const relationship = String(guardian?.relationship || "").trim();
  const relationshipOther = String(guardian?.relationshipOther || "").trim();
  return Boolean(
    relationship &&
    String(guardian?.guardianName || "").trim() &&
    String(guardian?.email || "").trim() &&
    String(guardian?.phone || "").trim() &&
    (relationship !== "Other" || relationshipOther)
  );
}

function isStudentComplete(student) {
  const currentSchool = String(student?.currentSchool || "").trim();
  const currentSchoolOther = String(student?.currentSchoolOther || "").trim();
  return Boolean(
    String(student?.firstName || "").trim() &&
    String(student?.lastName || "").trim() &&
    String(student?.gradeApplyingFor || "").trim() &&
    currentSchool &&
    (currentSchool !== "Other" || currentSchoolOther)
  );
}

function buildHouseholdReadiness(context) {
  const guardians = context?.family?.guardians || [];
  const students = context?.students || [];
  const mission = context?.mission || {};
  const docs = context?.documents || {};
  const inquiry = context?.inquiry || {};

  return {
    householdSize: `${guardians.length || 0} guardian(s), ${students.length || 0} child(ren)`,
    checkpoints: [
      {
        label: "Inquiry setup",
        done: Boolean(String(inquiry.campus || "").trim() && String(inquiry.startTerm || "").trim()),
      },
      {
        label: "Guardians complete",
        done: guardians.length > 0 && guardians.every(isGuardianComplete),
      },
      {
        label: "Children complete",
        done: students.length > 0 && students.every(isStudentComplete),
      },
      {
        label: "Mission alignment",
        done: Boolean(mission.covenantPartnership && mission.discipleshipCommitment),
      },
      {
        label: "Document readiness",
        done: Object.values(docs).filter(Boolean).length >= 2,
      },
    ],
  };
}

function StepFrame({
  title,
  subtitle,
  stepIndex,
  totalSteps,
  steps,
  children,
  goNext,
  goBack,
  canGoBack,
  continueLabel = "Continue ->",
  canContinue = true,
  context,
}) {
  const readiness = buildHouseholdReadiness(context || {});
  const checkpointsDone = readiness.checkpoints.filter((checkpoint) => checkpoint.done).length;

  return (
    <div>
      <CrownWizardStepHeader
        title={title}
        subtitle={subtitle}
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div className="crown-card" style={{ marginTop: 16, padding: 16 }}>
        <div
          style={{
            border: "1px solid var(--crown-border)",
            borderRadius: 8,
            padding: "10px 12px",
            marginBottom: 12,
            background: "var(--crown-bg, #f8fafc)",
            fontSize: 12,
          }}
        >
          <div style={{ marginBottom: 6, color: "var(--crown-muted)" }}>
            Household: {readiness.householdSize} · Readiness {checkpointsDone}/{readiness.checkpoints.length}
          </div>
          <div style={{ display: "grid", gap: 4 }}>
            {readiness.checkpoints.map((checkpoint) => (
              <div key={checkpoint.label} style={{ color: checkpoint.done ? "var(--crown-success, #1b8f4b)" : "var(--crown-muted)" }}>
                {checkpoint.done ? "✓" : "○"} {checkpoint.label}
              </div>
            ))}
          </div>
        </div>
        {children}
      </div>

      <div className="crown-wizard-actions">
        <span className="crown-muted" style={{ fontSize: 12 }}>
          Step {stepIndex + 1} of {totalSteps}
        </span>
        <div className="crown-wizard-actions-right">
          {canGoBack && (
            <button className="crown-btn" onClick={goBack}>
              Back
            </button>
          )}
          <button
            className="crown-btn crown-btn-primary"
            onClick={goNext}
            disabled={!canContinue}
            title={canContinue ? undefined : "Complete required fields to continue"}
          >
            {continueLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

function StepInterest(props) {
  return (
    <StepFrame
      {...props}
      title="Begin Your Admissions Journey"
      subtitle="A mission-aligned process for families seeking Christian formation and academic excellence."
    >
      <p style={{ marginTop: 0, color: "var(--crown-text)" }}>
        This intake starts with your family story, then guides you through inquiry,
        application, and enrollment in a clear, supportive flow.
      </p>
      <ul style={{ marginBottom: 0, color: "var(--crown-muted)" }}>
        <li>Interest and inquiry in one guided path</li>
        <li>Clear checklist and expectations</li>
        <li>Mission and portrait-aligned family conversation</li>
        <li>Human-led review and transparent next steps</li>
      </ul>
    </StepFrame>
  );
}

function StepInquiry({ context, setContext, goNext, ...props }) {
  const inquiry = context.inquiry;
  const [attemptedContinue, setAttemptedContinue] = useState(false);

  const missingRequired = [];
  if (!String(inquiry.campus || "").trim()) missingRequired.push("Campus");
  if (!String(inquiry.startTerm || "").trim()) missingRequired.push("Start Term");

  const canContinue = missingRequired.length === 0;

  function update(name, value) {
    setContext((prev) => ({
      ...prev,
      inquiry: { ...prev.inquiry, [name]: value },
    }));
  }

  function handleContinue() {
    setAttemptedContinue(true);
    if (!canContinue) {
      return;
    }
    goNext();
  }

  return (
    <StepFrame
      {...props}
      context={context}
      title="Inquiry Details"
      subtitle="Tell us where and when you are applying."
      goNext={handleContinue}
    >
      <div style={{ display: "grid", gap: 12 }}>
        <label>
          <span style={{ display: "block", marginBottom: 4 }}>Campus *</span>
          <select
            className="crown-input"
            value={inquiry.campus}
            onChange={(e) => update("campus", e.target.value)}
          >
            <option value="">Select campus</option>
            {CAMPUS_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>
        <label>
          <span style={{ display: "block", marginBottom: 4 }}>Start Term *</span>
          <select
            className="crown-input"
            value={inquiry.startTerm}
            onChange={(e) => update("startTerm", e.target.value)}
          >
            <option value="">Select start term</option>
            {START_TERM_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>
        <label>
          <span style={{ display: "block", marginBottom: 4 }}>How did you hear about us?</span>
          <select
            className="crown-input"
            value={inquiry.heardAbout}
            onChange={(e) => update("heardAbout", e.target.value)}
          >
            <option value="">Select one (optional)</option>
            {HEARD_ABOUT_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>

        <label>
          <span style={{ display: "block", marginBottom: 4 }}>Preferred tour window</span>
          <select
            className="crown-input"
            value={inquiry.preferredTourWindow || ""}
            onChange={(e) => update("preferredTourWindow", e.target.value)}
          >
            <option value="">Select one (optional)</option>
            {TOUR_WINDOW_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>

        <label>
          <span style={{ display: "block", marginBottom: 4 }}>Preferred interview mode</span>
          <select
            className="crown-input"
            value={inquiry.preferredInterviewMode || ""}
            onChange={(e) => update("preferredInterviewMode", e.target.value)}
          >
            <option value="">Select one (optional)</option>
            {INTERVIEW_MODE_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>

        {attemptedContinue && !canContinue && (
          <p className="crown-alert" style={{ margin: 0 }}>
            Please complete required fields: {missingRequired.join(", ")}.
          </p>
        )}
      </div>
    </StepFrame>
  );
}

function StepFamily({ context, setContext, ...props }) {
  const family = context.family;
  const guardians = (Array.isArray(family.guardians) && family.guardians.length > 0
    ? family.guardians
    : [createGuardian(true)]).map((guardian) => ({
      ...guardian,
      id: guardian.id || createLocalId("guardian"),
    }));

  const canContinue = guardians.every((guardian) => {
    const hasCore = Boolean(
      String(guardian.guardianName || "").trim() &&
      String(guardian.email || "").trim() &&
      String(guardian.phone || "").trim() &&
      String(guardian.relationship || "").trim()
    );
    if (!hasCore) {
      return false;
    }
    if (guardian.relationship === "Other") {
      return Boolean(String(guardian.relationshipOther || "").trim());
    }
    return true;
  });

  function update(name, value) {
    setContext((prev) => ({
      ...prev,
      family: { ...prev.family, [name]: value },
    }));
  }

  function updateGuardian(index, name, value) {
    setContext((prev) => {
      const source = Array.isArray(prev.family.guardians) && prev.family.guardians.length > 0
        ? prev.family.guardians
        : [createGuardian(true)];
      const nextGuardians = source.map((guardian, currentIndex) => {
        if (currentIndex !== index) {
          return guardian;
        }
        return { ...guardian, [name]: value };
      });
      return {
        ...prev,
        family: {
          ...prev.family,
          guardians: nextGuardians,
        },
      };
    });
  }

  function setPrimaryGuardian(index) {
    setContext((prev) => {
      const source = Array.isArray(prev.family.guardians) && prev.family.guardians.length > 0
        ? prev.family.guardians
        : [createGuardian(true)];
      const nextGuardians = source.map((guardian, currentIndex) => ({
        ...guardian,
        isPrimary: currentIndex === index,
      }));
      return {
        ...prev,
        family: {
          ...prev.family,
          guardians: nextGuardians,
        },
      };
    });
  }

  function addGuardian() {
    setContext((prev) => ({
      ...prev,
      family: {
        ...prev.family,
        guardians: [
          ...(Array.isArray(prev.family.guardians) && prev.family.guardians.length > 0
            ? prev.family.guardians
            : [createGuardian(true)]),
          createGuardian(false),
        ],
      },
    }));
  }

  function removeGuardian(index) {
    setContext((prev) => {
      const existing = prev.family.guardians || [];
      if (existing.length <= 1) {
        return prev;
      }
      let nextGuardians = existing.filter((_, currentIndex) => currentIndex !== index);
      if (!nextGuardians.some((guardian) => guardian.isPrimary)) {
        nextGuardians = nextGuardians.map((guardian, currentIndex) => ({
          ...guardian,
          isPrimary: currentIndex === 0,
        }));
      }
      return {
        ...prev,
        family: {
          ...prev.family,
          guardians: nextGuardians,
        },
      };
    });
  }

  return (
    <StepFrame
      {...props}
      context={context}
      title="Family Profile"
      subtitle="Primary guardian contact and household context."
      canContinue={canContinue}
    >
      <div style={{ display: "grid", gap: 12 }}>
        {guardians.map((guardian, index) => (
          <div
            key={guardian.id}
            className="crown-card"
            style={{ padding: 12, border: "1px solid var(--crown-border)" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <strong>Guardian {index + 1}</strong>
              {guardians.length > 1 ? (
                <button className="crown-btn" type="button" onClick={() => removeGuardian(index)}>
                  Remove
                </button>
              ) : null}
            </div>

            <div style={{ display: "grid", gap: 10 }}>
              <label>
                <span style={{ display: "block", marginBottom: 4 }}>Relationship *</span>
                <select
                  className="crown-input"
                  value={guardian.relationship}
                  onChange={(e) => updateGuardian(index, "relationship", e.target.value)}
                >
                  <option value="">Select relationship</option>
                  {GUARDIAN_RELATIONSHIP_OPTIONS.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </label>

              {guardian.relationship === "Other" ? (
                <label>
                  <span style={{ display: "block", marginBottom: 4 }}>Relationship (Other) *</span>
                  <input
                    className="crown-input"
                    value={guardian.relationshipOther || ""}
                    onChange={(e) => updateGuardian(index, "relationshipOther", e.target.value)}
                  />
                </label>
              ) : null}

              <label>
                <span style={{ display: "block", marginBottom: 4 }}>Guardian Name *</span>
                <input
                  className="crown-input"
                  value={guardian.guardianName || ""}
                  onChange={(e) => updateGuardian(index, "guardianName", e.target.value)}
                />
              </label>

              <label>
                <span style={{ display: "block", marginBottom: 4 }}>Email *</span>
                <input
                  className="crown-input"
                  type="email"
                  value={guardian.email || ""}
                  onChange={(e) => updateGuardian(index, "email", e.target.value)}
                />
              </label>

              <label>
                <span style={{ display: "block", marginBottom: 4 }}>Phone *</span>
                <input
                  className="crown-input"
                  value={guardian.phone || ""}
                  onChange={(e) => updateGuardian(index, "phone", e.target.value)}
                />
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  checked={Boolean(guardian.isPrimary)}
                  onChange={() => setPrimaryGuardian(index)}
                />
                <span>Primary contact</span>
              </label>
            </div>
          </div>
        ))}

        <button className="crown-btn" type="button" onClick={addGuardian}>
          Add Guardian
        </button>

        <label>
          <span style={{ display: "block", marginBottom: 4 }}>Church Affiliation (optional)</span>
          <select
            className="crown-input"
            value={family.churchAffiliation}
            onChange={(e) => update("churchAffiliation", e.target.value)}
          >
            <option value="">Select one (optional)</option>
            {CHURCH_AFFILIATION_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>

        {family.churchAffiliation === "Other" && (
          <label>
            <span style={{ display: "block", marginBottom: 4 }}>Church Affiliation (Other)</span>
            <input
              className="crown-input"
              value={family.churchAffiliationOther || ""}
              onChange={(e) => update("churchAffiliationOther", e.target.value)}
              placeholder="Enter church affiliation"
            />
          </label>
        )}
      </div>
    </StepFrame>
  );
}

function StepStudent({ context, setContext, ...props }) {
  const students = (Array.isArray(context.students) && context.students.length > 0
    ? context.students
    : [createStudent()]).map((student) => ({
      ...student,
      id: student.id || createLocalId("student"),
    }));

  const canContinue = students.every((student) => {
    const hasCurrentSchool =
      student.currentSchool === "Other"
        ? Boolean(String(student.currentSchoolOther || "").trim())
        : Boolean(String(student.currentSchool || "").trim());
    return isStudentComplete(student) && hasCurrentSchool;
  });

  function updateStudent(index, name, value) {
    setContext((prev) => ({
      ...prev,
      students: (
        Array.isArray(prev.students) && prev.students.length > 0
          ? prev.students
          : [createStudent()]
      ).map((student, currentIndex) => {
        if (currentIndex !== index) {
          return student;
        }
        return { ...student, [name]: value };
      }),
    }));
  }

  function addStudent() {
    setContext((prev) => ({
      ...prev,
      students: [
        ...(Array.isArray(prev.students) && prev.students.length > 0 ? prev.students : [createStudent()]),
        createStudent(),
      ],
    }));
  }

  function removeStudent(index) {
    setContext((prev) => {
      const existing = prev.students || [];
      if (existing.length <= 1) {
        return prev;
      }
      return {
        ...prev,
        students: existing.filter((_, currentIndex) => currentIndex !== index),
      };
    });
  }

  return (
    <StepFrame
      {...props}
      context={context}
      title="Student Profile"
      subtitle="Academic context and support readiness."
      canContinue={canContinue}
    >
      <div style={{ display: "grid", gap: 12 }}>
        {students.map((student, index) => (
          <div
            key={student.id}
            className="crown-card"
            style={{ padding: 12, border: "1px solid var(--crown-border)" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <strong>Child {index + 1}</strong>
              {students.length > 1 ? (
                <button className="crown-btn" type="button" onClick={() => removeStudent(index)}>
                  Remove
                </button>
              ) : null}
            </div>

            <div style={{ display: "grid", gap: 10 }}>
              <label>
                <span style={{ display: "block", marginBottom: 4 }}>First Name *</span>
                <input
                  className="crown-input"
                  value={student.firstName || ""}
                  onChange={(e) => updateStudent(index, "firstName", e.target.value)}
                />
              </label>

              <label>
                <span style={{ display: "block", marginBottom: 4 }}>Last Name *</span>
                <input
                  className="crown-input"
                  value={student.lastName || ""}
                  onChange={(e) => updateStudent(index, "lastName", e.target.value)}
                />
              </label>

              <label>
                <span style={{ display: "block", marginBottom: 4 }}>Grade Applying For *</span>
                <select
                  className="crown-input"
                  value={student.gradeApplyingFor || ""}
                  onChange={(e) => updateStudent(index, "gradeApplyingFor", e.target.value)}
                >
                  <option value="">Select grade</option>
                  {GRADE_OPTIONS.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </label>

              <label>
                <span style={{ display: "block", marginBottom: 4 }}>Current School *</span>
                <select
                  className="crown-input"
                  value={student.currentSchool || ""}
                  onChange={(e) => updateStudent(index, "currentSchool", e.target.value)}
                >
                  <option value="">Select one</option>
                  {CURRENT_SCHOOL_OPTIONS.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </label>

              {student.currentSchool === "Other" ? (
                <label>
                  <span style={{ display: "block", marginBottom: 4 }}>Current School (Other) *</span>
                  <input
                    className="crown-input"
                    value={student.currentSchoolOther || ""}
                    onChange={(e) => updateStudent(index, "currentSchoolOther", e.target.value)}
                    placeholder="Enter current school"
                  />
                </label>
              ) : null}

              <label>
                <span style={{ display: "block", marginBottom: 4 }}>Student Strengths</span>
                <textarea
                  className="crown-input"
                  rows={3}
                  value={student.strengths || ""}
                  onChange={(e) => updateStudent(index, "strengths", e.target.value)}
                />
              </label>

              <label>
                <span style={{ display: "block", marginBottom: 4 }}>Support Needs (if any)</span>
                <textarea
                  className="crown-input"
                  rows={3}
                  value={student.supportNeeds || ""}
                  onChange={(e) => updateStudent(index, "supportNeeds", e.target.value)}
                />
              </label>
            </div>
          </div>
        ))}

        <button className="crown-btn" type="button" onClick={addStudent}>
          Add Child
        </button>
      </div>
    </StepFrame>
  );
}

function StepMission({ context, setContext, ...props }) {
  const mission = context.mission;
  const canContinue = mission.covenantPartnership && mission.discipleshipCommitment;

  function toggle(name) {
    setContext((prev) => ({
      ...prev,
      mission: { ...prev.mission, [name]: !prev.mission[name] },
    }));
  }

  function updateComments(value) {
    setContext((prev) => ({
      ...prev,
      mission: { ...prev.mission, comments: value },
    }));
  }

  return (
    <StepFrame
      {...props}
      context={context}
      title="Mission and Values Alignment"
      subtitle="This section supports mission-fit conversation and partnership readiness."
      canContinue={canContinue}
    >
      <div style={{ display: "grid", gap: 10 }}>
        <label>
          <input
            type="checkbox"
            checked={mission.covenantPartnership}
            onChange={() => toggle("covenantPartnership")}
          />{" "}
          We understand the school-family covenant partnership model. *
        </label>
        <label>
          <input
            type="checkbox"
            checked={mission.discipleshipCommitment}
            onChange={() => toggle("discipleshipCommitment")}
          />{" "}
          We value spiritual formation and discipleship as part of education. *
        </label>
        <label>
          <input
            type="checkbox"
            checked={mission.serviceMindset}
            onChange={() => toggle("serviceMindset")}
          />{" "}
          We encourage service, character, and leadership development.
        </label>
        <label>
          <span style={{ display: "block", marginBottom: 4 }}>Family mission comments (optional)</span>
          <textarea
            className="crown-input"
            rows={4}
            value={mission.comments}
            onChange={(e) => updateComments(e.target.value)}
            placeholder="Share what you value most in a Christian school partnership."
          />
        </label>
      </div>
    </StepFrame>
  );
}

function StepDocuments({ context, setContext, ...props }) {
  const docs = context.documents;
  const completionCount = Object.values(docs).filter(Boolean).length;
  const canContinue = completionCount >= 2;

  function toggle(name) {
    setContext((prev) => ({
      ...prev,
      documents: { ...prev.documents, [name]: !prev.documents[name] },
    }));
  }

  return (
    <StepFrame
      {...props}
      context={context}
      title="Document Readiness"
      subtitle="Select what you already have ready. You can still continue with partial completion."
      canContinue={canContinue}
    >
      <div style={{ display: "grid", gap: 10 }}>
        <label><input type="checkbox" checked={docs.transcriptReady} onChange={() => toggle("transcriptReady")} /> Transcript available</label>
        <label><input type="checkbox" checked={docs.recommendationsReady} onChange={() => toggle("recommendationsReady")} /> Recommendations available</label>
        <label><input type="checkbox" checked={docs.pastorReferenceReady} onChange={() => toggle("pastorReferenceReady")} /> Pastor/church reference available</label>
        <label><input type="checkbox" checked={docs.immunizationReady} onChange={() => toggle("immunizationReady")} /> Immunization records available</label>
      </div>
      <p style={{ marginTop: 14, color: "var(--crown-muted)", fontSize: 13 }}>
        Ready items: {completionCount}/4
      </p>
    </StepFrame>
  );
}

function StepReview({ context, ...props }) {
  const summary = useMemo(
    () => ({
      inquiry: context.inquiry,
      family: context.family,
      students: context.students,
      mission: context.mission,
      documents: context.documents,
    }),
    [context]
  );

  return (
    <StepFrame
      {...props}
      context={context}
      title="Review Application"
      subtitle="Confirm details before submission."
      continueLabel="Submit Application ->"
    >
      <div className="crown-card" style={{ padding: 12, marginBottom: 12, border: "1px solid var(--crown-border)" }}>
        <p style={{ margin: "0 0 8px 0", fontWeight: 600 }}>What happens next</p>
        <ul style={{ margin: 0, color: "var(--crown-muted)" }}>
          <li>Admissions coordinator responds within 1 business day</li>
          <li>Completeness and mission-conversation review starts within 2 business days</li>
          <li>You receive milestone updates by email (and SMS if opted in)</li>
        </ul>
      </div>

      <div className="crown-card" style={{ padding: 12, marginBottom: 12, border: "1px solid var(--crown-border)" }}>
        <p style={{ margin: "0 0 8px 0", fontWeight: 600 }}>Application snapshot</p>
        <div style={{ display: "grid", gap: 6, color: "var(--crown-muted)", fontSize: 13 }}>
          <div>Campus: {summary.inquiry?.campus || "Not provided"}</div>
          <div>Start term: {summary.inquiry?.startTerm || "Not provided"}</div>
          <div>Tour preference: {summary.inquiry?.preferredTourWindow || "Not provided"}</div>
          <div>Interview preference: {summary.inquiry?.preferredInterviewMode || "Not provided"}</div>
          <div>Guardians: {summary.family?.guardians?.length || 0}</div>
          <div>Students: {summary.students?.length || 0}</div>
          <div>Documents ready: {Object.values(summary.documents || {}).filter(Boolean).length}/4</div>
        </div>
      </div>

      <details>
        <summary style={{ cursor: "pointer", marginBottom: 8 }}>View full JSON payload</summary>
      <pre
        style={{
          margin: 0,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          color: "var(--crown-text)",
          fontSize: 12,
          background: "var(--crown-bg, #f8fafc)",
          padding: 12,
          borderRadius: 8,
        }}
      >
        {JSON.stringify(summary, null, 2)}
      </pre>
      </details>
    </StepFrame>
  );
}

function resolveSubmitErrorMessage(error) {
  const status = Number(error?.status || 0);
  const detail = error?.details?.detail;
  if (status >= 500) {
    return "Submission service is temporarily unavailable. Please retry in a few minutes or contact admissions support.";
  }
  if (typeof detail === "string" && detail.trim()) {
    return detail.trim();
  }
  if (typeof error?.message === "string" && error.message.trim()) {
    return error.message.trim();
  }
  return "Unable to submit application right now.";
}

function buildSubmissionSummary(receipt) {
  if (receipt?.application_ids?.length) {
    return `Submission references (${receipt.application_ids.length}): ${receipt.application_ids.join(", ")}`;
  }
  if (receipt?.application_id) {
    return `Submission reference: ${receipt.application_id}`;
  }
  return "";
}

function getSubmitBlockReason({ submitting, preflightStatus, canFinalize }) {
  if (submitting) {
    return "in_progress";
  }
  if (preflightStatus === "down") {
    return "Submission service appears offline. Please run the service check and retry.";
  }
  if (!canFinalize) {
    return "Please complete required attestations before submitting.";
  }
  return "";
}

function normalizeFeeConfig(rawConfig) {
  const amount = Number(rawConfig?.amount);
  const fallbackAmount = Number(FALLBACK_FEE_CONFIG.amount || 0);
  return {
    required: Boolean(rawConfig?.required),
    amount: Number.isFinite(amount) ? amount : fallbackAmount,
    currency: String(rawConfig?.currency || FALLBACK_FEE_CONFIG.currency || "USD"),
  };
}

async function checkSubmitServiceAvailability() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await window.fetch("/api/v1/admissions/submit/", {
      method: "OPTIONS",
      credentials: "include",
      cache: "no-store",
      signal: controller.signal,
    });
    if (response.ok || response.status === 405) {
      return { status: "ready", message: "Submission service is available." };
    }
    return {
      status: "down",
      message: `Submission service check returned HTTP ${response.status}. Please retry in a moment.`,
    };
  } catch {
    return {
      status: "down",
      message: "Submission service is currently unreachable. Please check connectivity or contact admissions support.",
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

function toggleFeeSelection(currentFee, name) {
  const current = {
    policyAccepted: Boolean(currentFee?.policyAccepted),
    waiverRequested: Boolean(currentFee?.waiverRequested),
  };
  if (name === "policyAccepted") {
    const next = !current.policyAccepted;
    return {
      policyAccepted: next,
      waiverRequested: next ? false : current.waiverRequested,
    };
  }
  const next = !current.waiverRequested;
  return {
    policyAccepted: next ? false : current.policyAccepted,
    waiverRequested: next,
  };
}

function getFeeSummaryText(feeStatus) {
  if (!feeStatus?.required) {
    return "No application fee is required.";
  }
  if (feeStatus?.status === "waiver_requested") {
    return `Application fee waiver requested (${feeStatus.currency || "USD"} ${feeStatus.amount || "0"}).`;
  }
  return `Application fee due: ${feeStatus.currency || "USD"} ${feeStatus.amount || "0"}.`;
}

function SubmissionLifecyclePanels({ receipt }) {
  return (
    <>
      {Array.isArray(receipt?.status_center?.milestones) ? (
        <div className="crown-card" style={{ marginTop: 10, padding: 12, border: "1px solid var(--crown-border)" }}>
          <p style={{ margin: "0 0 8px 0", fontWeight: 600 }}>Status center</p>
          <div style={{ marginBottom: 8, color: "var(--crown-muted)", fontSize: 13 }}>
            Owner: {receipt?.status_center?.owner_team || "Admissions"} · Next update: {receipt?.status_center?.next_update_target || "Within 1 business day"}
          </div>
          <div style={{ display: "grid", gap: 6 }}>
            {receipt.status_center.milestones.map((milestone) => (
              <div key={milestone.key} style={{ color: "var(--crown-muted)", fontSize: 13 }}>
                <strong>{milestone.title}</strong> - {milestone.target} ({milestone.status})
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {Array.isArray(receipt?.documents_lifecycle) ? (
        <div className="crown-card" style={{ marginTop: 10, padding: 12, border: "1px solid var(--crown-border)" }}>
          <p style={{ margin: "0 0 8px 0", fontWeight: 600 }}>Documents lifecycle</p>
          <div style={{ display: "grid", gap: 6 }}>
            {receipt.documents_lifecycle.map((item) => (
              <div key={item.key} style={{ color: "var(--crown-muted)", fontSize: 13 }}>
                <strong>{item.label}</strong> - {item.status} · {item.next_action}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {Array.isArray(receipt?.enrollment_continuity?.checklist) ? (
        <div className="crown-card" style={{ marginTop: 10, padding: 12, border: "1px solid var(--crown-border)" }}>
          <p style={{ margin: "0 0 8px 0", fontWeight: 600 }}>Enrollment continuity</p>
          <div style={{ display: "grid", gap: 6 }}>
            {receipt.enrollment_continuity.checklist.map((item) => (
              <div key={item.key} style={{ color: "var(--crown-muted)", fontSize: 13 }}>
                <strong>{item.title}</strong> - {item.status}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}

function FeeSelectionPanel({ feeConfig, applicationFee, onToggleFee }) {
  if (!feeConfig.required) {
    return null;
  }

  return (
    <div className="crown-card" style={{ padding: 10, border: "1px solid var(--crown-border)", marginBottom: 6 }}>
      <p style={{ margin: "0 0 8px 0", fontWeight: 600 }}>
        Application fee: {feeConfig.currency} {feeConfig.amount.toFixed(2)}
      </p>
      <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <input
          type="checkbox"
          checked={Boolean(applicationFee.policyAccepted)}
          onChange={() => onToggleFee("policyAccepted")}
        />
        <span>I acknowledge the application fee policy.</span>
      </label>
      <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <input
          type="checkbox"
          checked={Boolean(applicationFee.waiverRequested)}
          onChange={() => onToggleFee("waiverRequested")}
        />
        <span>Request a fee waiver for this application.</span>
      </label>
    </div>
  );
}

function SubmitPendingPanel({
  preflight,
  submitting,
  runPreflightCheck,
  feeConfig,
  applicationFee,
  toggleApplicationFee,
  attestations,
  toggleAttestation,
  submitError,
  submitCorrelationId,
  onSubmit,
  canFinalize,
}) {
  return (
    <>
      <p style={{ marginTop: 0 }}>
        Final submission triggers a staff review workflow with human-led mission-fit discernment and
        transparent communication milestones.
      </p>
      <div
        className={preflight.status === "down" ? "crown-alert" : "crown-muted"}
        style={{ marginBottom: 10 }}
      >
        Service check: {preflight.message}
      </div>
      <button className="crown-btn" type="button" onClick={runPreflightCheck} disabled={submitting || preflight.status === "checking"}>
        {preflight.status === "checking" ? "Checking..." : "Re-check Service"}
      </button>
      <div style={{ display: "grid", gap: 8, marginBottom: 10 }}>
        <FeeSelectionPanel
          feeConfig={feeConfig}
          applicationFee={applicationFee}
          onToggleFee={toggleApplicationFee}
        />
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={Boolean(attestations.informationAccurate)}
            onChange={() => toggleAttestation("informationAccurate")}
          />
          <span>I confirm the information provided is accurate for our household. *</span>
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={Boolean(attestations.missionPartnershipUnderstood)}
            onChange={() => toggleAttestation("missionPartnershipUnderstood")}
          />
          <span>I understand admissions includes a mission-fit partnership conversation. *</span>
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={Boolean(attestations.communicationOptIn)}
            onChange={() => toggleAttestation("communicationOptIn")}
          />
          <span>Send me admissions updates by email and phone.</span>
        </label>
      </div>
      {submitError ? (
        <div className="crown-alert">
          <div>{submitError}</div>
          <div style={{ marginTop: 6, fontSize: 12 }}>
            Need immediate help? Call (555) 010-1000 or email admissions@crown.edu.
          </div>
          {submitCorrelationId ? (
            <div style={{ marginTop: 6, fontSize: 12 }}>
              Support reference: {submitCorrelationId}
            </div>
          ) : null}
        </div>
      ) : null}
      <button className="crown-btn crown-btn-primary" onClick={onSubmit} disabled={submitting || !canFinalize || preflight.status === "checking"}>
        {submitting ? "Submitting..." : "Confirm and Submit"}
      </button>
    </>
  );
}

function SubmitSuccessPanel({ receipt, submissionSummary }) {
  const paymentHandoff = receipt?.application_fee?.payment_handoff;
  return (
    <>
      <p style={{ marginTop: 0, fontWeight: 600 }}>
        Thank you. Your application has been submitted.
      </p>
      {submissionSummary ? (
        <p style={{ marginTop: 6, color: "var(--crown-muted)", fontSize: 13 }}>
          {submissionSummary}
        </p>
      ) : null}
      {receipt?.application_fee ? (
        <p style={{ marginTop: 6, color: "var(--crown-muted)", fontSize: 13 }}>
          {getFeeSummaryText(receipt.application_fee)}
        </p>
      ) : null}
      {receipt?.application_fee?.finance?.state === "invoiced" ? (
        <div className="crown-card" style={{ marginTop: 8, padding: 10, border: "1px solid var(--crown-border)" }}>
          <p style={{ margin: "0 0 6px 0", fontWeight: 600 }}>Finance processing</p>
          <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>
            Invoice reference: {receipt.application_fee.finance.invoice_id}
          </div>
          <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>
            Collection endpoint: {receipt.application_fee.finance.collection_path}
          </div>
          {paymentHandoff ? (
            <div style={{ marginTop: 8, color: "var(--crown-muted)", fontSize: 13 }}>
              Payment intent handoff ready. Sign in to continue secure payment at {paymentHandoff.endpoint}.
            </div>
          ) : null}
        </div>
      ) : null}
      <SubmissionLifecyclePanels receipt={receipt} />
      <ul style={{ color: "var(--crown-muted)", marginBottom: 0 }}>
        <li>Next update target: within 1 business day</li>
        <li>Admissions will review completeness and mission conversation notes</li>
        <li>You will receive next-step instructions by email</li>
      </ul>
    </>
  );
}

function StepSubmit({
  context,
  setContext,
  goBack,
  stepIndex,
  totalSteps,
  steps,
  onFinalizeSubmit,
  admissionsPublicConfig,
}) {
  const [submittedNow, setSubmittedNow] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [submitCorrelationId, setSubmitCorrelationId] = useState("");
  const [receipt, setReceipt] = useState(null);
  const [preflight, setPreflight] = useState({ status: "checking", message: "Checking submission service..." });

  const attestations = context.attestations || {};
  const feeConfig = normalizeFeeConfig(admissionsPublicConfig?.application_fee || FALLBACK_FEE_CONFIG);
  const applicationFee = context.applicationFee || { policyAccepted: !feeConfig.required, waiverRequested: false };
  const feeSatisfied = !feeConfig.required || applicationFee.policyAccepted || applicationFee.waiverRequested;
  const canFinalize = Boolean(
    attestations.informationAccurate &&
    attestations.missionPartnershipUnderstood &&
    feeSatisfied
  );
  const submissionSummary = buildSubmissionSummary(receipt);

  async function runPreflightCheck() {
    setPreflight({ status: "checking", message: "Checking submission service..." });
    const status = await checkSubmitServiceAvailability();
    setPreflight(status);
  }

  useEffect(() => {
    runPreflightCheck();
  }, []);

  useEffect(() => {
    if (!feeConfig.required) {
      setContext((prev) => ({
        ...prev,
        applicationFee: {
          policyAccepted: true,
          waiverRequested: false,
        },
      }));
    }
  }, [feeConfig.required, setContext]);

  function toggleAttestation(name) {
    setContext((prev) => ({
      ...prev,
      attestations: {
        ...prev.attestations,
        [name]: !prev.attestations?.[name],
      },
    }));
  }

  function toggleApplicationFee(name) {
    setContext((prev) => ({
      ...prev,
      applicationFee: toggleFeeSelection(prev.applicationFee, name),
    }));
  }

  async function handleFinalize() {
    const blockReason = getSubmitBlockReason({
      submitting,
      preflightStatus: preflight.status,
      canFinalize,
    });
    if (blockReason === "in_progress") return;

    setSubmitError("");
    setSubmitCorrelationId("");
    if (blockReason) {
      setSubmitError(blockReason);
      return;
    }
    setSubmitting(true);
    try {
      const response = await submitAdmissionsIntake(context);
      setReceipt(response);
      setContext((prev) => ({ ...prev, submitted: true }));
      if (typeof onFinalizeSubmit === "function") {
        onFinalizeSubmit();
      }
      setSubmittedNow(true);
    } catch (error) {
      const correlation = String(error?.correlationId || error?.requestId || "").trim();
      if (correlation) {
        setSubmitCorrelationId(correlation);
      }
      setSubmitError(resolveSubmitErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Application Submitted"
        subtitle="Your inquiry and application packet are now in the admissions queue."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div className="crown-card" style={{ marginTop: 16, padding: 16 }}>
        {!submittedNow && !context.submitted ? (
          <SubmitPendingPanel
            preflight={preflight}
            submitting={submitting}
            runPreflightCheck={runPreflightCheck}
            feeConfig={feeConfig}
            applicationFee={applicationFee}
            toggleApplicationFee={toggleApplicationFee}
            attestations={attestations}
            toggleAttestation={toggleAttestation}
            submitError={submitError}
            submitCorrelationId={submitCorrelationId}
            onSubmit={handleFinalize}
            canFinalize={canFinalize}
          />
        ) : (
          <SubmitSuccessPanel receipt={receipt} submissionSummary={submissionSummary} />
        )}
      </div>

      <div className="crown-wizard-actions">
        <span className="crown-muted" style={{ fontSize: 12 }}>
          Step {stepIndex + 1} of {totalSteps}
        </span>
        <div className="crown-wizard-actions-right">
          <button className="crown-btn" onClick={goBack}>Back</button>
        </div>
      </div>
    </div>
  );
}

const STEP_COMPONENTS = [
  StepInterest,
  StepInquiry,
  StepFamily,
  StepStudent,
  StepMission,
  StepDocuments,
  StepReview,
  StepSubmit,
];

export default function ProspectiveFamilyAdmissionsWizard() {
  const {
    value: draftContext,
    saveDraft,
    clearDraft,
    loaded,
    lastSavedAt,
  } = useWizardDraft("admissions-apply", INITIAL_CONTEXT);
  const [admissionsPublicConfig, setAdmissionsPublicConfig] = useState({
    application_fee: FALLBACK_FEE_CONFIG,
  });

  useEffect(() => {
    let mounted = true;
    fetchAdmissionsPublicConfig()
      .then((data) => {
        if (!mounted || !data) return;
        setAdmissionsPublicConfig((prev) => ({
          ...prev,
          ...data,
        }));
      })
      .catch(() => {
        // Keep fallback fee config when public config endpoint is unavailable.
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (!loaded) {
    return null;
  }

  function handleStartOver() {
    clearDraft();
    globalThis.location.reload();
  }

  return (
    <CrownPublicLayout
      title="Admissions Application"
      subtitle="Prospective Family Intake"
      right={(
        <button className="crown-btn" onClick={handleStartOver}>
          Start over
        </button>
      )}
      helpNotice={(
        <>
          Need help? Call Admissions at <strong>(555) 010-1000</strong> or email <strong>admissions@crown.edu</strong>.
          {" "}Your progress is saved automatically on this device.
          {lastSavedAt ? ` Last saved: ${new Date(lastSavedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}.` : ""}
        </>
      )}
    >
      <div className="crown-card" style={{ padding: "22px 24px" }}>
        <CrownWizard
          stepComponents={STEP_COMPONENTS}
          stepLabels={STEPS}
          initialContext={draftContext}
          onContextChange={saveDraft}
          stepProps={{ onFinalizeSubmit: clearDraft, admissionsPublicConfig }}
        />
      </div>
    </CrownPublicLayout>
  );
}
