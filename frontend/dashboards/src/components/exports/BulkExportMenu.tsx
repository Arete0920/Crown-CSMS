import React, { useState } from "react";
import {
  Button,
  Menu,
  MenuItem,
  CircularProgress,
  Divider,
  Typography,
} from "@mui/material";
import { authenticatedFetch } from "../../utils/authClient";

const ArrowDropDownIcon = () => <span aria-hidden="true">v</span>;

interface BulkExportMenuProps {
  label?: string;
  dateFrom?: string;
  dateTo?: string;
  gradeLevel?: string;
  schoolYear?: string;
}

const BulkExportMenu: React.FC<BulkExportMenuProps> = ({
  label = "Export",
  dateFrom = new Date(new Date().getFullYear(), 6, 1).toISOString().split("T")[0],
  dateTo = new Date().toISOString().split("T")[0],
  gradeLevel,
  schoolYear,
}) => {
  const [anchor, setAnchor] = useState<null | HTMLElement>(null);
  const [loading, setLoading] = useState(false);

  const open = (e: React.MouseEvent<HTMLElement>) => setAnchor(e.currentTarget);
  const close = () => setAnchor(null);

  const download = async (url: string, params: Record<string, string>, filename: string) => {
    setLoading(true);
    close();
    try {
      const resp = await authenticatedFetch(url, { query: params });
      const blob = await resp.blob();
      const link = Object.assign(document.createElement("a"), {
        href: window.URL.createObjectURL(blob),
        download: filename,
      });
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        variant="outlined"
        size="small"
        endIcon={loading ? <CircularProgress size={14} /> : <ArrowDropDownIcon />}
        onClick={open}
        disabled={loading}
        sx={{ textTransform: "none", fontWeight: 500 }}
      >
        {label}
      </Button>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={close}>
        <Typography variant="caption" sx={{ px: 2, py: 0.5, display: "block", color: "text.secondary" }}>
          PDF Reports
        </Typography>
        <Divider />
        <MenuItem onClick={() => download(
          "/api/v1/reports/attendance/",
          { from: dateFrom, to: dateTo, ...(gradeLevel ? { grade: gradeLevel } : {}) },
          `attendance_${dateFrom}_${dateTo}.pdf`
        )}>
          Attendance Summary
        </MenuItem>
        <MenuItem onClick={() => download(
          "/api/v1/reports/board/",
          { ...(schoolYear ? { year: schoolYear } : {}) },
          `board_${schoolYear || "current"}.pdf`
        )}>
          Board Report
        </MenuItem>
      </Menu>
    </>
  );
};

export default BulkExportMenu;
