import React, { useState } from "react";
import { Button, CircularProgress, Tooltip } from "@mui/material";
import axios from "axios";

const DownloadIcon = () => <span aria-hidden="true">DL</span>;

type ReportType =
  | "transcript"
  | "report-card"
  | "attendance-summary"
  | "financial-statement"
  | "aid-letter"
  | "board";

interface ExportButtonProps {
  type: ReportType;
  studentId?: number | string;
  householdId?: number | string;
  applicationId?: number | string;
  params?: Record<string, string | number>;
  label?: string;
  variant?: "contained" | "outlined" | "text";
  size?: "small" | "medium" | "large";
  color?: "primary" | "secondary" | "inherit";
}

const REPORT_URLS: Record<ReportType, (props: ExportButtonProps) => string> = {
  "transcript": (p) => `/api/v1/reports/transcript/${p.studentId}/`,
  "report-card": (p) => `/api/v1/reports/report-card/${p.studentId}/`,
  "attendance-summary": (_) => `/api/v1/reports/attendance/`,
  "financial-statement": (p) => `/api/v1/reports/financial-statement/${p.householdId}/`,
  "aid-letter": (p) => `/api/v1/reports/aid-letter/${p.applicationId}/`,
  "board": (_) => `/api/v1/reports/board/`,
};

const DEFAULT_LABELS: Record<ReportType, string> = {
  "transcript": "Download Transcript",
  "report-card": "Download Report Card",
  "attendance-summary": "Download Attendance Report",
  "financial-statement": "Download Statement",
  "aid-letter": "Download Aid Letter",
  "board": "Download Board Report",
};

const ExportButton: React.FC<ExportButtonProps> = ({
  type,
  studentId,
  householdId,
  applicationId,
  params = {},
  label,
  variant = "outlined",
  size = "small",
  color = "primary",
}) => {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("auth_token");
      const schoolId = localStorage.getItem("school_id");
      const url = REPORT_URLS[type]({ type, studentId, householdId, applicationId, params, label, variant, size, color });

      const resp = await axios.get(url, {
        params,
        responseType: "blob",
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
          "X-School-Id": schoolId || "",
        },
      });

      const blob = new Blob([resp.data], { type: "application/pdf" });
      const link = Object.assign(document.createElement("a"), {
        href: window.URL.createObjectURL(blob),
        download: `${type}.pdf`,
      });
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Tooltip title={DEFAULT_LABELS[type]}>
      <span>
        <Button
          variant={variant}
          size={size}
          color={color}
          onClick={handleDownload}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={14} /> : <DownloadIcon />}
          sx={{ textTransform: "none", fontWeight: 500 }}
        >
          {label || DEFAULT_LABELS[type]}
        </Button>
      </span>
    </Tooltip>
  );
};

export default ExportButton;
