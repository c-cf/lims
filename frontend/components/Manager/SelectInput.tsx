'use client';
import type { ReactNode, CSSProperties, ChangeEvent } from 'react';
import inputStyle from '@/components/Manager/utils/inputStyle';

const SelectInput = ({
  value,
  onChange,
  children,
  style = undefined,
}: {
  value?: string | number;
  onChange?: (e: ChangeEvent<HTMLSelectElement>) => void;
  children?: ReactNode;
  style?: CSSProperties;
}) => (
  <select value={value} onChange={onChange} style={{ ...inputStyle, cursor: 'pointer', ...style }}>
    {children}
  </select>
);
export default SelectInput;
export { SelectInput };
