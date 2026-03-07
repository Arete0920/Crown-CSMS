$base = "C:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src\pages"
$files = @(
  "AcademicYearWizard.jsx","AftercareRosterPage.jsx","BellScheduleWizard.jsx",
  "CategoryWeightsEditor.jsx","CommsComposePage.jsx","CommsInboxPage.jsx",
  "CommsThreadPage.jsx","CommunicationsThreadsList.jsx","DisciplinePage.jsx",
  "EnrollmentPeriodWizard.jsx","FeeScheduleWizard.jsx","FinanceInvoicesList.jsx",
  "GradeScaleWizard.jsx","Login.jsx","LoginPage.jsx","StaffOnboardingWizard.jsx",
  "Student360Page.jsx","TeamsPreviewPage.jsx","TermStructureWizard.jsx","TranscriptRO.jsx"
)
$sb = [System.Text.StringBuilder]::new()
foreach ($f in $files) {
    $path = "$base\$f"
    $lines = [System.IO.File]::ReadAllLines($path)
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("==== $f ($($lines.Count) lines) ====")
    $hasHit = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '#[0-9a-fA-F]{3,6}') {
            $hasHit = $true
            [void]$sb.AppendLine("  --- HIT L$($i+1) ---")
            $s = [Math]::Max(0, $i - 3)
            $e = [Math]::Min($lines.Count - 1, $i + 3)
            for ($j = $s; $j -le $e; $j++) {
                $mk = if ($j -eq $i) { ">>>" } else { "   " }
                [void]$sb.AppendLine("$mk $($j+1): $($lines[$j])")
            }
        }
    }
    if (-not $hasHit) { [void]$sb.AppendLine("  (no hex color hits)") }
}
$outFile = "C:\Users\JMega\OneDrive\Desktop\Crown2026\hex_audit.txt"
[System.IO.File]::WriteAllText($outFile, $sb.ToString())
Write-Host "Written to $outFile"
