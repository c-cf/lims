'use client';
import React from 'react';
import * as I from '@/components/ui/I';
import { muted as mMuted } from '@/lib/colors';
import { accent as mAccent } from '@/lib/colors';
import { text2 as mText2 } from '@/lib/colors';
const MI = I;
const Breadcrumb = ({ items }) => (
  <div
    style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginBottom: 14, fontSize: 13 }}
  >
    {items.map((it, i) => (
      <React.Fragment key={i}>
        {i > 0 && <MI.ChevronRight size={13} color={mMuted} />}
        {it.onClick ? (
          <button
            onClick={it.onClick}
            style={{
              background: 'transparent',
              border: 'none',
              padding: '2px 4px',
              cursor: 'pointer',
              color: mAccent,
              fontWeight: 600,
              fontFamily: 'inherit',
              fontSize: 13,
            }}
          >
            {it.label}
          </button>
        ) : (
          <span style={{ color: mText2, fontWeight: 500, padding: '2px 4px' }}>{it.label}</span>
        )}
      </React.Fragment>
    ))}
  </div>
);
export default Breadcrumb;
export { Breadcrumb };
