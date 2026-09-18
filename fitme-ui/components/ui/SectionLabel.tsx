import React from "react";

interface SectionLabelProps {
  label: string;
  chapter?: string;
  className?: string;
}

export function SectionLabel({ label, chapter, className = "" }: SectionLabelProps) {
  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#2D3339] bg-[#121517]/80 backdrop-blur-sm ${className}`}
    >
      <span className="w-2 h-2 rounded-full bg-[#76C043] animate-pulse" />
      <span className="text-xs font-semibold tracking-widest uppercase text-[#9CA3AF]">
        {chapter ? (
          <>
            <span className="text-[#76C043]">{chapter}</span>
            <span className="mx-1.5 opacity-40">•</span>
          </>
        ) : null}
        {label}
      </span>
    </div>
  );
}

export default SectionLabel;
