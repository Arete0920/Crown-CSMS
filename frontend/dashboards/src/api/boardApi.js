// frontend/dashboards/src/api/boardApi.js
// Board Oversight API helpers — wired to the Crown API client.
// The existing BoardDashboard.jsx uses its own self-contained fetch;
// this module is provided for future components that adopt useApiClient().
import { useApiClient } from "./apiClient";

export function useBoardApi() {
  const { request } = useApiClient();

  return {
    fetchMetrics: () =>
      request("/api/v1/board/metrics/"),

    fetchDashboard: () =>
      request("/api/v1/board/dashboard/"),

    fetchPackets: () =>
      request("/api/v1/board/packets/"),

    fetchSnapshots: () =>
      request("/api/v1/board/snapshots/"),

    fetchPacket: (packetId) =>
      request(`/api/v1/board/packets/${packetId}/`),
  };
}
