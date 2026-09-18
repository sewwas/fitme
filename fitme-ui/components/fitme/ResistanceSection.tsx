import React from "react";
import { SectionLabel } from "../ui/SectionLabel";

const RESISTANCE_CARDS = [
  {
    number: "01",
    title: "NO PLAN",
    subtitle: "Random Workouts",
    description:
      "Aimless gym sessions and shifting routines produce exhaustion without adaptation. Without a structured progressive overload model, momentum quickly fades.",
    remedy: "Solution: Periodized training built around your baseline.",
  },
  {
    number: "02",
    title: "NO ACCOUNTABILITY",
    subtitle: "Solitary Drift",
    description:
      "Motivation is fleeting. When schedules get demanding and discomfort sets in, solitary routines break down without coach oversight and check-ins.",
    remedy: "Solution: Dedicated coaching support and scheduled check-ins.",
  },
  {
    number: "03",
    title: "NO MEASURABLE PROGRESS",
    subtitle: "Invisible Results",
    description:
      "Guessing weights, ignoring body composition metrics, and hoping for change creates frustration. You cannot optimize what you do not quantify.",
    remedy: "Solution: Bi-weekly metrics, strength logs, and milestone audits.",
  },
];

export function ResistanceSection() {
  return (
    <section
      id="the-start"
      className="relative w-full bg-[#0B0D0E] py-24 sm:py-32 border-t border-[#2D3339]/50"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header Block */}
        <div className="flex flex-col items-start max-w-3xl">
          <SectionLabel chapter="CHAPTER 02" label="THE RESISTANCE" />

          <h2 className="mt-5 text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#F8FAFC] uppercase">
            Why Do Fitness <br />
            <span className="text-[#9CA3AF]">Journeys Stop?</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-[#9CA3AF] font-medium border-l-2 border-[#76C043] pl-4">
            Fitness should not depend on motivation alone.
          </p>
        </div>

        {/* 3 Clean Resistance Cards */}
        <div className="mt-14 sm:mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {RESISTANCE_CARDS.map((card) => (
            <div
              key={card.number}
              className="group relative flex flex-col justify-between rounded-xl border border-[#2D3339] bg-[#121517] p-8 transition-all duration-300 hover:border-[#76C043]/50 hover:bg-[#121517]/90 hover:shadow-[0_12px_32px_rgba(0,0,0,0.5)]"
            >
              {/* Top Row: Big Number & Tag */}
              <div>
                <div className="flex items-center justify-between pb-6 border-b border-[#2D3339]">
                  <span className="font-mono text-3xl font-black text-[#76C043]/90">
                    {card.number}
                  </span>
                  <span className="font-mono text-[11px] uppercase tracking-widest text-[#9CA3AF]">
                    {card.subtitle}
                  </span>
                </div>

                <h3 className="mt-6 text-xl sm:text-2xl font-bold tracking-tight text-[#F8FAFC] group-hover:text-[#76C043] transition-colors duration-200">
                  {card.title}
                </h3>

                <p className="mt-3.5 text-sm sm:text-base leading-relaxed text-[#9CA3AF]">
                  {card.description}
                </p>
              </div>

              {/* Bottom Remedy Note */}
              <div className="mt-8 pt-6 border-t border-[#2D3339]/60">
                <p className="text-xs font-mono font-semibold text-[#76C043]">
                  {card.remedy}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default ResistanceSection;
