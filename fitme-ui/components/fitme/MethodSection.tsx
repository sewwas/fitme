"use client";

import React from "react";
import { SectionLabel } from "../ui/SectionLabel";
import { FadeIn, StaggerContainer, StaggerItem } from "../ui/MotionWrapper";

const METHOD_STEPS = [
  {
    step: "01",
    name: "ASSESS",
    tagline: "Baseline Analysis",
    description: "Understand your starting point through mobility checks, body composition, and training history.",
  },
  {
    step: "02",
    name: "PLAN",
    tagline: "Custom Architecture",
    description: "Build a structured periodized program aligned with your schedule, recovery capacity, and targets.",
  },
  {
    step: "03",
    name: "TRAIN",
    tagline: "Focused Execution",
    description: "Execute with precise technique under true coach guidance, high-grade equipment, and progressive load.",
  },
  {
    step: "04",
    name: "FUEL",
    tagline: "Practical Nutrition",
    description: "Build sustainable dietary habits and macronutrient targets designed for performance and recovery.",
  },
  {
    step: "05",
    name: "TRACK",
    tagline: "Measure & Adapt",
    description: "Quantify strength logs, physical changes, and consistency metrics to continuously refine your protocol.",
  },
];

export function MethodSection() {
  return (
    <section
      id="method"
      className="relative w-full bg-[#0E1012] py-24 sm:py-32 border-t border-[#2D3339]/50"
    >
      <div className="max-w-[1750px] mx-auto px-4 sm:px-8 lg:px-14 xl:px-20">
        {/* Header Block */}
        <FadeIn direction="up" distance={24} className="flex flex-col items-start max-w-3xl">
          <SectionLabel label="THE FIT ME METHOD" />

          <h2 className="mt-5 text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#F8FAFC] uppercase">
            A Better Way <br />
            <span className="text-[#76C043]">To Train</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-[#9CA3AF] max-w-2xl">
            A continuous, calibrated 5-pillar system built to turn ambition into
            predictable, measurable physical adaptation.
          </p>
        </FadeIn>

        {/* Timeline Layout */}
        <div className="mt-16 sm:mt-24">
          {/* Desktop: Horizontal Timeline with Staggered Steps */}
          <div className="hidden lg:block relative">
            {/* Horizontal connecting line with animated gradient glow */}
            <div className="absolute top-7 left-10 right-10 h-0.5 bg-gradient-to-r from-[#76C043]/30 via-[#76C043]/80 to-[#76C043]/30 z-0" />

            <StaggerContainer
              staggerDelay={0.1}
              className="grid grid-cols-5 gap-4 relative z-10"
            >
              {METHOD_STEPS.map((step) => (
                <StaggerItem
                  key={step.step}
                  distance={24}
                  className="flex flex-col group"
                >
                  {/* Step Circle Marker */}
                  <div className="flex items-center gap-3 mb-6">
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-[#2D3339] bg-[#121517] font-mono text-lg font-bold text-[#76C043] transition-all duration-300 group-hover:border-[#76C043] group-hover:scale-110 group-hover:shadow-[0_0_24px_rgba(118,192,67,0.3)]">
                      {step.step}
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="flex-1 rounded-xl border border-[#2D3339] bg-[#121517] p-6 card-hover-border">
                    <span className="text-[10px] font-mono uppercase tracking-widest text-[#76C043]">
                      {step.tagline}
                    </span>
                    <h3 className="mt-1 text-xl font-bold tracking-tight text-[#F8FAFC]">
                      {step.name}
                    </h3>
                    <p className="mt-3 text-xs sm:text-sm leading-relaxed text-[#9CA3AF]">
                      {step.description}
                    </p>
                  </div>
                </StaggerItem>
              ))}
            </StaggerContainer>
          </div>

          {/* Mobile & Tablet: Vertical Timeline */}
          <div className="lg:hidden relative border-l-2 border-[#2D3339] ml-4 pl-6 space-y-8">
            {METHOD_STEPS.map((step) => (
              <FadeIn key={step.step} direction="left" distance={16} className="relative group">
                {/* Node on vertical line */}
                <div className="absolute -left-[35px] top-4 flex h-8 w-8 items-center justify-center rounded-lg border border-[#76C043] bg-[#0B0D0E] font-mono text-xs font-bold text-[#76C043] shadow-[0_0_12px_rgba(118,192,67,0.3)]">
                  {step.step}
                </div>

                {/* Mobile Card */}
                <div className="rounded-xl border border-[#2D3339] bg-[#121517] p-6">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-[#76C043]">
                    {step.tagline}
                  </span>
                  <h3 className="mt-1 text-lg font-bold tracking-tight text-[#F8FAFC]">
                    {step.name}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#9CA3AF]">
                    {step.description}
                  </p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default MethodSection;
