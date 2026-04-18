import React, { useState } from "react";
import { Button, CircularProgress } from "@mui/material";
import releaseApi from "../../lib/releaseApi";

const DownloadIcon = () => <span aria-hidden="true">DL</span>;

type ReleaseReport =
  | "transcript"
  | "report-card"
  | "discipline"
  | "board";

interface Props {
  report: ReleaseReport;
  studentRef?: string;
  label?: string;
  testId?: string;
}

const buildUrl = (report: ReleaseReport, studentRef?: string) => {
  switch (report) {
    case "transcript":
      return `/api/v1/reports/transcript/${studentRef ?? "DEMO-001"}/`;
    case "report-card":
      return `/api/v1/reports/report-card/${studentRef ?? "DEMO-001"}/`;
    case "discipline":
      return `/api/v1/reports/discipline/${studentRef ?? "DEMO-001"}/`;
    case "board":
      return `/api/v1/reports/board/`;
    default:
      return `/api/v1/reports/board/`;
  }
};

export default function ReleaseExportButton({
  report,
  studentRef,
  label,
  testId,
}: Props) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const response = await releaseApi.get(buildUrl(report, studentRef), {
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: "application/pdf" });
      const link = Object.assign(document.createElement("a"), {
        href: URL.createObjectURL(blob),
        download: `${report}.pdf`,
      });
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant="outlined"
      size="small"
      onClick={handleClick}
      disabled={loading}
      data-testid={testId || `release-export-${report}`}
      startIcon={loading ? <CircularProgress size={14} /> : <DownloadIcon />}
      sx={{ textTransform: "none", fontWeight: 500 }}
    >
      {label || `Download ${report}`}
    </Button>
  );
}
