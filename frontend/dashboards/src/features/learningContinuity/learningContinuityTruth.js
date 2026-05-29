export const CROWN_AUTHORITY_RULES = [
  {
    rule: "CROWN owns process truth",
    detail:
      "Remote learning activation, teacher readiness, parent visibility, student actions, curriculum maps, interventions, dual enrollment, and transcript impact originate in CROWN.",
  },
  {
    rule: "CROWN owns SIS truth",
    detail:
      "Students, households, guardians, staff, courses, sections, rosters, attendance, grades, transcript records, and intervention records remain authoritative in CROWN.",
  },
  {
    rule: "Microsoft executes and collaborates",
    detail:
      "Teams, Microsoft 365, Microsoft Education, Assignments, Classwork, SDS, Insights, Reflect, OneDrive, and SharePoint support execution and collaboration but do not replace CROWN record truth.",
  },
  {
    rule: "External systems report sync state",
    detail:
      "Microsoft and provider systems return sync status, errors, timestamps, launch status, assignment status, and engagement signals for CROWN review.",
  },
  {
    rule: "CROWN resolves conflicts",
    detail:
      "If CROWN and an external system disagree, CROWN shows an exception and requires authorized review instead of silently accepting external state.",
  },
];

export const SOURCE_SYSTEMS = {
  crown: "CROWN",
  teams: "Microsoft Teams",
  m365: "Microsoft 365",
  sds: "Microsoft School Data Sync",
  graph: "Microsoft Graph",
  provider: "External Provider",
  manual: "Manual Review",
};

export const RECORD_STATES = {
  configured: "Configured",
  planned: "Planned",
  ready: "Ready",
  watch: "Watch",
  risk: "Risk",
  blocked: "Blocked",
  live: "Live",
  complete: "Complete",
};

export const SYNC_STATES = {
  notConnected: "Not connected",
  pending: "Pending",
  synced: "Synced",
  warning: "Warning",
  failed: "Failed",
  manual: "Manual review",
};

