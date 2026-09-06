import { useEffect, useRef } from 'react';

export const useBackButtonProtection = (isExamActive) => {
  const warningShownRef = useRef(false);

  useEffect(() => {
    if (!isExamActive) {
      warningShownRef.current = false;
      return;
    }

    const handlePopState = (e) => {
      if (isExamActive) {
        e.preventDefault();
        // Push state again to maintain history
        window.history.pushState(null, '', window.location.href);
        
        // Return true to signal back button was intercepted
        return true;
      }
    };

    // Push initial state
    window.history.pushState(null, '', window.location.href);

    window.addEventListener('popstate', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [isExamActive]);

  const showWarningNeeded = () => {
    if (!warningShownRef.current) {
      warningShownRef.current = true;
      return true;
    }
    return false;
  };

  const resetWarningFlag = () => {
    warningShownRef.current = false;
  };

  return { showWarningNeeded, resetWarningFlag };
};
