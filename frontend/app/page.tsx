'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { SESSION_KEY } from '@/components/App/constants';
import { roleHome } from '@/lib/navigate';

export default function Page(): null {
  const router = useRouter();
  useEffect(() => {
    try {
      const stored = localStorage.getItem(SESSION_KEY);
      if (stored) {
        const u = JSON.parse(stored);
        router.replace(roleHome(u.role));
        return;
      }
    } catch {}
    router.replace('/login');
  }, [router]);
  return null;
}
