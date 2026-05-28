'use client';
import type { ReactNode, CSSProperties } from 'react';
import { lineSoft as mLineSft } from '@/lib/colors';
import { text2 as mText2 } from '@/lib/colors';

const CardHeader = ({
  children,
  style = undefined,
}: {
  children?: ReactNode;
  style?: CSSProperties;
}) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '14px 20px',
      borderBottom: `1px solid ${mLineSft}`,
      fontSize: 11,
      fontWeight: 700,
      color: mText2,
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      ...style,
    }}
  >
    {children}
  </div>
);
export default CardHeader;
export { CardHeader };
