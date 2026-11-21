import { useCallback, useEffect, useMemo, useState } from 'react';

export function useWizardDraft(wizardKey, initialValue, { storage = 'local' } = {}) {
  const storageName = storage === 'session' ? 'sessionStorage' : 'localStorage';
  const storageKey = useMemo(() => `crown_wizard_draft:${wizardKey}`, [wizardKey]);

  const [value, setValue] = useState(initialValue);
  const [loaded, setLoaded] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState(null);

  useEffect(() => {
    try {
      const raw = globalThis[storageName].getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object' && parsed.__draftVersion === 2) {
          setValue(parsed.value ?? initialValue);
          setLastSavedAt(parsed.savedAt || null);
        } else {
          setValue(parsed);
          setLastSavedAt(null);
        }
      }
    } catch {
      // Ignore malformed local draft payloads.
    } finally {
      setLoaded(true);
    }
  }, [initialValue, storageKey, storageName]);

  const saveDraft = useCallback(
    (nextValue) => {
      const toSave = nextValue ?? value;
      const savedAt = new Date().toISOString();
      globalThis[storageName].setItem(
        storageKey,
        JSON.stringify({
          __draftVersion: 2,
          value: toSave,
          savedAt,
        }),
      );
      setLastSavedAt(savedAt);
    },
    [storageKey, value, storageName],
  );

  const clearDraft = useCallback(() => {
    globalThis[storageName].removeItem(storageKey);
    setLastSavedAt(null);
  }, [storageKey, storageName]);

  return {
    value,
    setValue,
    saveDraft,
    clearDraft,
    loaded,
    lastSavedAt,
  };
}
