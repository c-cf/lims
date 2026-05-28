'use client';
import inputStyle from '@/components/Manager/utils/inputStyle';

const SelectInput = ({ value, onChange, children, style = undefined }) => (
  <select value={value} onChange={onChange} style={{ ...inputStyle, cursor: 'pointer', ...style }}>
    {children}
  </select>
);
export default SelectInput;
export { SelectInput };
