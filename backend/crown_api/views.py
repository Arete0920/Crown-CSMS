from django.shortcuts import render


def director_dashboard_page(request):
    """Serve the Director Dashboard HTML page."""
    return render(request, "director_dashboard.html")
