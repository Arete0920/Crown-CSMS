import { APP_PERMISSIONS } from '../auth/permissions';

export const API_CONTRACTS = {
  'admissions.applications.list': {
    method: 'GET',
    path: '/api/admissions/applications/',
    owner: 'AdmissionsPipelineList',
    permission: APP_PERMISSIONS.ADMISSIONS_VIEW,
    responseType: 'list',
  },
  'admissions.enroll': {
    method: 'POST',
    path: '/api/admissions/enroll/',
    owner: 'AdmissionsPipelineList',
    permission: APP_PERMISSIONS.ADMISSIONS_EDIT,
    responseType: 'object',
  },
  'finance.invoices.list': {
    method: 'GET',
    path: '/api/v1/billing/invoices/',
    owner: 'FinanceInvoicesList',
    permission: APP_PERMISSIONS.BILLING_VIEW,
    responseType: 'list',
  },
  'communications.threads.list': {
    method: 'GET',
    path: '/api/v1/threads/',
    owner: 'CommunicationsThreadsList',
    permission: APP_PERMISSIONS.COMMUNICATIONS_VIEW,
    responseType: 'list',
  },
  'communications.threads.detail': {
    method: 'GET',
    path: '/api/v1/threads/:threadId/',
    owner: 'CommunicationsThreadsList',
    permission: APP_PERMISSIONS.COMMUNICATIONS_VIEW,
    responseType: 'object',
  },
  'system.health': {
    method: 'GET',
    path: '/api/system/health/',
    owner: 'SystemStatusPage',
    permission: APP_PERMISSIONS.SYSTEM_VIEW,
    responseType: 'object',
  },
};
