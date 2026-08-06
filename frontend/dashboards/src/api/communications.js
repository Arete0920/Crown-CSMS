import { apiGet, apiGetList } from './request';
import { buildApiPath } from '../utils/apiContracts';

/**
 * Fetch message threads list
 * @returns {Promise<Array>} - array of thread objects
 */
export const getThreads = async () => {
  return apiGetList(buildApiPath('communications.threads.list'));
};

/**
 * Fetch thread detail with messages
 * @param {string} threadId - UUID of the thread
 * @returns {Promise<Object>} - thread object with messages array
 */
export const getThreadDetail = async (threadId) => {
  return apiGet(
    buildApiPath('communications.threads.detail', {
      threadId,
    }),
  );
};

