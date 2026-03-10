import { useState } from "react";
import { List, ListItemButton, ListItemText, Collapse, Typography, Box } from "@mui/material";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import { getDashboardNavSections } from './dashboardNavConfig';

/**
 * Collapsible sidebar section with a labelled group header.
 */
function Section({ title, children }) {
  const [open, setOpen] = useState(true);

  return (
    <>
      <ListItemButton
        onClick={() => setOpen((v) => !v)}
        sx={{ py: 0.5, px: 1, borderRadius: 1 }}
      >
        <ListItemText
          primary={
            <Typography
              variant="caption"
              sx={{
                fontWeight: 700,
                fontSize: 10,
                letterSpacing: 1.1,
                textTransform: "uppercase",
                color: "text.disabled",
              }}
            >
              {title}
            </Typography>
          }
        />
        {open ? (
          <ExpandLess sx={{ fontSize: 14, color: "text.disabled" }} />
        ) : (
          <ExpandMore sx={{ fontSize: 14, color: "text.disabled" }} />
        )}
      </ListItemButton>

      <Collapse in={open} timeout="auto" unmountOnExit>
        <Box sx={{ pl: 1 }}>
          {children}
        </Box>
      </Collapse>
    </>
  );
}

function NavItem({ label, href }) {
  const active = typeof window !== "undefined" && window.location.pathname === href;
  return (
    <ListItemButton
      component="a"
      href={href}
      selected={active}
      sx={{
        borderRadius: 1,
        py: 0.5,
        px: 1,
        fontSize: 13,
        fontWeight: active ? 600 : 400,
      }}
    >
      <ListItemText
        primary={label}
        primaryTypographyProps={{ fontSize: 13, fontWeight: active ? 600 : 400 }}
      />
    </ListItemButton>
  );
}

/**
 * CrownSidebar — collapsible grouped navigation.
 *
 * Standalone MUI component; can be embedded alongside the existing CrownLayout
 * sidebar or used independently in a new layout composition.
 */
export default function CrownSidebar() {
  const dashboardNavSections = getDashboardNavSections();

  return (
    <List dense disablePadding>
      <Section title="Academics">
        <NavItem label="Gradebook Workspace"  href="/gradebook" />
        <NavItem label="Classrooms" href="/classrooms" />
        <NavItem label="Attendance Workspace" href="/teacher/attendance" />
      </Section>

      <Section title="Board">
        <NavItem label="Board Dashboard" href="/board" />
        <NavItem label="Integrity" href="/integrity" />
      </Section>

      <Section title="Teacher">
        <NavItem label="Teacher Dashboard" href="/teacher" />
        <NavItem label="Gradebook" href="/gradebook" />
        <NavItem label="Attendance" href="/teacher/attendance" />
      </Section>

      <Section title="Family">
        <NavItem label="Family Dashboard" href="/parent" />
        <NavItem label="Grades" href="/academics/parent-snapshot" />
        <NavItem label="Tuition" href="/finance/invoices" />
      </Section>

      <Section title="Student">
        <NavItem label="Student Dashboard" href="/student" />
        <NavItem label="Assignments" href="/academics/student-work" />
        <NavItem label="Grades" href="/gradebook" />
      </Section>

      <Section title="Student Life">
        <NavItem label="Student Life Dashboard" href="/spiritual-life" />
        <NavItem label="Chapel" href="/spiritual-life" />
        <NavItem label="Service Hours" href="/service-hours" />
        <NavItem label="Care Notes" href="/spiritual-life" />
      </Section>

      <Section title="Master Control">
        <NavItem label="Master Control Dashboard" href="/master-control" />
        <NavItem label="Schools" href="/master-control" />
        <NavItem label="Support" href="/communications" />
        <NavItem label="Executive Reports" href="/master-control" />
      </Section>

      <Section title="Operations">
        <NavItem label="Inquiries" href="/admissions/pipeline" />
        <NavItem label="Applicants" href="/admissions/pipeline" />
        <NavItem label="Decisions" href="/admissions/pipeline" />
        <NavItem label="Scheduling Workspace"  href="/classrooms" />
      </Section>

      {dashboardNavSections.map((section) => (
        <Section key={section.label} title={section.label}>
          {section.children.map((item) => (
            <NavItem key={item.key} label={item.label} href={item.href} />
          ))}
        </Section>
      ))}
    </List>
  );
}
