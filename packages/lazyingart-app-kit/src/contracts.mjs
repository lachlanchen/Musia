export class ContractError extends Error {
  constructor(code) {
    super(code);
    this.name = 'ContractError';
    this.code = code;
  }
}

export function requireContract(condition, code) {
  if (!condition) throw new ContractError(code);
}

function record(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

export function boundedText(value, max = 256) {
  return typeof value === 'string' && value.length > 0 && value.length <= max
    && !/[\u0000-\u001f\u007f]/u.test(value);
}

export function httpsUrl(value) {
  requireContract(boundedText(value, 2048), 'invalid_https_url');
  let url;
  try { url = new URL(value); } catch { throw new ContractError('invalid_https_url'); }
  requireContract(url.protocol === 'https:' && !url.username && !url.password
    && !url.search && !url.hash && !/[?#*\\]/u.test(value), 'invalid_https_url');
  requireContract(url.href === value || (url.origin === value && url.pathname === '/'), 'noncanonical_url');
  return url;
}

export function validateIssuer(value) {
  const url = httpsUrl(value);
  requireContract(value === url.origin, 'invalid_issuer');
  return value;
}

export function validateRegistration(value) {
  requireContract(record(value), 'invalid_registration');
  validateIssuer(value.issuer);
  httpsUrl(value.redirectUri);
  requireContract(boundedText(value.clientId) && boundedText(value.audience), 'invalid_client_binding');
  requireContract(['public', 'confidential'].includes(value.type), 'invalid_client_type');
  return Object.freeze({ issuer: value.issuer, redirectUri: value.redirectUri,
    clientId: value.clientId, audience: value.audience, type: value.type });
}

const ENDPOINTS = Object.freeze({
  authorization_endpoint: '/account/authorize', token_endpoint: '/account/token',
  profile_endpoint: '/account/profile', revocation_endpoint: '/account/revoke', account_endpoint: '/account',
});

export function validateDiscovery(value, expectedIssuer) {
  validateIssuer(expectedIssuer);
  requireContract(record(value) && value.contract_version === 1, 'unsupported_account_contract');
  requireContract(value.issuer === expectedIssuer, 'issuer_mismatch');
  for (const [key, path] of Object.entries(ENDPOINTS)) {
    requireContract(value[key] === expectedIssuer + path, 'endpoint_mismatch');
  }
  for (const [key, required] of Object.entries({
    response_types_supported: ['code'], grant_types_supported: ['authorization_code', 'refresh_token'],
    code_challenge_methods_supported: ['S256'], scopes_supported: ['profile'],
  })) {
    requireContract(Array.isArray(value[key]) && required.every(item => value[key].includes(item)), 'unsupported_account_contract');
  }
  requireContract(value.registration_requires_invitation === false
    && typeof value.echomind_invitation_required === 'boolean', 'invalid_invitation_policy');
  requireContract(record(value.providers), 'invalid_providers');
  const providers = {};
  for (const provider of ['password', 'apple', 'google', 'github']) {
    requireContract(typeof value.providers[provider] === 'boolean', 'invalid_providers');
    providers[provider] = value.providers[provider];
  }
  return Object.freeze({
    contract_version: 1, issuer: expectedIssuer,
    ...Object.fromEntries(Object.entries(ENDPOINTS).map(([key, path]) => [key, expectedIssuer + path])),
    providers: Object.freeze(providers), registration_requires_invitation: false,
    echomind_invitation_required: value.echomind_invitation_required,
  });
}

export function validateProfile(value, clientId) {
  requireContract(record(value) && boundedText(value.subject), 'invalid_profile');
  requireContract(value.client_id === clientId, 'profile_client_mismatch');
  requireContract(value.account_status === 'active', 'account_not_active');
  requireContract(typeof value.display_name === 'string' && value.display_name.length <= 256
    && !/[\u0000-\u001f\u007f]/u.test(value.display_name), 'invalid_profile');
  return Object.freeze({ subject: value.subject, display_name: value.display_name,
    client_id: clientId, account_status: 'active' });
}

// A tuple avoids delimiter collisions. Never substitute email for subject.
export function accountKey(issuer, subject) {
  validateIssuer(issuer);
  requireContract(boundedText(subject), 'invalid_subject');
  return JSON.stringify([issuer, subject]);
}

const SESSION_STATES = ['guest', 'active', 'offline', 'reauth_required'];
const ACCESS_STATES = ['active', 'invitation_required', 'purchase_required', 'suspended', 'unknown'];

// UI guidance only. Protected services must independently authorize every operation.
export function featureDecision(feature, sessionState = 'guest', accessState = 'unknown') {
  requireContract(record(feature) && typeof feature.available === 'boolean'
    && typeof feature.requiresAccount === 'boolean' && typeof feature.requiresAccess === 'boolean', 'invalid_feature');
  requireContract(SESSION_STATES.includes(sessionState) && ACCESS_STATES.includes(accessState), 'invalid_access_state');
  if (!feature.available) return 'unavailable';
  if (feature.requiresAccount && sessionState !== 'active') {
    return sessionState === 'offline' ? 'offline' : 'sign_in';
  }
  if (feature.requiresAccess && accessState !== 'active') return accessState;
  return 'available';
}

export function validateAppManifest(value) {
  requireContract(record(value) && value.schemaVersion === 1, 'invalid_app_manifest');
  requireContract(boundedText(value.appId) && /^[a-z][a-z0-9-]{1,63}$/.test(value.appId)
    && boundedText(value.displayName) && boundedText(value.candidate), 'invalid_app_id');
  requireContract(record(value.account) && typeof value.account.enabled === 'boolean', 'invalid_account_config');
  requireContract(Array.isArray(value.account.registrations), 'invalid_registrations');
  const registrations = new Set();
  for (const item of value.account.registrations) {
    validateRegistration(item);
    requireContract(['web', 'ios', 'android', 'macos'].includes(item.platform), 'invalid_platform');
    const key = JSON.stringify([item.issuer, item.clientId]);
    requireContract(!registrations.has(key), 'duplicate_client');
    registrations.add(key);
  }
  requireContract(Array.isArray(value.features) && value.features.length > 0, 'invalid_features');
  const features = new Set();
  for (const feature of value.features) {
    requireContract(record(feature) && boundedText(feature.id)
      && /^[a-z][a-zA-Z0-9]{1,63}$/.test(feature.id) && !features.has(feature.id), 'invalid_feature_id');
    featureDecision(feature);
    requireContract(typeof feature.explicitConfirmation === 'boolean', 'invalid_feature_confirmation');
    features.add(feature.id);
  }
  return value;
}

export const ACCEPTANCE_GATES = Object.freeze([
  'liveDiscovery', 'registeredCallback', 'liveCodeExchange', 'refreshRecovery',
  'relaunchAndDraftRecovery', 'revocationAndSignOut', 'legacyLinkProof',
  'entitlementIsolation', 'deletionAndRetention', 'privacyAndReview',
]);

// Receipts are per candidate AND client, never transferable between app/platform builds.
export function assessReadiness(manifest, evidence = {}) {
  validateAppManifest(manifest);
  requireContract(record(evidence), 'invalid_evidence');
  const blockers = [];
  if (!manifest.account.enabled) blockers.push('disabled_by_default');
  if (!manifest.account.registrations.length) blockers.push('no_registered_clients');
  const clients = manifest.account.registrations.map(registration => {
    const key = JSON.stringify([registration.issuer, registration.clientId]);
    const receipt = record(evidence.clients) ? evidence.clients[key] : null;
    const bound = record(receipt) && receipt.audience === registration.audience
      && receipt.redirectUri === registration.redirectUri && receipt.platform === registration.platform
      && receipt.candidate === manifest.candidate && boundedText(receipt.verifiedAt)
      && Number.isFinite(Date.parse(receipt.verifiedAt));
    const missing = ACCEPTANCE_GATES.filter(gate => !bound || receipt.checks?.[gate] !== true);
    if (missing.length) blockers.push(`client_not_verified:${registration.clientId}`);
    return { clientId: registration.clientId, platform: registration.platform, missing };
  });
  return { appId: manifest.appId, configurationValid: true,
    readyForOwnerReview: blockers.length === 0, liveServiceVerifiedByThisTool: false,
    blockers, clients };
}
