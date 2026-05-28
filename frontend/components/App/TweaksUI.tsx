'use client';
import { SIGNIN_OPTIONS, TWEAK_DEFAULTS } from './constants';
import FabGradient from './FabGradient';
import TweaksPanel from '@/components/Tweaks/TweaksPanel';
import TweakSection from '@/components/Tweaks/TweakSection';
import TweakColor from '@/components/Tweaks/TweakColor';
import TweakButton from '@/components/Tweaks/TweakButton';

type TweakDefaults = typeof TWEAK_DEFAULTS;
type SetTweak = (
  keyOrEdits: keyof TweakDefaults | Partial<TweakDefaults>,
  val?: TweakDefaults[keyof TweakDefaults],
) => void;

export default function TweaksUI({ t, setTweak }: { t: TweakDefaults; setTweak: SetTweak }) {
  return (
    <TweaksPanel>
      <TweakSection label="Sign in button" />
      <TweakColor
        label="Background"
        value={t.signInBg}
        options={SIGNIN_OPTIONS}
        onChange={(v) => setTweak('signInBg', String(v))}
      />
      <TweakColor
        label="Text"
        value={t.signInFg}
        options={['#ffffff', '#1e1e24', '#f7f8fa']}
        onChange={(v) => setTweak('signInFg', String(v))}
      />
      <TweakSection label="fab_user icon" />
      <FabGradient value={t.fabBg} onChange={(v) => setTweak('fabBg', v)} />
      <TweakButton
        onClick={() => setTweak({ ...TWEAK_DEFAULTS })}
        label="Reset to theme defaults"
      />
    </TweaksPanel>
  );
}
