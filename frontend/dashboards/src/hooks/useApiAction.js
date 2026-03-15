import { useState } from 'react';

export function useApiAction(action) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = async (...args) => {
    setLoading(true);
    setError(null);

    try {
      return await action(...args);
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => setError(null);

  return {
    run,
    loading,
    error,
    clearError,
  };
}
