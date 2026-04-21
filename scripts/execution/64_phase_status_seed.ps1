$ErrorActionPreference = "Stop"

$score = ".\docs\Crown_Master_Binder\03_Operations_and_Delivery\03_Phase_Progress_Scorecard.csv"
$gate  = ".\docs\Crown_Master_Binder\03_Operations_and_Delivery\09_Phase_Gate_Register.csv"

if (Test-Path $score) { Import-Csv $score | Format-Table -AutoSize }
if (Test-Path $gate)  { Import-Csv $gate  | Format-Table -AutoSize }
