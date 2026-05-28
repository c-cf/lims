'use client';
import React from 'react';

function useTweaks<T extends Record<string, string>>(
  defaults: T,
): [T, (keyOrEdits: keyof T | Partial<T>, val?: T[keyof T]) => void] {
  const [values, setValues] = React.useState<T>(defaults);
  const setTweak = React.useCallback((keyOrEdits: keyof T | Partial<T>, val?: T[keyof T]) => {
    const edits: Partial<T> =
      typeof keyOrEdits === 'object' && keyOrEdits !== null
        ? keyOrEdits
        : ({ [keyOrEdits as string]: val } as Partial<T>);
    setValues((prev: T) => ({ ...prev, ...edits }));
    window.parent.postMessage({ type: '__edit_mode_set_keys', edits }, '*');
    window.dispatchEvent(new CustomEvent('tweakchange', { detail: edits }));
  }, []);
  return [values, setTweak];
}
export default useTweaks;
export { useTweaks };
