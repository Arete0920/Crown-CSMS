export function getBuildInfo() {
  return {
    mode: import.meta.env.MODE || 'unknown',
    baseUrl: import.meta.env.BASE_URL || '/',
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'missing',
    buildSha: import.meta.env.VITE_BUILD_SHA || 'missing',
    buildTag: import.meta.env.VITE_BUILD_TAG || 'missing',
    buildTime: import.meta.env.VITE_BUILD_TIME || 'missing',
  };
}
