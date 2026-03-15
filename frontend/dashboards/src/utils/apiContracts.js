import { API_CONTRACTS } from '../config/apiContracts';

export function getApiContract(key) {
  const contract = API_CONTRACTS[key];

  if (!contract) {
    throw new Error(`Unknown API contract key: ${key}`);
  }

  return contract;
}

export function buildApiPath(key, params = {}) {
  const contract = getApiContract(key);

  return Object.entries(params).reduce((path, [paramKey, paramValue]) => {
    return path.replace(`:${paramKey}`, String(paramValue));
  }, contract.path);
}
