'use client';
import React from 'react';

const Card = ({
  children,
  style,
  padding = 0,
  ...rest
}: {
  children?: React.ReactNode;
  style?: React.CSSProperties;
  padding?: number;
  [key: string]: unknown;
}) => (
  <div
    {...rest}
    style={{
      background: '#fff',
      border: '1px solid var(--border)',
      borderRadius: 12,
      padding,
      ...style,
    }}
  >
    {children}
  </div>
);

export default Card;
export { Card };
