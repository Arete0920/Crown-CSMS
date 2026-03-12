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
    <Box
      sx={{
        mb: 0.75,
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 1.25,
        backgroundColor: "rgba(255,255,255,0.03)",
      }}
    >
      <ListItemButton
        onClick={() => setOpen((v) => !v)}
        sx={{ py: 0.7, px: 1.1, borderRadius: 1 }}
      >
        <ListItemText
          primary={
            <Typography
              variant="caption"
              sx={{
                fontWeight: 800,
                fontSize: 10,
                letterSpacing: 1.15,
                textTransform: "uppercase",
                color: "rgba(255,255,255,0.72)",
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
        <Box sx={{ px: 0.8, pb: 0.7 }}>
          {children}
        </Box>
      </Collapse>
    </Box>
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
        py: 0.65,
        px: 1,
        mb: 0.35,
        fontSize: 13,
        fontWeight: active ? 700 : 500,
        color: active ? "#ffffff" : "rgba(255,255,255,0.8)",
        backgroundColor: active ? "rgba(176,141,87,0.38)" : "transparent",
        border: active ? "1px solid rgba(255,255,255,0.28)" : "1px solid transparent",
        '&:hover': {
          backgroundColor: active ? "rgba(176,141,87,0.45)" : "rgba(255,255,255,0.08)",
        },
      }}
    >
      <ListItemText
        primary={label}
        primaryTypographyProps={{
          fontSize: 13,
          fontWeight: active ? 700 : 500,
          lineHeight: 1.2,
        }}
      />
    </ListItemButton>
  );
}

/**
 * CrownSidebar - collapsible grouped navigation.
 *
 * Standalone MUI component; can be embedded alongside the existing CrownLayout
 * sidebar or used independently in a new layout composition.
 */
export default function CrownSidebar() {
  return (
    <List dense disablePadding sx={{ pt: 0.2 }}>
      <Section title="Academics">
        <NavItem label="Gradebook" href="/gradebook" />
        <NavItem label="Courses" href="/courses" />
        <NavItem label="Attendance" href="/attendance" />
      </Section>

      <Section title="Finance">
        <NavItem label="Billing" href="/billing" />
        <NavItem label="Financial Aid" href="/aid" />
        <NavItem label="Invoices" href="/invoices" />
      </Section>

      <Section title="Board">
        <NavItem label="Metrics" href="/board/metrics" />
        <NavItem label="Integrity" href="/integrity" />
      </Section>

      <Section title="Operations">
        <NavItem label="Admissions" href="/admissions" />
        <NavItem label="Registrar" href="/registrar" />
        <NavItem label="Scheduling" href="/scheduling" />
      </Section>
    </List>
  );
}
