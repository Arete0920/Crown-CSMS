import { useCallback, useEffect, useMemo, useState } from 'react';

export function useWizardDraft(wizardKey, initialValue) {
  const storageKey = useMemo(() => `crown_wizard_draft:${wizardKey}`, [wizardKey]);

  const [value, setValue] = useState(initialValue);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        setValue(parsed);
      }
    } catch {
      // Ignore malformed local draft payloads.
    } finally {
      setLoaded(true);
    }
  }, [storageKey]);

  const saveDraft = useCallback(
    (nextValue) => {
      const toSave = nextValue ?? value;
      window.localStorage.setItem(storageKey, JSON.stringify(toSave));
    },
    [storageKey, value],
  );

  const clearDraft = useCallback(() => {
    window.localStorage.removeItem(storageKey);
  }, [storageKey]);

  return {
    value,
    setValue,
    saveDraft,
    clearDraft,
    loaded,
  };
}
