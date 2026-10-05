"""Repository-owned adult resources; no ingestion, records, or model transport."""
from types import MappingProxyType

CATALOG_VERSION = "solomon-assistance-v1"
SOURCE_DOCUMENT = "docs/solomon/SOLOMON_APPROVED_ASSISTANCE.md"

ASSISTANCE = MappingProxyType({
    "knowledge": {
        "title": "Find reliable CROWN answers",
        "guidance": "Use published page help and maintained CROWN documentation. Confirm the documented version and source before applying instructions. If an answer is absent or conflicts with your configuration, ask authorized support; do not invent an answer.",
        "steps": ["Open Solomon on the relevant page.", "Review the published instructions and their scope.", "Verify permissions and configuration with the responsible adult.", "Escalate missing or conflicting guidance to support."],
        "draft": "Support request outline\nModule: [module name]\nExpected behavior: [general description]\nDocumentation reviewed: [approved reference]\nQuestion: [general operational question]\nKeep records, credentials, screenshots of personal data, and private logs out of this outline.",
    },
    "training": {
        "title": "Prepare adult staff training",
        "guidance": "Use a synthetic practice environment and a role-specific agenda. Confirm local permissions, provide accessible instructions, and have the implementation owner approve the session before delivery.",
        "steps": ["Select the adult staff audience and learning objectives.", "Demonstrate the relevant workflow using synthetic examples.", "Allow supervised practice and questions.", "Record completion through the school's approved training process."],
        "draft": "Staff training agenda\n1. Purpose and responsibilities\n2. Navigation and permissions\n3. Demonstration with synthetic examples\n4. Supervised practice\n5. Troubleshooting and support\n6. Human acceptance review before live use",
    },
    "communications": {
        "title": "Prepare a general announcement",
        "guidance": "Adapt this generic draft outside Solomon using your authorized communication workflow. Verify dates, audience, links, accessibility, and school approval before sending. Solomon does not select recipients or send messages.",
        "steps": ["Choose the announcement purpose.", "Replace every placeholder in the approved communication editor.", "Check facts, audience permissions, and accessible wording.", "Obtain human approval before sending."],
        "draft": "Subject: Reminder about [event]\n\nOur school will hold [event] on [date] at [time] in [location]. Please review [approved school link] for preparation and participation details. For general questions, contact [school office].\n\nThank you for partnering with our school.\n\nDraft only: verify all details and obtain approval before sending.",
    },
    "teaching": {
        "title": "Prepare a teacher-reviewed lesson outline",
        "guidance": "Use school-approved curriculum and materials you have permission to use. Teachers select content, biblical alignment, age suitability, and assessment criteria. Do not submit student work, grades, accommodations, or personal learning profiles.",
        "steps": ["Choose a curriculum objective from approved materials.", "Plan a brief introduction, model, guided practice, and independent practice.", "Create an assessment rubric aligned to the objective.", "Review accessibility, accuracy, and school expectations before teaching."],
        "draft": "Lesson planning outline\nObjective: [approved curriculum objective]\nMaterials: [rights-cleared resources]\nIntroduction: [connect to prior learning]\nTeacher model: [worked example]\nGuided practice: [general activity]\nIndependent practice: [general task]\nReflection: [discussion question]\nRubric: accuracy, reasoning, clarity, and appropriate use of sources\nTeacher review required before use.",
    },
    "leadership": {
        "title": "Prepare a leadership meeting agenda",
        "guidance": "Use this generic agenda to organize human discussion. Keep actual minutes, personnel matters, confidential deliberations, school finances, and individual cases outside Solomon. Leadership remains accountable for policy and decisions.",
        "steps": ["Confirm meeting purpose and accountable leader.", "Identify policies requiring human discussion and approval.", "Prepare authorized materials through the school's normal process.", "Assign owners and record decisions in the approved governance system."],
        "draft": "Leadership agenda\n1. Opening reflection and purpose\n2. Review previous approved action items\n3. Mission and operational priorities\n4. Policy review questions\n5. Staff training and implementation needs\n6. Decisions reserved for authorized leaders\n7. Owners, deadlines, and next meeting",
    },
    "outreach": {
        "title": "Prepare general Kingdom Path outreach",
        "guidance": "Use verified public sources and authorized school messaging. Check publication dates, geographic scope, and reuse rights. Do not infer family circumstances, rank prospects, or target identifiable people. School-specific tuition and enrollment strategy requires human advisory support.",
        "steps": ["Define a general public audience and outreach objective.", "Verify public source dates, definitions, and reuse rights.", "Have school leadership approve every factual claim.", "Publish only through the school's authorized channels."],
        "draft": "Public outreach outline\nWho we serve: [approved general description]\nOur mission: [approved mission statement]\nLearning opportunities: [verified program descriptions]\nInvitation: [approved public event or inquiry link]\nContact: [public school office contact]\nDo not insert invented enrollment, outcome, scholarship, or demographic claims.",
    },
    "care": {
        "title": "Plan Diadem, care, camp, and activity operations",
        "guidance": "Use a general planning checklist with authorized adult staff. Actual supervision, attendance, health, emergency, and pickup decisions must follow approved school procedures and qualified human direction. This checklist is not emergency or licensing advice.",
        "steps": ["Confirm program purpose, approved hours, and responsible adult leaders.", "Review applicable licensing and school procedures with qualified staff.", "Plan staff training, supplies, accessible activities, and communication.", "Use established systems for attendance, health, safeguarding, and authorized pickup."],
        "draft": "Program planning outline\nPurpose and approved schedule\nAccountable staff and training\nFacilities, supplies, and accessible activities\nApproved family communication process\nRequired human review of supervision and emergency procedures\nAcceptance checklist before opening",
    },
    "accessibility": {
        "title": "Prepare clear, accessible general instructions",
        "guidance": "Use short sentences, descriptive links, clear headings, and one action per step. Have an appropriate reviewer check translations and safety or policy wording. This resource does not certify accessibility compliance or provide automatic translation.",
        "steps": ["State the purpose in familiar language.", "Use one action per numbered step and descriptive link text.", "Check keyboard access, text alternatives, contrast, and mobile readability.", "Have a qualified reviewer confirm meaning before publishing translated content."],
        "draft": "Plain-language help template\nPurpose: [what this task accomplishes]\nBefore you start: [approved prerequisites]\n1. Open [page name].\n2. Select [control name].\n3. Review [items to verify].\n4. Ask [authorized support] if anything is unclear.\nExpected result: [verified result]\n\nGeneral Spanish help example for human review:\nRevise la información antes de continuar. Si necesita ayuda, comuníquese con la oficina de la escuela.",
    },
    "quality": {
        "title": "Prepare synthetic software quality checks",
        "guidance": "Use synthetic fixtures and maintained specifications. Verify tenant isolation, permissions, failure handling, accessibility, and human review. Do not upload production databases, credentials, private logs, or identifiable screenshots to an external assistant.",
        "steps": ["Define expected behavior and a synthetic fixture.", "Test authorized and unauthorized roles and school boundaries.", "Test unavailable services, malformed input, and cancellation.", "Verify accessible layout, source labels, and review requirements."],
        "draft": "Synthetic test case outline\nFeature and expected behavior\nSynthetic role and school fixtures\nAuthorized success scenario\nUnauthorized and cross-school rejection scenarios\nInvalid-input and unavailable-service scenarios\nKeyboard, mobile, and reduced-motion checks\nEvidence and remaining limitations",
    },
})
