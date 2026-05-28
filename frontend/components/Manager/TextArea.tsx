'use client';
import type { TextareaHTMLAttributes } from 'react';
import inputStyle from '@/components/Manager/utils/inputStyle';

const TextArea = (p: TextareaHTMLAttributes<HTMLTextAreaElement>) => (
  <textarea
    {...p}
    style={{ ...inputStyle, minHeight: 70, resize: 'vertical', fontFamily: 'inherit', ...p.style }}
  />
);
export default TextArea;
export { TextArea };
