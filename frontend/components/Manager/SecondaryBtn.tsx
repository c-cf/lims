'use client';
import { ink as mInk } from '@/lib/colors';
import { line as mLine } from '@/lib/colors';

const SecondaryBtn = ({
  children,
  onClick,
  icon = undefined,
  disabled = false,
  danger = false,
  style = undefined,
}) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 7,
      padding: '9px 14px',
      borderRadius: 8,
      background: '#fff',
      color: danger ? '#b9384a' : mInk,
      border: `1px solid ${danger ? '#e6c2c7' : mLine}`,
      fontSize: 13,
      fontWeight: 600,
      cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.55 : 1,
      fontFamily: 'inherit',
      ...style,
    }}
  >
    {icon}
    {children}
  </button>
);
export default SecondaryBtn;
export { SecondaryBtn };
