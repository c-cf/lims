'use client';
import React from 'react';

type IconProps = {
  children?: React.ReactNode;
  size?: number;
  color?: string;
  strokeWidth?: number;
  style?: React.CSSProperties;
  [key: string]: unknown;
};

const Icon = ({
  children,
  size = 16,
  color = 'currentColor',
  strokeWidth = 2,
  style,
  ...rest
}: IconProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ flexShrink: 0, ...style }}
    {...(rest as React.SVGProps<SVGSVGElement>)}
  >
    {children}
  </svg>
);
export default Icon;
export { Icon };
