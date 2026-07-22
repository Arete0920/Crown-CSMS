Set-StrictMode -Version Latest

function Get-GauntletStaticAssertions {
    [CmdletBinding()]
    param()

    return @(
        [pscustomobject]@{
            Name = "18_sandbox_nav_flag_static_assertions"
            Path = "frontend/dashboards/src/components/navigation/dashboardNavConfig.js"
            Patterns = @(
                "VITE_SANDBOX_READY_ONLY",
                "VITE_HIDE_UNREADY_NAV",
                "VITE_SANDBOX_MODE",
                "isProductionReady",
                "visibleStaticSections = readyOnly"
            )
        },
        [pscustomobject]@{
            Name = "19_backend_dashboard_sample_fail_closed_assertions"
            Path = "backend/crown_api/dashboards/views.py"
            Patterns = @(
                "CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS",
                "dashboard_live_data_required",
                "No live or snapshot payload is available",
                "sample_payload_allowed"
            )
        }
    )
}

Export-ModuleMember -Function Get-GauntletStaticAssertions