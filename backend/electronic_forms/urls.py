from django.urls import path

from .api import (
    ElectronicConsentDisclosureView,
    ElectronicEnvelopeConsentView,
    ElectronicEnvelopeCreateView,
    ElectronicEnvelopeDetailView,
    ElectronicEnvelopePaperCopyView,
    ElectronicEnvelopeSignView,
    ElectronicEnvelopeWithdrawView,
    ElectronicFormTemplateListCreateView,
    MyElectronicEnvelopesView,
)

urlpatterns = [
    path("consent-disclosure/", ElectronicConsentDisclosureView.as_view(), name="electronic-consent-disclosure"),
    path("templates/", ElectronicFormTemplateListCreateView.as_view(), name="electronic-form-templates"),
    path("envelopes/", ElectronicEnvelopeCreateView.as_view(), name="electronic-envelope-create"),
    path("envelopes/my/", MyElectronicEnvelopesView.as_view(), name="electronic-envelope-my"),
    path("envelopes/<uuid:envelope_id>/", ElectronicEnvelopeDetailView.as_view(), name="electronic-envelope-detail"),
    path("envelopes/<uuid:envelope_id>/consent/", ElectronicEnvelopeConsentView.as_view(), name="electronic-envelope-consent"),
    path("envelopes/<uuid:envelope_id>/sign/", ElectronicEnvelopeSignView.as_view(), name="electronic-envelope-sign"),
    path("envelopes/<uuid:envelope_id>/withdraw-consent/", ElectronicEnvelopeWithdrawView.as_view(), name="electronic-envelope-withdraw"),
    path("envelopes/<uuid:envelope_id>/paper-copy/", ElectronicEnvelopePaperCopyView.as_view(), name="electronic-envelope-paper-copy"),
]
