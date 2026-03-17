'use client';
import { create } from 'zustand';
import type { UserMe } from '@/types/api';

type State = {
  token: string | null;
  me: UserMe | null;
  setToken: (token: string | null) => void;
  setMe: (me: UserMe | null) => void;
  logout: () => void;
};

export const useAuthStore = create<State>((set) => ({
  token: typeof window !== 'undefined' ? localStorage.getItem('dw_token') : null,
  me: null,
  setToken: (token) => {
    if (typeof window !== 'undefined') {
      if (token) { localStorage.setItem('dw_token', token); document.cookie = `dw_token=${token}; path=/`; }
      else { localStorage.removeItem('dw_token'); document.cookie = 'dw_token=; Max-Age=0; path=/'; }
    }
    set({ token });
  },
  setMe: (me) => set({ me }),
  logout: () => {
    if (typeof window !== 'undefined') { localStorage.removeItem('dw_token'); document.cookie = 'dw_token=; Max-Age=0; path=/'; }
    set({ token: null, me: null });
  }
}));
