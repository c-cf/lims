'use client';
import React from 'react';

const FabCard = ({
  children,
  padding = 22,
  style = undefined,
}: {
  children?: React.ReactNode;
  padding?: number;
  style?: React.CSSProperties;
}) => (
  <div
    style={{
      background: '#fff',
      borderRadius: 14,
      border: '1px solid rgba(0,0,0,0.07)',
      padding,
      boxShadow: '0 1px 2px rgba(30,30,36,0.03)',
      ...style,
    }}
  >
    {children}
  </div>
);
export default FabCard;
export { FabCard };
