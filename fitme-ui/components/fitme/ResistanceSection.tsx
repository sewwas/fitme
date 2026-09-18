"use client";

import React from "react";
import { SectionLabel } from "../ui/SectionLabel";
import { FadeIn, StaggerContainer, StaggerItem } from "../ui/MotionWrapper";

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
      <div className="max-w-[1750px] mx-auto px-4 sm:px-8 lg:px-14 xl:px-20">
        {/* Header Block */}
        <FadeIn direction="up" distance={20} className="flex flex-col items-start max-w-3xl">
          <SectionLabel chapter="CHAPTER 02" label="THE RESISTANCE" />

          <h2 className="mt-5 text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#F8FAFC] uppercase">
            Why Do Fitness <br />
            <span className="text-[#9CA3AF]">Journeys Stop?</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-[#9CA3AF] font-medium border-l-2 border-[#76C043] pl-4">
            Fitness should not depend on motivation alone.
          </p>
        </FadeIn>

        {/* 3 Clean Resistance Cards with Sequential Scroll Stagger */}
        <StaggerContainer
          staggerDelay={0.12}
          className="mt-14 sm:mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8"
        >
          {RESISTANCE_CARDS.map((card) => (
            <StaggerItem key={card.number} className="h-full">
              <div className="group relative flex h-full flex-col justify-between rounded-xl border border-[#2D3339] bg-[#121517] p-8 card-hover-border">
                {/* Top Row: Big Number & Tag */}
                <div>
                  <div className="flex items-center justify-between pb-6 border-b border-[#2D3339]">
                    <span className="font-mono text-3xl font-black text-[#76C043]/90 group-hover:scale-110 transition-transform duration-300 inline-block">
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
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  );
}

export default ResistanceSection;
