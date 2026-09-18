import React from "react";
import Image from "next/image";
import Link from "next/link";

export interface ProgramItem {
  id: string;
  title: string;
  category: string;
  description: string;
  difficulty: "All Levels" | "Beginner" | "Intermediate" | "Advanced";
  sessionsPerWeek: string;
  imageUrl: string;
  imageAlt: string;
}

interface ProgramCardProps {
  program: ProgramItem;
}

export function ProgramCard({ program }: ProgramCardProps) {
  return (
    <div className="group relative flex flex-col justify-between overflow-hidden rounded-xl border border-[#2D3339] bg-[#121517] transition-all duration-300 hover:border-[#76C043]/50 hover:shadow-[0_12px_32px_rgba(0,0,0,0.6)]">
      {/* Top Image Container */}
      <div className="relative h-64 w-full overflow-hidden bg-[#0E1012]">
        <Image
          src={program.imageUrl}
          alt={program.imageAlt}
          fill
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          className="object-cover transition-transform duration-500 ease-out group-hover:scale-105"
        />
        {/* Dark subtle gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#121517] via-[#121517]/40 to-transparent" />

        {/* Category tag */}
        <div className="absolute top-4 left-4">
          <span className="rounded bg-[#0B0D0E]/80 backdrop-blur-md px-2.5 py-1 text-[11px] font-semibold uppercase tracking-widest text-[#76C043] border border-[#2D3339]">
            {program.category}
          </span>
        </div>
      </div>

      {/* Card Content */}
      <div className="flex flex-1 flex-col justify-between p-6">
        <div>
          <h3 className="text-xl font-bold tracking-tight text-[#F8FAFC] group-hover:text-[#76C043] transition-colors duration-200">
            {program.title}
          </h3>
          <p className="mt-2.5 text-sm leading-relaxed text-[#9CA3AF]">
            {program.description}
          </p>
        </div>

        <div className="mt-6 pt-5 border-t border-[#2D3339]/70">
          <div className="flex items-center justify-between text-xs text-[#9CA3AF] mb-4">
            <span className="flex items-center gap-1.5 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-[#76C043]" />
              {program.difficulty}
            </span>
            <span className="font-mono text-[#F8FAFC]/80">{program.sessionsPerWeek}</span>
          </div>

          <Link
            href="#membership"
            className="inline-flex items-center gap-2 text-xs font-bold tracking-wider uppercase text-[#76C043] transition-all duration-200 group-hover:translate-x-1"
          >
            <span>VIEW PROGRAM</span>
            <svg
              className="w-3.5 h-3.5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default ProgramCard;
