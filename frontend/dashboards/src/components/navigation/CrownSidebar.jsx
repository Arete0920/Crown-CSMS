import { useState } from "react";
import { List, ListItemButton, ListItemText, Collapse, Typography, Box } from "@mui/material";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";

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
  return (
    <List dense disablePadding>
      <Section title="Academics">
        <NavItem label="Gradebook"  href="/gradebook" />
        <NavItem label="Courses"    href="/courses" />
        <NavItem label="Attendance" href="/attendance" />
      </Section>

      <Section title="Finance">
        <NavItem label="Billing"       href="/billing" />
        <NavItem label="Financial Aid" href="/aid" />
        <NavItem label="Invoices"      href="/invoices" />
      </Section>

      <Section title="Board">
        <NavItem label="Metrics"     href="/board/metrics" />
        <NavItem label="Integrity"   href="/integrity" />
      </Section>

      <Section title="Operations">
        <NavItem label="Admissions"  href="/admissions" />
        <NavItem label="Registrar"   href="/registrar" />
        <NavItem label="Scheduling"  href="/scheduling" />
      </Section>
    </List>
  );
}
