'use client';
import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import LoginPage from '@/components/Login/LoginPage';
import TweaksUI from '@/components/App/TweaksUI';
import useTweaks from '@/components/Tweaks/useTweaks';
import { SESSION_KEY, TWEAK_DEFAULTS } from '@/components/App/constants';
import { roleHome } from '@/lib/navigate';

export default function Page() {
  const router = useRouter();
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty('--tweak-signin-bg', t.signInBg);
    root.style.setProperty('--tweak-signin-fg', t.signInFg);
    root.style.setProperty('--tweak-fab-bg', t.fabBg);
  }, [t.signInBg, t.signInFg, t.fabBg]);

  // Already logged in → redirect
  useEffect(() => {
    try {
      const stored = localStorage.getItem(SESSION_KEY);
      if (stored) {
        const u = JSON.parse(stored);
        router.replace(roleHome(u.role));
      }
    } catch {}
  }, [router]);

  const handleLogin = (user) => {
    localStorage.setItem(SESSION_KEY, JSON.stringify(user));
    router.push(roleHome(user.role));
  };

  return (
    <div data-screen-label="Login">
      <LoginPage onLogin={handleLogin} />
      <TweaksUI t={t} setTweak={setTweak} />
    </div>
  );
}