export const learningContinuityPages = {
  onlineCommand: {
    pageKey: "onlineCommand",
    eyebrow: "CROWN source of truth",
    title: "Online Learning Command Center",
    subtitle:
      "CROWN-owned activation, monitoring, communication, attendance, assignment, and evidence control for remote or closure learning.",
    crownOwner: "School Administrator / Principal",
    authorityStatement:
      "Remote-learning days are created, governed, closed, and archived in CROWN. Teams and Microsoft services execute class collaboration and return status back to CROWN.",
    primarySource: SOURCE_SYSTEMS.crown,
    externalSystems: [SOURCE_SYSTEMS.teams, SOURCE_SYSTEMS.m365, SOURCE_SYSTEMS.graph],
    metrics: [
      {
        label: "Remote day state",
        value: "Configured",
        helper: "CROWN workflow shell is ready for activation state wiring.",
        tone: "royal",
      },
      {
        label: "Class readiness",
        value: "91%",
        helper: "CROWN readiness score from lesson, Teams, attendance, assignment, and roster checks.",
        tone: "emerald",
      },
      {
        label: "Family notice gap",
        value: "31",
        helper: "Families that have not opened required notice.",
        tone: "amber",
      },
      {
        label: "Evidence state",
        value: "Draft",
        helper: "Closure-day audit packet is defined but not yet backed by live export.",
        tone: "violet",
      },
    ],
    records: [
      {
        crownRecordId: "RLD-2026-0001",
        recordType: "RemoteLearningDay",
        state: RECORD_STATES.configured,
        crownTruth: "Remote day activation, scope, reason, dates, affected classes, and closeout belong to CROWN.",
        microsoftRole: "Receives class meeting/channel activation and returns launch/completion status.",
        syncState: SYNC_STATES.pending,
        nextAction: "Wire backend RemoteLearningDay model and activation endpoint.",
      },
      {
        crownRecordId: "CLR-2026-0001",
        recordType: "ClassLearningReadiness",
        state: RECORD_STATES.watch,
        crownTruth: "CROWN calculates readiness from roster, lesson, assignment, attendance method, and Teams verification.",
        microsoftRole: "Returns class team, channel, meeting, and assignment availability.",
        syncState: SYNC_STATES.warning,
        nextAction: "Create readiness API that aggregates CROWN + Microsoft status.",
      },
      {
        crownRecordId: "RLE-2026-0001",
        recordType: "RemoteLearningEvidencePacket",
        state: RECORD_STATES.planned,
        crownTruth: "CROWN owns evidence archive for attendance, notices, class sessions, assignments, and decisions.",
        microsoftRole: "Supplies meeting/assignment/file metadata where available.",
        syncState: SYNC_STATES.manual,
        nextAction: "Define export format and evidence retention policy.",
      },
    ],
    workflow: [
      "Create remote-learning day in CROWN.",
      "Select closure reason, affected dates, grades, classes, and operating rules.",
      "Generate CROWN announcements and required acknowledgements.",
      "Verify Teams/class/channel/assignment readiness.",
      "Monitor live class launch, attendance, and family access.",
      "Close day and export evidence packet.",
    ],
  },

  teacherCockpit: {
    pageKey: "teacherCockpit",
    eyebrow: "CROWN teacher truth",
    title: "Teacher Daily Cockpit",
    subtitle:
      "CROWN-owned teacher operating page for the class day: schedule, roster, lesson plan, attendance, assignment, messages, and student support.",
    crownOwner: "Teacher / Academic Leadership",
    authorityStatement:
      "The teacher's class obligations, lesson expectations, attendance state, grading queue, and student-support responsibilities originate in CROWN.",
    primarySource: SOURCE_SYSTEMS.crown,
    externalSystems: [SOURCE_SYSTEMS.teams, SOURCE_SYSTEMS.m365, SOURCE_SYSTEMS.graph],
    metrics: [
      {
        label: "Next class",
        value: "10:05",
        helper: "CROWN schedule and section roster determine the next teaching obligation.",
        tone: "royal",
      },
      {
        label: "Attendance open",
        value: "1",
        helper: "Attendance state belongs to CROWN SIS/attendance workflow.",
        tone: "amber",
      },
      {
        label: "Ungraded work",
        value: "23",
        helper: "CROWN gradebook owns grading obligations and final grade truth.",
        tone: "rose",
      },
      {
        label: "Lesson state",
        value: "Ready",
        helper: "Publisher baseline + teacher edits available for today.",
        tone: "emerald",
      },
    ],
    records: [
      {
        crownRecordId: "CLS-ENG8B-2026-05-27",
        recordType: "ClassSession",
        state: RECORD_STATES.ready,
        crownTruth: "CROWN owns section, roster, class time, attendance requirement, and completion state.",
        microsoftRole: "Hosts Teams class meeting or class channel if remote/hybrid.",
        syncState: SYNC_STATES.pending,
        nextAction: "Connect ClassSession state to schedule, attendance, and Teams launch status.",
      },
      {
        crownRecordId: "LP-ENG8B-U04-L12",
        recordType: "LessonPlan",
        state: RECORD_STATES.ready,
        crownTruth: "CROWN owns lesson objective, curriculum map position, teacher edits, and actual-taught state.",
        microsoftRole: "May receive files, links, resources, or assignment shells.",
        syncState: SYNC_STATES.manual,
        nextAction: "Build lesson-plan API and version history.",
      },
      {
        crownRecordId: "ASSIGN-ENG8B-ESSAY-REV1",
        recordType: "AssignmentObligation",
        state: RECORD_STATES.watch,
        crownTruth: "CROWN owns assignment expectation, gradebook impact, missing-work state, and parent visibility.",
        microsoftRole: "May execute assignment distribution/submission through Teams Assignments.",
        syncState: SYNC_STATES.warning,
        nextAction: "Map CROWN assignment obligations to Teams assignment references.",
      },
    ],
    workflow: [
      "Open next class from CROWN schedule.",
      "Review roster and support flags.",
      "Open CROWN lesson plan and Teams resources.",
      "Take attendance in CROWN.",
      "Post or confirm assignment obligation.",
      "Update actual-taught status and grading queue.",
    ],
  },

  parentStatus: {
    pageKey: "parentStatus",
    eyebrow: "CROWN family truth",
    title: "Parent Learning Status",
    subtitle:
      "CROWN-owned family view of child schedule, attendance, missing work, messages, grades, school actions, and mission-life updates.",
    crownOwner: "Parent / Guardian, constrained by CROWN family-scope permissions",
    authorityStatement:
      "CROWN determines what each parent can see based on household/guardian relationships, student enrollment, role permissions, and school policy.",
    primarySource: SOURCE_SYSTEMS.crown,
    externalSystems: [SOURCE_SYSTEMS.teams, SOURCE_SYSTEMS.m365, SOURCE_SYSTEMS.sds],
    metrics: [
      {
        label: "Family tasks",
        value: "4",
        helper: "CROWN family action queue.",
        tone: "amber",
      },
      {
        label: "Child learning status",
        value: "Watch",
        helper: "One child has missing work or access risk.",
        tone: "rose",
      },
      {
        label: "Unread school messages",
        value: "3",
        helper: "CROWN communications remain family-scoped.",
        tone: "violet",
      },
      {
        label: "Class links ready",
        value: "6",
        helper: "Teams/Microsoft links surfaced through CROWN.",
        tone: "emerald",
      },
    ],
    records: [
      {
        crownRecordId: "FAM-0042-STUDENT-LEARNING-DAY",
        recordType: "ParentLearningDigest",
        state: RECORD_STATES.watch,
        crownTruth: "CROWN owns family-scoped digest, school actions, child status, and communication visibility.",
        microsoftRole: "May supply Teams assignment or guardian digest metadata where available.",
        syncState: SYNC_STATES.pending,
        nextAction: "Create parent digest endpoint from CROWN SIS + communications + gradebook + attendance.",
      },
      {
        crownRecordId: "ACK-REMOTE-NOTICE-2026-0001",
        recordType: "FamilyAcknowledgement",
        state: RECORD_STATES.watch,
        crownTruth: "CROWN owns required notice acknowledgement status.",
        microsoftRole: "May deliver or link notices through Teams/Outlook, but acknowledgement belongs to CROWN.",
        syncState: SYNC_STATES.manual,
        nextAction: "Add required acknowledgement model and route.",
      },
    ],
    workflow: [
      "Identify current parent/guardian household in CROWN.",
      "Load only that family's students.",
      "Show today's schedule, attendance, missing work, messages, and actions.",
      "Surface Teams links without exposing unrelated class data.",
      "Record required acknowledgements in CROWN.",
    ],
  },

  studentToday: {
    pageKey: "studentToday",
    eyebrow: "CROWN student truth",
    title: "Student Today",
    subtitle:
      "CROWN-owned student action sequence: join class, complete work, review feedback, ask for help, and participate in mission life.",
    crownOwner: "Student, constrained by CROWN student-scope permissions",
    authorityStatement:
      "CROWN ranks the student's next actions based on schedule, assignment obligations, missing work, grades, attendance, support needs, and school priorities.",
    primarySource: SOURCE_SYSTEMS.crown,
    externalSystems: [SOURCE_SYSTEMS.teams, SOURCE_SYSTEMS.m365, SOURCE_SYSTEMS.graph],
    metrics: [
      {
        label: "Next action",
        value: "Join class",
        helper: "CROWN ranks next action from schedule and assignment state.",
        tone: "royal",
      },
      {
        label: "Assignments due",
        value: "6",
        helper: "CROWN assignment obligations, optionally synced to Teams.",
        tone: "amber",
      },
      {
        label: "Missing work",
        value: "2",
        helper: "CROWN determines gradebook and parent-visible missing work.",
        tone: "rose",
      },
      {
        label: "Service hours",
        value: "14",
        helper: "CROWN mission/service record.",
        tone: "emerald",
      },
    ],
    records: [
      {
        crownRecordId: "STU-0087-TODAY",
        recordType: "StudentLearningActionQueue",
        state: RECORD_STATES.ready,
        crownTruth: "CROWN owns action ordering and student-visible obligations.",
        microsoftRole: "Executes class meeting, assignment handoff, and document collaboration.",
        syncState: SYNC_STATES.pending,
        nextAction: "Create CROWN Today Engine for student action ranking.",
      },
      {
        crownRecordId: "HELP-REQUEST-STU-0087",
        recordType: "StudentHelpRequest",
        state: RECORD_STATES.planned,
        crownTruth: "CROWN owns help requests and routing to academic, technology, counselor, or chaplain staff.",
        microsoftRole: "May notify staff through Teams/Outlook.",
        syncState: SYNC_STATES.manual,
        nextAction: "Add help request workflow and role routing.",
      },
    ],
    workflow: [
      "Load student schedule from CROWN.",
      "Rank next class and assignments.",
      "Surface Teams/class resources.",
      "Show missing work and feedback.",
      "Allow academic, tech, care, and prayer support requests.",
    ],
  },

  curriculumImport: {
    pageKey: "curriculumImport",
    eyebrow: "CROWN curriculum truth",
    title: "Curriculum Import and Lesson Plan Authority",
    subtitle:
      "CROWN-owned publisher baseline, school-approved map, teacher-editable plan, and actual-taught record.",
    crownOwner: "Academic Leadership / Curriculum Director / Teacher",
    authorityStatement:
      "CROWN owns curriculum map, lesson-plan versions, pacing variance, and actual-taught records. Publisher files are imported source material, not operational truth.",
    primarySource: SOURCE_SYSTEMS.crown,
    externalSystems: [SOURCE_SYSTEMS.m365, SOURCE_SYSTEMS.teams],
    metrics: [
      {
        label: "Publisher lanes",
        value: "3",
        helper: "BJU Press, Abeka, Purposeful Design.",
        tone: "royal",
      },
      {
        label: "Baseline map",
        value: "Planned",
        helper: "Import/parsing workflow not yet wired.",
        tone: "amber",
      },
      {
        label: "Teacher edits",
        value: "Required",
        helper: "Teacher customization must preserve baseline and version history.",
        tone: "emerald",
      },
      {
        label: "Actual taught",
        value: "Required",
        helper: "CROWN must capture skipped, moved, repeated, and taught lessons.",
        tone: "violet",
      },
    ],
    records: [
      {
        crownRecordId: "CURR-BJU-ENG8-2026",
        recordType: "CurriculumMap",
        state: RECORD_STATES.planned,
        crownTruth: "CROWN owns approved course map after import and review.",
        microsoftRole: "Stores supporting files or pushes assignment resources when needed.",
        syncState: SYNC_STATES.manual,
        nextAction: "Create curriculum import parser and approval workflow.",
      },
      {
        crownRecordId: "LESSON-ENG8-U04-L12",
        recordType: "LessonPlanVersion",
        state: RECORD_STATES.planned,
        crownTruth: "CROWN owns publisher baseline, school approved, teacher edited, and actual taught states.",
        microsoftRole: "May receive files or assignment shell generated from lesson plan.",
        syncState: SYNC_STATES.pending,
        nextAction: "Create lesson-plan versioning and Teams assignment handoff.",
      },
    ],
    workflow: [
      "Upload publisher or custom curriculum file.",
      "Map course, grade, unit, lesson, objective, and school year.",
      "Approve CROWN baseline map.",
      "Generate teacher-editable lesson plans.",
      "Track actual taught and pacing variance.",
    ],
  },

  microsoftHealth: {
    pageKey: "microsoftHealth",
    eyebrow: "CROWN integration control",
    title: "Microsoft Education Health",
    subtitle:
      "CROWN-owned integration health page for Teams, Microsoft 365, SDS, Assignments, Classwork, Insights, Reflect, and sync exceptions.",
    crownOwner: "IT / School Administrator / Academic Leadership",
    authorityStatement:
      "CROWN determines expected Microsoft state from CROWN records, then compares Microsoft responses for sync health and exception handling.",
    primarySource: SOURCE_SYSTEMS.crown,
    externalSystems: [
      SOURCE_SYSTEMS.teams,
      SOURCE_SYSTEMS.m365,
      SOURCE_SYSTEMS.sds,
      SOURCE_SYSTEMS.graph,
    ],
    metrics: [
      {
        label: "Expected class teams",
        value: "From CROWN",
        helper: "CROWN sections and rosters define expected Microsoft class teams.",
        tone: "royal",
      },
      {
        label: "Roster sync",
        value: "Watch",
        helper: "SDS/Graph sync verification not yet connected.",
        tone: "amber",
      },
      {
        label: "Guardian sync",
        value: "Planned",
        helper: "Parent/guardian relationships originate in CROWN.",
        tone: "rose",
      },
      {
        label: "Exception queue",
        value: "Required",
        helper: "Mismatch handling must be visible and auditable.",
        tone: "violet",
      },
    ],
    records: [
      {
        crownRecordId: "MS-HEALTH-2026-0001",
        recordType: "MicrosoftEducationHealthSnapshot",
        state: RECORD_STATES.planned,
        crownTruth: "CROWN owns expected class, roster, owner, guardian, and assignment state.",
        microsoftRole: "Returns actual tenant, team, channel, roster, assignment, and insight availability.",
        syncState: SYNC_STATES.notConnected,
        nextAction: "Create Microsoft health service and Graph/SDS status adapters.",
      },
      {
        crownRecordId: "SYNC-EXCEPTION-CLASS-0001",
        recordType: "IntegrationSyncException",
        state: RECORD_STATES.planned,
        crownTruth: "CROWN owns exception visibility, resolution, and audit trail.",
        microsoftRole: "Supplies mismatched or failed sync response.",
        syncState: SYNC_STATES.failed,
        nextAction: "Create exception queue and resolution workflow.",
      },
    ],
    workflow: [
      "Read expected classes, rosters, guardians, and assignments from CROWN.",
      "Query Microsoft tenant/class/team/assignment/SDS state.",
      "Compare expected vs actual.",
      "Create CROWN exception records.",
      "Route resolution to IT/admin/academic owners.",
    ],
  },

  dualEnrollment: {
    pageKey: "dualEnrollment",
    eyebrow: "CROWN transcript truth",
    title: "Dual Enrollment and External Course Tracker",
    subtitle:
      "CROWN-owned external course, progress, credit, grade, transcript, and approval workflow.",
    crownOwner: "Registrar / Academic Leadership",
    authorityStatement:
      "External providers may deliver instruction or grades, but CROWN owns transcript mapping, credit posting, parent/student visibility, and approval state.",
    primarySource: SOURCE_SYSTEMS.crown,
    externalSystems: [SOURCE_SYSTEMS.provider, SOURCE_SYSTEMS.manual],
    metrics: [
      {
        label: "External courses",
        value: "8",
        helper: "CROWN external course enrollment records.",
        tone: "royal",
      },
      {
        label: "Transcript pending",
        value: "3",
        helper: "Registrar review required before credit is official.",
        tone: "rose",
      },
      {
        label: "Progress current",
        value: "84%",
        helper: "Provider progress updates received or manually entered.",
        tone: "emerald",
      },
      {
        label: "Provider exceptions",
        value: "2",
        helper: "Login, grade, transcript, or documentation issue.",
        tone: "amber",
      },
    ],
    records: [
      {
        crownRecordId: "EXT-COURSE-ALG-2026",
        recordType: "ExternalCourseEnrollment",
        state: RECORD_STATES.watch,
        crownTruth: "CROWN owns course enrollment, credit value, transcript mapping, and approval state.",
        microsoftRole: "No authoritative role unless Microsoft-hosted resources are used.",
        syncState: SYNC_STATES.manual,
        nextAction: "Create external course model, registrar approval, and transcript impact preview.",
      },
      {
        crownRecordId: "TRANSCRIPT-IMPACT-0087",
        recordType: "TranscriptImpactPreview",
        state: RECORD_STATES.planned,
        crownTruth: "CROWN determines if and how external credit applies to transcript.",
        microsoftRole: "None unless documents are stored in SharePoint/OneDrive.",
        syncState: SYNC_STATES.manual,
        nextAction: "Build transcript impact preview and final posting workflow.",
      },
    ],
    workflow: [
      "Create external course enrollment in CROWN.",
      "Record provider, term, credits, grading scale, and contact.",
      "Track access, progress, grades, and documentation.",
      "Review transcript impact.",
      "Approve final credit posting in CROWN.",
    ],
  },

  interventions: {
    pageKey: "interventions",
    eyebrow: "CROWN intervention truth",
    title: "Remedial / Recovery / Intervention Workflow",
    subtitle:
      "CROWN-owned intervention assignment, mastery target, progress, parent visibility, and exit decision.",
    crownOwner: "Academic Leadership / Teacher / Student Support",
    authorityStatement:
      "CROWN owns intervention reason, plan, assignment, mastery goal, progress review, family visibility, and closeout.",
    primarySource: SOURCE_SYSTEMS.crown,
    externalSystems: [SOURCE_SYSTEMS.teams, SOURCE_SYSTEMS.provider, SOURCE_SYSTEMS.manual],
    metrics: [
      {
        label: "Active plans",
        value: "12",
        helper: "CROWN intervention assignments.",
        tone: "amber",
      },
      {
        label: "Mastery met",
        value: "67%",
        helper: "Current plans meeting target.",
        tone: "emerald",
      },
      {
        label: "Family updates due",
        value: "5",
        helper: "Parent visibility and communication follow-up.",
        tone: "rose",
      },
      {
        label: "Review due",
        value: "4",
        helper: "Teacher or principal review required.",
        tone: "royal",
      },
    ],
    records: [
      {
        crownRecordId: "INT-READING-0087",
        recordType: "InterventionCourseAssignment",
        state: RECORD_STATES.watch,
        crownTruth: "CROWN owns diagnostic reason, target skill, assignment, mastery goal, and review cadence.",
        microsoftRole: "May host resources, Teams class channel, or assignments.",
        syncState: SYNC_STATES.manual,
        nextAction: "Create intervention plan model and progress review workflow.",
      },
      {
        crownRecordId: "INT-PARENT-VIS-0087",
        recordType: "InterventionParentVisibility",
        state: RECORD_STATES.planned,
        crownTruth: "CROWN determines parent-visible intervention status and communication cadence.",
        microsoftRole: "May notify through Teams/Outlook but does not own visibility rules.",
        syncState: SYNC_STATES.pending,
        nextAction: "Add parent-visible intervention summary and alert rules.",
      },
    ],
    workflow: [
      "Create diagnostic reason and target skill in CROWN.",
      "Assign remedial/recovery/support course.",
      "Set mastery target and review cadence.",
      "Track progress and teacher notes.",
      "Notify parent when policy requires.",
      "Close or extend intervention based on CROWN review.",
    ],
  },
};

export function getLearningContinuityTruth(pageKey) {
  return learningContinuityPages[pageKey] ?? learningContinuityPages.onlineCommand;
}
