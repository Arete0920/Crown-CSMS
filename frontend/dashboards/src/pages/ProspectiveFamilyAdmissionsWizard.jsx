/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useState } from "react";
import CrownPublicLayout from "../components/crown/CrownPublicLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import CrownWizardStepHeader from "../components/crown/CrownWizardStepHeader.jsx";
import { useWizardDraft } from "../hooks/useWizardDraft";
import { fetchAdmissionsPublicConfig, submitAdmissionsIntake } from "../api/admissions";
import { clearAdmissionsStartIntake, loadAdmissionsStartIntake } from "../lib/admissionsStartIntake.js";
import { markAdmissionsLifecycleStarted, markAdmissionsLifecycleSubmitted } from "../lib/admissionsLifecycleState.js";
import "../styles/crown-wizard.css";

const STEPS = [
  "Interest",
  "Inquiry",
  "Family Profile",
  "Student Profile",
  "Mission Alignment",
  "Documents",
  "Financial Aid Interest",
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
const DEFAULT_FINANCIAL_AID_FEE_AMOUNT = Number(import.meta.env.VITE_ADMISSIONS_FINANCIAL_AID_FEE_USD || "35");
const DEFAULT_ENROLLMENT_FEE_AMOUNT = Number(import.meta.env.VITE_ADMISSIONS_ENROLLMENT_FEE_USD || "250");
const DEMO_SCHOOL_NAME = (import.meta.env.VITE_DEMO_SCHOOL_NAME || "Heritage Christian Academy").trim();
const DEMO_AID_YEAR = (import.meta.env.VITE_DEMO_AID_YEAR || "2026-2027").trim();
const FALLBACK_FEE_CONFIG = {
  required: Number.isFinite(DEFAULT_APPLICATION_FEE_AMOUNT) && DEFAULT_APPLICATION_FEE_AMOUNT > 0,
  amount: Number.isFinite(DEFAULT_APPLICATION_FEE_AMOUNT) ? DEFAULT_APPLICATION_FEE_AMOUNT : 0,
  currency: "USD",
};

function feeDiscountPercentForChild(childIndex) {
  if (childIndex <= 1) return 0;
  if (childIndex === 2) return 25;
  if (childIndex === 3) return 50;
  if (childIndex === 4) return 75;
  return 100;
}

function applyFeeDiscount(amount, childIndex) {
  const numeric = Number(amount || 0);
  const percent = feeDiscountPercentForChild(childIndex);
  const discounted = numeric * (1 - (percent / 100));
  return Math.max(0, Number(discounted.toFixed(2)));
}

function formatCurrency(value, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(Number(value || 0));
}

function buildHouseholdFeePreview({ context, feeConfig }) {
  const students = Array.isArray(context?.students) ? context.students : [];
  const aidIntent = String(context?.financialAidInterest?.intent || "").trim().toLowerCase();
  const appFeeAmount = Number(feeConfig?.amount || DEFAULT_APPLICATION_FEE_AMOUNT);
  const aidFeeAmount = Number(DEFAULT_FINANCIAL_AID_FEE_AMOUNT);
  const enrollmentFeeAmount = Number(DEFAULT_ENROLLMENT_FEE_AMOUNT);

  return students.map((student, index) => {
    const childIndex = index + 1;
    const discountPercent = feeDiscountPercentForChild(childIndex);
    const applicationFee = applyFeeDiscount(appFeeAmount, childIndex);
    const financialAidFee = aidIntent === "applying" ? applyFeeDiscount(aidFeeAmount, childIndex) : 0;
    const enrollmentFee = applyFeeDiscount(enrollmentFeeAmount, childIndex);
    return {
      childIndex,
      studentName: `${String(student?.firstName || "").trim()} ${String(student?.lastName || "").trim()}`.trim() || `Child ${childIndex}`,
      discountPercent,
      applicationFee,
      financialAidFee,
      enrollmentFee,
      total: Number((applicationFee + financialAidFee + enrollmentFee).toFixed(2)),
    };
  });
}

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

const STUDENT_INTEREST_ACTIVITY_OPTIONS = [
  "Reading",
  "Choir",
  "Team sports",
  "Visual art",
  "Instrumental music",
  "STEM and robotics",
  "Theater and drama",
  "Service and volunteering",
];

const SUPPORT_NEEDS_OPTIONS = [
  "Reading support",
  "Math support",
  "Executive functioning support",
  "Speech and language support",
  "Social-emotional support",
  "ESL/ELL support",
];

const MISSION_ALIGNMENT_OPTIONS = [
  "Value Christian education",
  "Spiritual formation",
  "Discipleship",
  "Christian service",
  "Biblical worldview development",
  "Christ-centered character and leadership",
];

const CHURCH_ATTENDANCE_OPTIONS = [
  "Weekly",
  "Two to three times per month",
  "Monthly",
  "Occasionally",
  "Not currently attending",
];

const COMMITMENT_TO_CHRIST_OPTIONS = [
  "Parent or guardian professes faith in Christ",
  "Family is actively exploring Christian faith",
  "Family supports Christ-centered education but is still discerning",
];

const PORTRAIT_RUBRIC_ITEMS = [
  { key: "christ_centered_identity", label: "Christ-centered identity" },
  { key: "biblical_worldview", label: "Biblical worldview" },
  { key: "servant_leadership", label: "Servant leadership" },
  { key: "academic_readiness", label: "Academic readiness" },
  { key: "community_impact", label: "Community impact" },
];

function normalizePortraitScore(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  if (numeric < 1 || numeric > 5) return 0;
  return Math.round(numeric);
}

function normalizePortraitRatings(ratings) {
  const source = ratings && typeof ratings === "object" ? ratings : {};
  const normalized = {};
  PORTRAIT_RUBRIC_ITEMS.forEach((item) => {
    normalized[item.key] = normalizePortraitScore(source[item.key]);
  });
  return normalized;
}

function hasCompletePortraitRatings(ratings) {
  const normalized = normalizePortraitRatings(ratings);
  return PORTRAIT_RUBRIC_ITEMS.every((item) => normalized[item.key] >= 1);
}

function computePortraitPercent(ratings) {
  const normalized = normalizePortraitRatings(ratings);
  const total = PORTRAIT_RUBRIC_ITEMS.reduce((sum, item) => sum + normalized[item.key], 0);
  const max = PORTRAIT_RUBRIC_ITEMS.length * 5;
  if (max <= 0) return 0;
  return Math.round((total / max) * 100);
}

function getMissionRatingsContainer(mission, key) {
  const source = mission?.[key];
  return source && typeof source === "object" ? source : {};
}

function normalizeMissionAlignment(value) {
  const normalized = normalizeMultiSelect(value);
  return normalized.filter((item) => MISSION_ALIGNMENT_OPTIONS.includes(item));
}

function normalizeMultiSelect(value) {
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }

  if (typeof value === "string") {
    const normalized = value.trim();
    if (!normalized) return [];
    return normalized
      .split(/[,;]+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}

function getSelectMultipleValues(event) {
  return Array.from(event.target.selectedOptions).map((option) => option.value);
}

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
    interestsAndActivities: [],
    supportNeeds: [],
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
    churchAttendance: "",
    commitmentToChrist: "",
    spiritualLifeComments: "",
    alignmentFocus: [],
    comments: "",
    guardianPortraitRatings: {},
    studentPortraitRatings: {},
  },
  documents: {
    transcriptReady: false,
    recommendationsReady: false,
    pastorReferenceReady: false,
    immunizationReady: false,
  },
  financialAidInterest: {
    intent: "",
    note: "",
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

const IS_SANDBOX_FLOW = Boolean(
  import.meta.env.VITE_DEMO_MODE === "sandbox"
  || import.meta.env.VITE_SANDBOX_MODE === "1"
);
const IS_DEMO_PREFILL_MODE = Boolean(
  IS_SANDBOX_FLOW
  && (String(import.meta.env.VITE_ADMISSIONS_DEMO_PREFILL || "").trim() === "1"
    || String(import.meta.env.VITE_ADMISSIONS_DEMO_PREFILL || "").trim().toLowerCase() === "true")
);

const DEMO_PRIMARY_STUDENT_ID = createLocalId("student");

const DEMO_INITIAL_CONTEXT = {
  ...INITIAL_CONTEXT,
  inquiry: {
    campus: "Heritage Christian Academy",
    startTerm: "2026-2027",
    heardAbout: "Current family",
    preferredTourWindow: "Weekday mornings",
    preferredInterviewMode: "In person",
  },
  family: {
    guardians: [
      {
        id: createLocalId("guardian"),
        relationship: "Mother",
        relationshipOther: "",
        guardianName: "Jordan Reed",
        email: "parent@crown-demo.local",
        phone: "555-010-1101",
        isPrimary: true,
      },
      {
        id: createLocalId("guardian"),
        relationship: "Father",
        relationshipOther: "",
        guardianName: "Casey Reed",
        email: "guardian2@heritage.example.org",
        phone: "555-010-1102",
        isPrimary: false,
      },
    ],
    churchAffiliation: "Attend regularly",
    churchAffiliationOther: "",
  },
  students: [
    {
      id: DEMO_PRIMARY_STUDENT_ID,
      firstName: "Avery",
      lastName: "Reed",
      gradeApplyingFor: "6",
      currentSchool: "Christian school",
      currentSchoolOther: "",
      interestsAndActivities: ["Reading", "Choir", "Service and volunteering"],
      supportNeeds: [],
    },
  ],
  mission: {
    covenantPartnership: true,
    discipleshipCommitment: true,
    serviceMindset: true,
    churchAttendance: "Weekly",
    commitmentToChrist: "Parent or guardian professes faith in Christ",
    spiritualLifeComments: "Our family attends church regularly and wants school to reinforce discipleship, biblical worldview, and daily Christian formation.",
    alignmentFocus: ["Spiritual formation", "Discipleship"],
    comments: "Spiritual formation, Discipleship",
    guardianPortraitRatings: {},
    studentPortraitRatings: {
      [DEMO_PRIMARY_STUDENT_ID]: {
        christ_centered_identity: 4,
        biblical_worldview: 4,
        servant_leadership: 3,
        academic_readiness: 4,
        community_impact: 3,
      },
    },
  },
  documents: {
    transcriptReady: true,
    recommendationsReady: true,
    pastorReferenceReady: true,
    immunizationReady: true,
  },
  financialAidInterest: {
    intent: "applying",
    note: "Family plans to complete aid application after admissions submit.",
  },
  attestations: {
    informationAccurate: true,
    missionPartnershipUnderstood: true,
    communicationOptIn: true,
  },
};

function splitFullName(fullName) {
  const normalized = String(fullName || "").trim();
  if (!normalized) {
    return { firstName: "", lastName: "" };
  }
  const parts = normalized.split(/\s+/).filter(Boolean);
  if (parts.length === 1) {
    return { firstName: parts[0], lastName: "" };
  }
  return {
    firstName: parts[0],
    lastName: parts.slice(1).join(" "),
  };
}

function mergeStartIntakeIntoContext(context, intake) {
  if (!intake || typeof intake !== "object") {
    return context;
  }

  const merged = { ...context };
  const inquiry = intake.inquiry || {};
  const family = intake.family || {};
  const student = intake.student || {};

  merged.inquiry = {
    ...merged.inquiry,
    campus: String(merged.inquiry?.campus || inquiry.campus || "").trim(),
    startTerm: String(merged.inquiry?.startTerm || inquiry.startTerm || "").trim(),
    heardAbout: String(merged.inquiry?.heardAbout || inquiry.heardAbout || "").trim(),
    preferredTourWindow: String(merged.inquiry?.preferredTourWindow || inquiry.preferredTourWindow || "").trim(),
    preferredInterviewMode: String(merged.inquiry?.preferredInterviewMode || inquiry.preferredInterviewMode || "").trim(),
  };

  const guardians = Array.isArray(merged.family?.guardians) && merged.family.guardians.length > 0
    ? [...merged.family.guardians]
    : [createGuardian(true)];

  const primaryGuardianIndex = guardians.findIndex((guardian) => guardian?.isPrimary);
  const guardianIndex = Math.max(primaryGuardianIndex, 0);
  const primaryGuardian = guardians[guardianIndex] || createGuardian(true);
  guardians[guardianIndex] = {
    ...primaryGuardian,
    guardianName: String(primaryGuardian.guardianName || family.parentName || "").trim(),
    email: String(primaryGuardian.email || family.email || "").trim(),
    phone: String(primaryGuardian.phone || family.phone || "").trim(),
    isPrimary: true,
  };

  merged.family = {
    ...merged.family,
    guardians,
  };

  const students = Array.isArray(merged.students) && merged.students.length > 0
    ? [...merged.students]
    : [createStudent()];
  const firstStudent = students[0] || createStudent();
  const guardianNameParts = splitFullName(family.parentName);
  students[0] = {
    ...firstStudent,
    gradeApplyingFor: String(firstStudent.gradeApplyingFor || student.gradeApplyingFor || "").trim(),
    lastName: String(firstStudent.lastName || guardianNameParts.lastName || "").trim(),
  };

  merged.students = students;
  return merged;
}

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

function buildJourneyStageSnapshot(context, stepIndex) {
  const inquiry = context?.inquiry || {};
  const family = context?.family || {};
  const students = context?.students || [];
  const documents = context?.documents || {};
  const mission = context?.mission || {};

  const guardiansComplete = Array.isArray(family.guardians) && family.guardians.length > 0
    && family.guardians.every(isGuardianComplete);
  const studentsComplete = Array.isArray(students) && students.length > 0
    && students.every(isStudentComplete);
  const documentsReady = Object.values(documents).filter(Boolean).length;

  if (stepIndex <= 1) {
    return {
      stage: "Inquiry and Exploration",
      familyAction: String(inquiry.campus || "").trim() && String(inquiry.startTerm || "").trim()
        ? "Confirm tour and interview preferences so admissions can personalize your follow-up."
        : "Choose your campus and start term so we can route your family to the right admissions path.",
      staffAction: "Assign counselor, send welcome guidance, and invite the family into the next admissions touchpoint.",
      visibility: "You should always know what happens next, who owns your file, and the first action to take.",
    };
  }

  if (stepIndex <= 3) {
    return {
      stage: "Household Profile Completion",
      familyAction: guardiansComplete && studentsComplete
        ? "Review interests, activities, support needs, and household details before moving into mission alignment."
        : "Complete guardian and student profiles so admissions can guide your family without duplicate follow-up.",
      staffAction: "Prepare a household-level view, watch for inactivity, and keep the next required action visible.",
      visibility: "Strong funnels keep progress obvious instead of burying families inside a giant form.",
    };
  }

  if (stepIndex <= 5) {
    return {
      stage: "Mission Alignment and Readiness",
      familyAction: mission.covenantPartnership && mission.discipleshipCommitment
        ? "Confirm your document readiness and get ready for a transparent human-led review."
        : "Complete the partnership commitments so the next conversation is about fit, formation, and support.",
      staffAction: "Prepare mission-fit review context and identify any missing readiness items before submit.",
      visibility: `Document readiness currently shows ${documentsReady}/4 items ready.`,
    };
  }

  if (stepIndex === 6) {
    return {
      stage: "Application Review and Submit",
      familyAction: "Review your household snapshot, then submit so admissions can begin file completion and interview coordination.",
      staffAction: "Trigger the post-submit workflow, ownership assignment, and milestone communications.",
      visibility: "Families should see the next milestone, the owner, and the expected response window before they submit.",
    };
  }

  return {
    stage: "Post-Submit Status Center",
    familyAction: "Use the status center and checklist below to track milestones, documents, and the next admissions action.",
    staffAction: "Maintain visible milestone updates, follow-up ownership, and enrollment continuity.",
    visibility: "The funnel should now feel like an ongoing guided journey, not a black-box handoff.",
  };
}

function JourneyStagePanel({ context, stepIndex }) {
  const snapshot = buildJourneyStageSnapshot(context, stepIndex);

  return (
    <div
      style={{
        border: "1px solid var(--crown-border)",
        borderRadius: 8,
        padding: "10px 12px",
        marginBottom: 12,
        background: "var(--crown-bg, #f8fafc)",
      }}
    >
      <div style={{ marginBottom: 6, fontSize: 12, color: "var(--crown-muted)" }}>
        Current journey stage
      </div>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>{snapshot.stage}</div>
      <div style={{ display: "grid", gap: 6, fontSize: 13, color: "var(--crown-muted)" }}>
        <div><strong>Your next action:</strong> {snapshot.familyAction}</div>
        <div><strong>Admissions next action:</strong> {snapshot.staffAction}</div>
        <div><strong>Why this matters:</strong> {snapshot.visibility}</div>
      </div>
    </div>
  );
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
        <JourneyStagePanel context={context || {}} stepIndex={stepIndex} />
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
        <li>Mission, spiritual-life, and church-partnership conversation</li>
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
      interestsAndActivities: normalizeMultiSelect(student.interestsAndActivities ?? student.strengths),
      supportNeeds: normalizeMultiSelect(student.supportNeeds),
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
                <span style={{ display: "block", marginBottom: 4 }}>Student Interests and Activities</span>
                <select
                  className="crown-input"
                  multiple
                  size={Math.min(STUDENT_INTEREST_ACTIVITY_OPTIONS.length, 6)}
                  value={student.interestsAndActivities || []}
                  onChange={(e) => updateStudent(index, "interestsAndActivities", getSelectMultipleValues(e))}
                >
                  {STUDENT_INTEREST_ACTIVITY_OPTIONS.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
                <span style={{ display: "block", marginTop: 4, color: "var(--crown-muted)", fontSize: 12 }}>
                  Hold Ctrl (Windows) or Command (Mac) to select multiple.
                </span>
              </label>

              <label>
                <span style={{ display: "block", marginBottom: 4 }}>Support Needs (if any)</span>
                <select
                  className="crown-input"
                  multiple
                  size={Math.min(SUPPORT_NEEDS_OPTIONS.length, 6)}
                  value={student.supportNeeds || []}
                  onChange={(e) => updateStudent(index, "supportNeeds", getSelectMultipleValues(e))}
                >
                  {SUPPORT_NEEDS_OPTIONS.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
                <span style={{ display: "block", marginTop: 4, color: "var(--crown-muted)", fontSize: 12 }}>
                  Select all that apply.
                </span>
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
  const students = Array.isArray(context?.students) ? context.students : [];
  const selectedAlignmentFocus = normalizeMissionAlignment(mission.alignmentFocus ?? mission.comments);
  const studentPortraitRatings = getMissionRatingsContainer(mission, "studentPortraitRatings");
  const studentPortraitComplete = students.every((student, index) => {
    const studentId = String(student?.id || `student-${index}`).trim();
    return hasCompletePortraitRatings(studentPortraitRatings[studentId]);
  });

  const respondentPercents = students.map((student, index) => {
      const studentId = String(student?.id || `student-${index}`).trim();
      return computePortraitPercent(studentPortraitRatings[studentId]);
    }).filter((value) => Number.isFinite(value) && value > 0);

  const studentPortraitScore = respondentPercents.length > 0
    ? Math.round(respondentPercents.reduce((sum, value) => sum + value, 0) / respondentPercents.length)
    : 0;

  const canContinue = mission.covenantPartnership
    && mission.discipleshipCommitment
    && Boolean(String(mission.churchAttendance || "").trim())
    && Boolean(String(mission.commitmentToChrist || "").trim())
    && selectedAlignmentFocus.length > 0
    && studentPortraitComplete;

  function toggle(name) {
    setContext((prev) => ({
      ...prev,
      mission: { ...prev.mission, [name]: !prev.mission[name] },
    }));
  }

  function updateAlignmentFocus(values) {
    const normalized = normalizeMissionAlignment(values);
    setContext((prev) => ({
      ...prev,
      mission: {
        ...prev.mission,
        alignmentFocus: normalized,
        comments: normalized.join(", "),
      },
    }));
  }

  function updatePortraitScore(groupKey, profileId, rubricKey, value) {
    const normalizedId = String(profileId || "").trim();
    if (!normalizedId) {
      return;
    }
    const score = normalizePortraitScore(value);
    setContext((prev) => {
      const missionSource = prev.mission || {};
      const currentContainer = getMissionRatingsContainer(missionSource, groupKey);
      const currentProfile = normalizePortraitRatings(currentContainer[normalizedId]);
      return {
        ...prev,
        mission: {
          ...missionSource,
          [groupKey]: {
            ...currentContainer,
            [normalizedId]: {
              ...currentProfile,
              [rubricKey]: score,
            },
          },
        },
      };
    });
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
          <span style={{ display: "block", marginBottom: 4 }}>Church attendance *</span>
          <select
            className="crown-input"
            value={mission.churchAttendance || ""}
            onChange={(e) => setContext((prev) => ({
              ...prev,
              mission: { ...prev.mission, churchAttendance: e.target.value },
            }))}
          >
            <option value="">Select one</option>
            {CHURCH_ATTENDANCE_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>
        <label>
          <span style={{ display: "block", marginBottom: 4 }}>Commitment to Christ *</span>
          <select
            className="crown-input"
            value={mission.commitmentToChrist || ""}
            onChange={(e) => setContext((prev) => ({
              ...prev,
              mission: { ...prev.mission, commitmentToChrist: e.target.value },
            }))}
          >
            <option value="">Select one</option>
            {COMMITMENT_TO_CHRIST_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>
        <label>
          <span style={{ display: "block", marginBottom: 4 }}>Spiritual life at home or church (optional)</span>
          <textarea
            className="crown-input"
            rows={3}
            value={mission.spiritualLifeComments || ""}
            onChange={(e) => setContext((prev) => ({
              ...prev,
              mission: { ...prev.mission, spiritualLifeComments: e.target.value },
            }))}
            placeholder="Share how your family approaches church attendance, discipleship, prayer, or Christian formation."
          />
        </label>
        <label>
          <span style={{ display: "block", marginBottom: 4 }}>Family mission alignment focus *</span>
          <select
            className="crown-input"
            multiple
            size={Math.min(MISSION_ALIGNMENT_OPTIONS.length, 6)}
            value={selectedAlignmentFocus}
            onChange={(e) => updateAlignmentFocus(getSelectMultipleValues(e))}
          >
            {MISSION_ALIGNMENT_OPTIONS.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
          <span style={{ display: "block", marginTop: 4, color: "var(--crown-muted)", fontSize: 12 }}>
            Select the areas that best describe why your family is pursuing Christ-centered education. Hold Ctrl (Windows) or Command (Mac) to select multiple.
          </span>
        </label>

        <div className="crown-card" style={{ padding: 12, border: "1px solid var(--crown-border)" }}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Student Portrait of the Graduate reflection</div>
          <div style={{ color: "var(--crown-muted)", fontSize: 13, marginBottom: 8 }}>
            Admissions should evaluate the student against the Portrait of the Graduate. Parents should answer spiritual-life and commitment questions, not portrait scoring for themselves.
          </div>

          <div style={{ display: "grid", gap: 12 }}>
            {students.map((student, index) => {
              const studentId = String(student?.id || `student-${index}`).trim();
              const ratings = normalizePortraitRatings(studentPortraitRatings[studentId]);
              const studentName = `${String(student?.firstName || "").trim()} ${String(student?.lastName || "").trim()}`.trim() || `Student ${index + 1}`;
              return (
                <div key={studentId} style={{ border: "1px solid var(--crown-border)", borderRadius: 8, padding: 10 }}>
                  <div style={{ fontWeight: 600, marginBottom: 8 }}>{studentName} (Student)</div>
                  <div style={{ display: "grid", gap: 8 }}>
                    {PORTRAIT_RUBRIC_ITEMS.map((rubric) => (
                      <label key={rubric.key}>
                        <span style={{ display: "block", marginBottom: 4 }}>{rubric.label} *</span>
                        <select
                          className="crown-input"
                          value={ratings[rubric.key] || ""}
                          onChange={(e) => updatePortraitScore("studentPortraitRatings", studentId, rubric.key, e.target.value)}
                        >
                          <option value="">Select score</option>
                          <option value="1">1 - Emerging</option>
                          <option value="2">2 - Developing</option>
                          <option value="3">3 - Proficient</option>
                          <option value="4">4 - Strong</option>
                          <option value="5">5 - Exemplary</option>
                        </select>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ marginTop: 10, fontSize: 13 }}>
            Student portrait readiness score: <strong>{studentPortraitScore}%</strong>
          </div>
        </div>
      </div>
    </StepFrame>
  );
}

function StepDocuments({ context, setContext, ...props }) {
  const docs = context.documents;
  const completionCount = Object.values(docs).filter(Boolean).length;
  const canContinue = completionCount === 4;

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
      subtitle="All required documents must be marked ready before review."
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
      {canContinue ? null : (
        <p className="crown-alert" style={{ marginTop: 8 }}>
          Review stays locked until all four required document items are ready.
        </p>
      )}
    </StepFrame>
  );
}

function StepFinancialAidInterest({ context, setContext, ...props }) {
  const financialAidInterest = context.financialAidInterest || { intent: "", note: "" };
  const canContinue = Boolean(String(financialAidInterest.intent || "").trim());

  useEffect(() => {
    if (String(financialAidInterest.intent || "").trim()) {
      return;
    }
    setContext((prev) => ({
      ...prev,
      financialAidInterest: {
        intent: "undecided",
        note: prev.financialAidInterest?.note || "",
      },
    }));
  }, [financialAidInterest.intent, setContext]);

  function update(name, value) {
    setContext((prev) => ({
      ...prev,
      financialAidInterest: {
        ...prev.financialAidInterest,
        [name]: value,
      },
    }));
  }

  return (
    <StepFrame
      {...props}
      context={context}
      title="Financial Aid Interest"
      subtitle="Tell us whether your family plans to apply for aid so the next steps and contract timeline stay clear."
      canContinue={canContinue}
    >
      <div style={{ display: "grid", gap: 10 }}>
        <label>
          <input
            type="radio"
            name="financialAidIntent"
            checked={financialAidInterest.intent === "applying"}
            onChange={() => update("intent", "applying")}
          />{" "}
          We plan to apply for financial aid.
        </label>
        <label>
          <input
            type="radio"
            name="financialAidIntent"
            checked={financialAidInterest.intent === "not_applying"}
            onChange={() => update("intent", "not_applying")}
          />{" "}
          We are not applying for financial aid.
        </label>
        <label>
          <input
            type="radio"
            name="financialAidIntent"
            checked={financialAidInterest.intent === "undecided"}
            onChange={() => update("intent", "undecided")}
          />{" "}
          We are undecided and need guidance.
        </label>

        <label>
          <span style={{ display: "block", marginBottom: 4 }}>Financial aid notes (optional)</span>
          <textarea
            className="crown-input"
            value={financialAidInterest.note || ""}
            onChange={(e) => update("note", e.target.value)}
            rows={3}
            placeholder="Share timing or document questions so admissions can route you quickly."
          />
        </label>
      </div>
    </StepFrame>
  );
}

function financialAidIntentLabel(intent) {
  if (intent === "applying") {
    return "Applying";
  }
  if (intent === "not_applying") {
    return "Not applying";
  }
  if (intent === "undecided") {
    return "Undecided";
  }
  return "Not provided";
}

function StepReview({ context, ...props }) {
  const feeConfig = normalizeFeeConfig(props?.admissionsPublicConfig?.application_fee || FALLBACK_FEE_CONFIG);
  const summary = useMemo(
    () => ({
      inquiry: context.inquiry,
      family: context.family,
      students: context.students,
      mission: context.mission,
      documents: context.documents,
      financialAidInterest: context.financialAidInterest,
      feeRows: buildHouseholdFeePreview({ context, feeConfig }),
      feeCurrency: feeConfig.currency || "USD",
    }),
    [context, feeConfig]
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
          <div>Financial aid intent: {financialAidIntentLabel(summary.financialAidInterest?.intent)}</div>
        </div>
      </div>

      <div className="crown-card" style={{ padding: 12, marginBottom: 12, border: "1px solid var(--crown-border)" }}>
        <p style={{ margin: "0 0 8px 0", fontWeight: 600 }}>Fee Schedule (Application, Financial Aid, Enrollment)</p>
        <div style={{ color: "var(--crown-muted)", fontSize: 13, marginBottom: 8 }}>
          Multi-child discounts: 2nd child 25% off, 3rd child 50% off, 4th child 75% off, 5th+ free.
        </div>
        <div style={{ display: "grid", gap: 8 }}>
          {summary.feeRows.map((row) => (
            <div key={`fee-row-${row.childIndex}`} style={{ border: "1px solid var(--crown-border)", borderRadius: 8, padding: 10 }}>
              <div style={{ fontWeight: 600 }}>{row.studentName} (Child {row.childIndex})</div>
              <div style={{ color: "var(--crown-muted)", fontSize: 13, marginTop: 4 }}>Discount: {row.discountPercent}%</div>
              <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>Application fee: {formatCurrency(row.applicationFee, summary.feeCurrency)}</div>
              <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>Financial aid fee: {formatCurrency(row.financialAidFee, summary.feeCurrency)}</div>
              <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>Enrollment fee: {formatCurrency(row.enrollmentFee, summary.feeCurrency)}</div>
              <div style={{ marginTop: 4 }}>Total: <strong>{formatCurrency(row.total, summary.feeCurrency)}</strong></div>
            </div>
          ))}
        </div>
      </div>

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
    const response = await globalThis.fetch("/api/v1/admissions/submit/", {
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
        When you submit, our admissions team will begin reviewing your application and follow up with next steps.
      </p>
      <div
        className={preflight.status === "down" ? "crown-alert" : "crown-muted"}
        style={{ marginBottom: 10 }}
      >
        Submission status: {preflight.message}
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
      <ul style={{ color: "var(--crown-muted)", marginBottom: 10 }}>
        <li>Admissions will contact you within 1 business day.</li>
        <li>Upload any remaining records from your checklist link.</li>
        <li>Watch your email and text messages for interview and next-step instructions.</li>
      </ul>
      <div className="crown-card" style={{ padding: 10, border: "1px solid var(--crown-border)" }}>
        <p style={{ margin: "0 0 6px 0", fontWeight: 600 }}>Need help?</p>
        <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>
          Call (555) 010-1000 or email admissions@crown.edu.
        </div>
      </div>
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
      const submitPayload = {
        ...context,
        demoChecklistAutoComplete: IS_SANDBOX_FLOW,
      };
      const response = await submitAdmissionsIntake(submitPayload);
      const checklistHub = response?.checklist_hub;
      markAdmissionsLifecycleSubmitted({
        applicationId: checklistHub?.application_id,
        checklistKey: checklistHub?.checklist_key,
      });
      setReceipt(response);
      setContext((prev) => ({ ...prev, submitted: true }));
      if (typeof onFinalizeSubmit === "function") {
        onFinalizeSubmit();
      }

      if (checklistHub?.path && checklistHub?.application_id && checklistHub?.checklist_key) {
        const target = `${checklistHub.path}?application_id=${encodeURIComponent(checklistHub.application_id)}&checklist_key=${encodeURIComponent(checklistHub.checklist_key)}&demo_flow=${IS_SANDBOX_FLOW ? "1" : "0"}`;
        globalThis.location.href = target;
        return;
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
  StepFinancialAidInterest,
  StepReview,
  StepSubmit,
];

export default function ProspectiveFamilyAdmissionsWizard() {
  const draftKey = IS_DEMO_PREFILL_MODE ? "admissions-apply-demo" : "admissions-apply";

  const initialDraftContext = useMemo(
    () => (IS_DEMO_PREFILL_MODE ? DEMO_INITIAL_CONTEXT : INITIAL_CONTEXT),
    [],
  );

  const {
    value: draftContext,
    setValue: setDraftContext,
    saveDraft,
    clearDraft,
    loaded,
    lastSavedAt,
  } = useWizardDraft(draftKey, initialDraftContext);
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

  useEffect(() => {
    if (!loaded || !IS_DEMO_PREFILL_MODE) return;

    const firstGuardian = draftContext?.family?.guardians?.[0] || {};
    const firstStudent = draftContext?.students?.[0] || {};
    const isEffectivelyBlank = !String(draftContext?.inquiry?.campus || "").trim()
      && !String(firstGuardian.guardianName || "").trim()
      && !String(firstGuardian.email || "").trim()
      && !String(firstStudent.firstName || "").trim()
      && !String(firstStudent.lastName || "").trim();

    if (!isEffectivelyBlank) return;

    setDraftContext(DEMO_INITIAL_CONTEXT);
    saveDraft(DEMO_INITIAL_CONTEXT);
  }, [loaded, draftContext, saveDraft, setDraftContext]);

  useEffect(() => {
    if (!loaded) return;
    const intake = loadAdmissionsStartIntake();
    if (!intake) return;

    const merged = mergeStartIntakeIntoContext(draftContext, intake);
    setDraftContext(merged);
    saveDraft(merged);
    clearAdmissionsStartIntake();
  }, [loaded, draftContext, saveDraft, setDraftContext]);

  useEffect(() => {
    if (!loaded) return;
    markAdmissionsLifecycleStarted("admissions_wizard");
  }, [loaded]);

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
          {" "}Sandbox school: <strong>{DEMO_SCHOOL_NAME}</strong> ({DEMO_AID_YEAR}).
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

