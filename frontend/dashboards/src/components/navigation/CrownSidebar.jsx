import { useState } from "react";
import { List, ListItemButton, ListItemText, Collapse, Typography, Box } from "@mui/material";
import { getDashboardNavSections } from './dashboardNavConfig';
import { getCurrentUserRoles } from '../../auth/roleAdapter';
import { filterVisibleNav } from '../../auth/roleAccess';
import { usePermissions } from '../../hooks/usePermissions';

/**
 * Collapsible sidebar section with a labelled group header.
 */
function Section({ title, children }) {
  const [open, setOpen] = useState(true);

  return (
    <Box
      sx={{
        mb: 0.75,
        border: "1px solid var(--crown-compat-color-b749cc2591)",
        borderRadius: 1.25,
        backgroundColor: "var(--crown-compat-color-8820ca3754)",
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
                color: "var(--crown-compat-color-b287e65b63)",
              }}
            >
              {title}
            </Typography>
          }
        />
        <Typography
          component="span"
          aria-hidden="true"
          sx={{ fontSize: 14, color: "text.disabled", lineHeight: 1 }}
        >
          {open ? "▴" : "▾"}
        </Typography>
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
        color: active ? "var(--crown-compat-color-f2074b6cef)" : "var(--crown-compat-color-1248f9ab2f)",
        backgroundColor: active ? "var(--crown-compat-color-a1adec2ba3)" : "transparent",
        border: active ? "1px solid var(--crown-compat-color-f6a93a8e2e)" : "1px solid transparent",
        '&:hover': {
          backgroundColor: active ? "var(--crown-compat-color-a744b12de6)" : "var(--crown-compat-color-c34f5a2a4d)",
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

const normalizeRole = (role) => String(role || 'guest').trim().toLowerCase();

const canSeeItem = (itemRoles, currentRole) => {
  if (!Array.isArray(itemRoles) || itemRoles.length === 0) return true;
  return itemRoles.map(normalizeRole).includes(normalizeRole(currentRole));
};

/**
 * CrownSidebar — collapsible grouped navigation.
 *
 * Standalone MUI component; can be embedded alongside the existing CrownLayout
 * sidebar or used independently in a new layout composition.
 */
export default function CrownSidebar() {
  const { permissions } = usePermissions();
  const dashboardNavSections = getDashboardNavSections();
  const userRoles = getCurrentUserRoles();
  const currentUserRole = userRoles[0] || 'guest';
  const visibleNavItems = filterVisibleNav(dashboardNavSections, { roles: userRoles, permissions })
    .map((section) => ({
      ...section,
      children: (section.children || []).filter((item) => {
        const roleVisible = canSeeItem(item.roles, currentUserRole);
        if (!Array.isArray(item.permissions) || item.permissions.length === 0) {
          return roleVisible;
        }

        if (permissions.includes('*')) {
          return true;
        }

        return roleVisible && item.permissions.some((permission) => permissions.includes(permission));
      }),
    }))
    .filter((section) => (section.children || []).length > 0);

  return (
    <List dense disablePadding sx={{ pt: 0.2 }}>
      {visibleNavItems.map((section) => (
        <Section key={section.label} title={section.label}>
          {section.children.map((item) => (
            <NavItem key={`${section.label}:${item.key}:${item.href}`} label={item.label} href={item.href} />
          ))}
        </Section>
      ))}
    </List>
  );
}
