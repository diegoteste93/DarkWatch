'use client';
export function toastError(message: string) {
  if (typeof window !== 'undefined') window.alert(message);
}
