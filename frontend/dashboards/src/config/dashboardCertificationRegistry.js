function createCertification(status, owner, notes = '') {
  return {
    status,
    owner,
    notes,
  };
}

export const DASHBOARD_CERTIFICATION_STATUS = {
  SCAFFOLD: 'scaffold',
  HYBRID: 'hybrid',
  LIVE: 'live',
  CERTIFIED: 'certified',
};

export const DASHBOARD_CERTIFICATION_REGISTRY = {
  // Tier 1
  attendance: createCertification('hybrid', 'Attendance Operations', 'Live-bound reference page.'),
  billing: createCertification('scaffold', 'Finance Team'),
  'financial-aid': createCertification('scaffold', 'Finance Team'),
  registrar: createCertification('scaffold', 'Registrar Team'),

  // Tier 2
  scheduling: createCertification('scaffold', 'Registrar Team'),
  gradebook: createCertification('scaffold', 'Academic Team'),
  'student-care': createCertification('scaffold', 'Student Care Team'),
  'activities-athletics': createCertification('scaffold', 'Student Life Team'),
  communications: createCertification('scaffold', 'School Operations'),

  // Tier 3
  'school-administrator': createCertification('scaffold', 'School Leadership'),
  'school-board': createCertification('scaffold', 'Board Governance'),
  'master-control': createCertification('scaffold', 'Platform Leadership'),
  admissions: createCertification('scaffold', 'Admissions Team'),
  advancement: createCertification('scaffold', 'Advancement Team'),

  // Tier 4
  hr: createCertification('scaffold', 'HR Team'),
  facilities: createCertification('scaffold', 'Facilities Team'),
  'health-office': createCertification('scaffold', 'Health Office'),
  transportation: createCertification('scaffold', 'Transportation Team'),
  'food-service': createCertification('scaffold', 'Food Service Team'),
  'it-support': createCertification('scaffold', 'IT Team'),

  // Tier 5
  'fine-arts': createCertification('scaffold', 'Fine Arts Team'),
  'athletics-director': createCertification('scaffold', 'Athletics Team'),
  'library-media': createCertification('scaffold', 'Library Media Team'),
  'extended-care': createCertification('scaffold', 'Extended Care Team'),
  'safety-security': createCertification('scaffold', 'Safety Team'),
  'curriculum-pd': createCertification('scaffold', 'Curriculum PD Team'),

  // Tier 6
  'chaplain-spiritual-life': createCertification('scaffold', 'Chaplaincy Team'),
  'advancement-operations': createCertification('scaffold', 'Advancement Operations'),
  'volunteer-management': createCertification('scaffold', 'Volunteer Coordinator'),
  'portrait-service': createCertification('scaffold', 'Portrait Service Team'),
  'alumni-relations': createCertification('scaffold', 'Alumni Relations'),
  'network-benchmarking': createCertification('scaffold', 'Platform Leadership'),

  // Tier 7
  'implementation-success': createCertification('scaffold', 'Implementation Team'),
  'data-migration': createCertification('scaffold', 'Data Operations Team'),
  'integrations-automation': createCertification('scaffold', 'Integrations Team'),
  'compliance-audit': createCertification('scaffold', 'Compliance Team'),
  'revenue-operations': createCertification('scaffold', 'Revenue Operations'),
  'release-reliability': createCertification('hybrid', 'Platform Engineering', 'Live-bound reference page.'),

  // Phase 9 control page
  'dashboard-certification-center': createCertification('live', 'Platform Engineering', 'Derived from internal registries.'),
};

export function getCertificationStatusColor(status) {
  switch (status) {
    case 'certified':
      return 'success';
    case 'live':
      return 'success';
    case 'hybrid':
      return 'warning';
    case 'scaffold':
    default:
      return 'default';
  }
}
