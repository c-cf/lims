'use client';
import type { ReactNode, CSSProperties } from 'react';
import { line as mLine } from '@/lib/colors';

const Card = ({
  children,
  padding = 22,
  style = undefined,
}: {
  children?: ReactNode;
  padding?: number;
  style?: CSSProperties;
}) => (
  <div
    style={{
      background: '#fff',
      borderRadius: 12,
      border: `1px solid ${mLine}`,
      padding,
      ...style,
    }}
  >
    {children}
  </div>
);
export default Card;
export { Card };
