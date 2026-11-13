export const unstable_ImmediatePriority = 1;
export const unstable_UserBlockingPriority = 2;
export const unstable_NormalPriority = 3;
export const unstable_LowPriority = 4;
export const unstable_IdlePriority = 5;

let currentPriority = unstable_NormalPriority;

export function unstable_now(): number {
  return typeof performance !== 'undefined' && typeof performance.now === 'function'
    ? performance.now()
    : Date.now();
}

export function unstable_scheduleCallback(
  priorityLevel: number,
  callback: (arg: { didTimeout: boolean; timeRemaining: () => number }) => void,
  options?: { delay?: number }
) {
  const delay = options?.delay && options.delay > 0 ? options.delay : 0;
  const timerId = setTimeout(() => {
    callback({ didTimeout: true, timeRemaining: () => 0 });
  }, delay);

  return { id: timerId, callback, priorityLevel };
}

export function unstable_cancelCallback(task: { id?: any; callback?: any } | null | undefined) {
  if (task && task.id) {
    clearTimeout(task.id);
    task.callback = null;
  }
}

export function unstable_shouldYield(): boolean {
  return false;
}

export function unstable_requestPaint(): void {}

export function unstable_runWithPriority<T>(priorityLevel: number, eventHandler: () => T): T {
  const prev = currentPriority;
  currentPriority = priorityLevel;
  try {
    return eventHandler();
  } finally {
    currentPriority = prev;
  }
}

export function unstable_next<T>(eventHandler: () => T): T {
  return eventHandler();
}

export function unstable_wrapCallback<T extends (...args: any[]) => any>(callback: T): T {
  return callback;
}

export function unstable_getCurrentPriorityLevel(): number {
  return currentPriority;
}

export function unstable_getFirstCallbackNode() {
  return null;
}

export function unstable_pauseExecution(): void {}
export function unstable_continueExecution(): void {}
export const unstable_Profiling = null;

const schedulerShim = {
  unstable_ImmediatePriority,
  unstable_UserBlockingPriority,
  unstable_NormalPriority,
  unstable_LowPriority,
  unstable_IdlePriority,
  unstable_now,
  unstable_scheduleCallback,
  unstable_cancelCallback,
  unstable_shouldYield,
  unstable_requestPaint,
  unstable_runWithPriority,
  unstable_next,
  unstable_wrapCallback,
  unstable_getCurrentPriorityLevel,
  unstable_getFirstCallbackNode,
  unstable_pauseExecution,
  unstable_continueExecution,
  unstable_Profiling,
};

export default schedulerShim;
