'use client';
import React from 'react';

const DangerBtn = ({
  children,
  onClick,
  style,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  style?: React.CSSProperties;
}) => (
  <button
    onClick={onClick}
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '8px 14px',
      borderRadius: 8,
      background: '#fff',
      color: '#c0394a',
      fontWeight: 600,
      fontSize: 13,
      border: '1px solid #f4c8c8',
      cursor: 'pointer',
      ...style,
    }}
  >
    {children}
  </button>
);
export default DangerBtn;
export { DangerBtn };
