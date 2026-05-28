'use client';
import React from 'react';

function TweakSection({
  label,
  children = undefined,
}: {
  label: string;
  children?: React.ReactNode;
}) {
  return (
    <>
      <div className="twk-sect">{label}</div>
      {children}
    </>
  );
}
export default TweakSection;
export { TweakSection };
