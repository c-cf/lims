'use client';
import React from 'react';

const onFocus = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
  e.target.style.borderColor = '#6c67b8';
  e.target.style.background = '#fff';
  e.target.style.boxShadow = '0 0 0 3px rgba(108,103,184,0.12)';
};
export default onFocus;
export { onFocus };
