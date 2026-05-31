export const DATA_STATES = Object.freeze({
  LIVE: 'live',
  FALLBACK: 'fallback',
  SAMPLE: 'sample',
  LOADING: 'loading',
  UNAVAILABLE: 'unavailable',
  STALE: 'stale',
});

export const MODULE_KPI_CATALOG = Object.freeze({
  attendance: {
    sourceLabel: 'Attendance operating feed',
    metrics: [
      { key: 'dailyAttendanceRate', label: 'Daily Attendance Rate', format: 'percent', accent: 'emerald' },
      { key: 'missingSubmissions', label: 'Missing Attendance', format: 'number', accent: 'gold', warnAbove: 0 },
      { key: 'chronicAbsenceRisk', label: 'Chronic Absence Risk', format: 'number', accent: 'navy', warnAbove: 0 },
      { key: 'tardyEvents', label: 'Tardy Events', format: 'number', accent: 'blue' },
    ],
    actions: [
      { key: 'missingSubmissions', title: 'Resolve missing attendance submissions', detail: 'Teacher sections without posted attendance.' },
      { key: 'chronicAbsenceRisk', title: 'Review chronic absence risk list', detail: 'Students crossing risk thresholds.' },
    ],
  },

  billing: {
    sourceLabel: 'Billing operating feed',
    metrics: [
      { key: 'outstandingAr', label: 'Outstanding A/R', format: 'currency', accent: 'gold', warnAbove: 0 },
      { key: 'failedPayments', label: 'Failed Payments', format: 'number', accent: 'navy', warnAbove: 0 },
      { key: 'upcomingDrafts', label: 'Upcoming Drafts', format: 'number', accent: 'blue' },
      { key: 'reconciliationExceptions', label: 'Reconciliation Exceptions', format: 'number', accent: 'gold', warnAbove: 0 },
    ],
    actions: [
      { key: 'failedPayments', title: 'Work failed payment queue', detail: 'Retry, contact, or adjust payment plan.' },
      { key: 'reconciliationExceptions', title: 'Clear reconciliation exceptions', detail: 'Match provider deposits to CROWN records.' },
    ],
  },

  financialAid: {
    sourceLabel: 'Financial aid operating feed',
    metrics: [
      { key: 'applicationsInReview', label: 'Aid In Review', format: 'number', accent: 'blue', warnAbove: 0 },
      { key: 'aidBudgetRemaining', label: 'Aid Budget Remaining', format: 'currency', accent: 'emerald' },
      { key: 'awardLettersPending', label: 'Award Letters Pending', format: 'number', accent: 'gold', warnAbove: 0 },
      { key: 'familyAffordabilityRisk', label: 'Affordability Risk', format: 'number', accent: 'navy', warnAbove: 0 },
    ],
    actions: [
      { key: 'applicationsInReview', title: 'Complete aid reviews', detail: 'Families waiting on award decisions.' },
      { key: 'awardLettersPending', title: 'Issue pending award letters', detail: 'Awards ready for family communication.' },
    ],
  },

  admissions: {
    sourceLabel: 'Admissions summary API',
    metrics: [
      { key: 'openApplications', label: 'Open Applications', format: 'number', accent: 'blue' },
      { key: 'submittedAwaitingReview', label: 'Awaiting Review', format: 'number', accent: 'gold', warnAbove: 0 },
      { key: 'acceptedNotEnrolled', label: 'Accepted Not Enrolled', format: 'number', accent: 'navy', warnAbove: 0 },
      { key: 'maxStageAgeDays', label: 'Max Stage Age', format: 'days', accent: 'gold', warnAbove: 3 },
    ],
    actions: [
      { key: 'submittedAwaitingReview', title: 'Review submitted applications', detail: 'Protect admissions decision turnaround.' },
      { key: 'acceptedNotEnrolled', title: 'Follow up accepted families', detail: 'Move accepted students into enrollment.' },
      { key: 'maxStageAgeDays', title: 'Clear stale admissions stages', detail: 'Applicants aging beyond service expectations.' },
    ],
  },

  registrar: {
    sourceLabel: 'Registrar operating feed',
    metrics: [
      { key: 'transcriptRequests', label: 'Transcript Requests', format: 'number', accent: 'blue', warnAbove: 0 },
      { key: 'recordExceptions', label: 'Record Exceptions', format: 'number', accent: 'gold', warnAbove: 0 },
      { key: 'enrollmentChanges', label: 'Enrollment Changes', format: 'number', accent: 'navy' },
      { key: 'missingDocuments', label: 'Missing Documents', format: 'number', accent: 'gold', warnAbove: 0 },
    ],
    actions: [
      { key: 'recordExceptions', title: 'Resolve record exceptions', detail: 'Student records needing registrar correction.' },
      { key: 'missingDocuments', title: 'Request missing documents', detail: 'Files blocking complete student records.' },
    ],
  },

  gradebook: {
    sourceLabel: 'Gradebook operating feed',
    metrics: [
      { key: 'missingGrades', label: 'Missing Grades', format: 'number', accent: 'gold', warnAbove: 0 },
      { key: 'studentsAtRisk', label: 'Students At Risk', format: 'number', accent: 'navy', warnAbove: 0 },
      { key: 'reportCardReadiness', label: 'Report Card Readiness', format: 'percent', accent: 'emerald' },
      { key: 'lateAssignments', label: 'Late Assignments', format: 'number', accent: 'blue' },
    ],
    actions: [
      { key: 'missingGrades', title: 'Post missing grades', detail: 'Assignments or terms missing grade entries.' },
      { key: 'studentsAtRisk', title: 'Review academic risk students', detail: 'Students requiring intervention.' },
    ],
  },

  communications: {
    sourceLabel: 'Communications operating feed',
    metrics: [
      { key: 'deliveryFailures', label: 'Delivery Failures', format: 'number', accent: 'gold', warnAbove: 0 },
      { key: 'unreadParentMessages', label: 'Unread Parent Messages', format: 'number', accent: 'blue', warnAbove: 0 },
      { key: 'campaignsScheduled', label: 'Scheduled Campaigns', format: 'number', accent: 'navy' },
      { key: 'emergencyReach', label: 'Emergency Reach', format: 'percent', accent: 'emerald' },
    ],
    actions: [
      { key: 'deliveryFailures', title: 'Fix delivery failures', detail: 'Messages that did not reach intended recipients.' },
      { key: 'unreadParentMessages', title: 'Respond to unread parent messages', detail: 'Open family communication items.' },
    ],
  },

  platformOperations: {
    sourceLabel: 'Platform operations feed',
    metrics: [
      { key: 'tenantHealthScore', label: 'Tenant Health Score', format: 'percent', accent: 'emerald' },
      { key: 'failedJobs', label: 'Failed Jobs', format: 'number', accent: 'gold', warnAbove: 0 },
      { key: 'apiP95Ms', label: 'API p95', format: 'milliseconds', accent: 'blue', warnAbove: 750 },
      { key: 'integrationFailures', label: 'Integration Failures', format: 'number', accent: 'navy', warnAbove: 0 },
    ],
    actions: [
      { key: 'failedJobs', title: 'Resolve failed background jobs', detail: 'Queue failures that may block operational data.' },
      { key: 'integrationFailures', title: 'Repair integration failures', detail: 'External syncs needing intervention.' },
    ],
  },
});

export function getOperationalCatalog(moduleKey) {
  return MODULE_KPI_CATALOG[moduleKey] || null;
}
