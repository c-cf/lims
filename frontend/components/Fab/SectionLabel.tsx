'use client';
import React from 'react';

const SectionLabel = ({
  children,
  style = undefined,
}: {
  children?: React.ReactNode;
  style?: React.CSSProperties;
}) => (
  <div
    style={{
      fontSize: 11,
      fontWeight: 600,
      color: 'var(--text-secondary)',
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      marginBottom: 14,
      ...style,
    }}
  >
    {children}
  </div>
);
export default SectionLabel;
export { SectionLabel };
