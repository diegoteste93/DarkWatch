'use client';
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { useAuthStore } from '@/store/auth';
import type { ApiEnvelope, UserMe } from '@/types/api';

export function useAuthBootstrap(enabled = true) {
  const { token, setMe } = useAuthStore();
  return useQuery({
    queryKey: ['auth-me'],
    enabled: enabled && !!token,
    queryFn: async () => {
      const { data } = await api.get<ApiEnvelope<UserMe>>('/auth/me');
      setMe(data.data);
      return data.data;
    }
  });
}
