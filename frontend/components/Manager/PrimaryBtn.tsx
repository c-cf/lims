'use client';
import type { ReactNode, CSSProperties } from 'react';
import { ink as mInk } from '@/lib/colors';

const PrimaryBtn = ({
  children,
  onClick,
  icon = undefined,
  disabled = false,
  danger = false,
  success = false,
  style = undefined,
}: {
  children?: ReactNode;
  onClick?: () => void;
  icon?: ReactNode;
  disabled?: boolean;
  danger?: boolean;
  success?: boolean;
  style?: CSSProperties;
}) => {
  const bg = disabled ? '#dcdce3' : danger ? '#b9384a' : success ? '#2e6a47' : mInk;
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 7,
        padding: '10px 16px',
        borderRadius: 8,
        background: bg,
        color: '#fff',
        border: 'none',
        fontSize: 13,
        fontWeight: 600,
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontFamily: 'inherit',
        ...style,
      }}
    >
      {icon}
      {children}
    </button>
  );
};
export default PrimaryBtn;
export { PrimaryBtn };
