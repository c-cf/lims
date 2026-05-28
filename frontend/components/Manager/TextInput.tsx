'use client';
import inputStyle from '@/components/Manager/utils/inputStyle';

const TextInput = (p) => <input {...p} style={{ ...inputStyle, ...p.style }} />;
export default TextInput;
export { TextInput };
