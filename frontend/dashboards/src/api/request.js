import { crownApiClient } from './client';
import { unwrapApiList, unwrapApiResponse } from './unwrap';

export async function apiGet(path, config = {}) {
  const response = await crownApiClient.get(path, config);
  return unwrapApiResponse(response);
}

export async function apiGetList(path, config = {}) {
  const response = await crownApiClient.get(path, config);
  return unwrapApiList(response);
}

export async function apiPost(path, payload = {}, config = {}) {
  const response = await crownApiClient.post(path, payload, config);
  return unwrapApiResponse(response);
}

export async function apiPatch(path, payload = {}, config = {}) {
  const response = await crownApiClient.patch(path, payload, config);
  return unwrapApiResponse(response);
}

export async function apiPut(path, payload = {}, config = {}) {
  const response = await crownApiClient.put(path, payload, config);
  return unwrapApiResponse(response);
}

export async function apiDelete(path, config = {}) {
  const response = await crownApiClient.delete(path, config);
  return unwrapApiResponse(response);
}
