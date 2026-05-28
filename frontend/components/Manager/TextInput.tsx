'use client';
import type { InputHTMLAttributes } from 'react';
import inputStyle from '@/components/Manager/utils/inputStyle';

const TextInput = (p: InputHTMLAttributes<HTMLInputElement>) => (
  <input {...p} style={{ ...inputStyle, ...p.style }} />
);
export default TextInput;
export { TextInput };
