import { useState, useEffect, useRef } from 'react';

export const useTimer = (durationMinutes, onTimeExpired) => {
  const [remainingTime, setRemainingTime] = useState(0);
  const [isRunning, setIsRunning] = useState(true);
  const timerIntervalRef = useRef(null);

  useEffect(() => {
  if (!durationMinutes || durationMinutes <= 0) {
    return;
  }

  setRemainingTime(durationMinutes * 60);
  setIsRunning(true);
}, [durationMinutes]);

useEffect(() => {
  if (!isRunning || remainingTime <= 0) {
    return;
  }

  timerIntervalRef.current = setInterval(() => {
    setRemainingTime((prev) => {
      if (prev <= 1) {
        clearInterval(timerIntervalRef.current);
        setIsRunning(false);

        if (onTimeExpired) {
          onTimeExpired();
        }

        return 0;
      }

      return prev - 1;
    });
  }, 1000);

  return () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
  };
}, [isRunning, remainingTime, onTimeExpired]);

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const pause = () => setIsRunning(false);
  const resume = () => setIsRunning(true);
  const reset = (newDuration) => {
    setIsRunning(true);
    setRemainingTime(newDuration * 60);
  };

  return {
    remainingTime,
    formattedTime: formatTime(remainingTime),
    isRunning,
    isExpired: remainingTime <= 0,
    pause,
    resume,
    reset,
  };
};
