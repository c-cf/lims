'use client';
import React from 'react';

function TweakRow({
  label,
  value = undefined,
  children = undefined,
  inline = false,
}: {
  label: string;
  value?: string | number;
  children?: React.ReactNode;
  inline?: boolean;
}) {
  return (
    <div className={inline ? 'twk-row twk-row-h' : 'twk-row'}>
      <div className="twk-lbl">
        <span>{label}</span>
        {value != null && <span className="twk-val">{value}</span>}
      </div>
      {children}
    </div>
  );
}
export default TweakRow;
export { TweakRow };
