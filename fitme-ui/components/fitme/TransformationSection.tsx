"use client";

import React, { useState } from "react";
import Link from "next/link";
import { SectionLabel } from "../ui/SectionLabel";

interface MilestoneData {
  day: string;
  phase: string;
  consistency: string;
  sessionsCompleted: number;
  strengthProgression: string;
  milestone: string;
  notes: string;
  stats: {
    benchBaseline: string;
    squatBaseline: string;
    vo2OrRecovery: string;
  };
}

const TRANSFORMATION_TIMELINE: MilestoneData[] = [
  {
    day: "DAY 01",
    phase: "Baseline Assessment",
    consistency: "Initial Setup",
    sessionsCompleted: 1,
    strengthProgression: "Baseline Establish (100%)",
    milestone: "Movement screen, joint mobility audit & biometric capture",
    notes:
      "Established foundational barbell mechanics, baseline work capacity, and calibrated daily macro targets.",
    stats: {
      benchBaseline: "Baseline (60 kg)",
      squatBaseline: "Baseline (80 kg)",
      vo2OrRecovery: "Resting HR: 74 bpm",
    },
  },
  {
    day: "DAY 30",
    phase: "Neuromuscular Adaptation",
    consistency: "94% Attendance",
    sessionsCompleted: 16,
    strengthProgression: "+12% Compound Volume",
    milestone: "Form stability locked across compound lifts",
    notes:
      "Consistent 4x weekly frequency. Muscle soreness reduced significantly; sleep recovery score normalized.",
    stats: {
      benchBaseline: "67.5 kg (+12.5%)",
      squatBaseline: "92.5 kg (+15.6%)",
      vo2OrRecovery: "Resting HR: 69 bpm",
    },
  },
  {
    day: "DAY 90",
    phase: "Hypertrophy & Work Capacity",
    consistency: "96% Attendance",
    sessionsCompleted: 48,
    strengthProgression: "+28% Compound Strength",
    milestone: "First major strength wave peak achieved",
    notes:
      "Completed 12-week progressive overload block. Notable density in postural muscles and noticeable stamina during high-rep accessory sets.",
    stats: {
      benchBaseline: "77.5 kg (+29.1%)",
      squatBaseline: "110.0 kg (+37.5%)",
      vo2OrRecovery: "Resting HR: 63 bpm",
    },
  },
  {
    day: "DAY 180",
    phase: "Sustainable Athletic Mastery",
    consistency: "95% Attendance",
    sessionsCompleted: 98,
    strengthProgression: "+42% Over Baseline",
    milestone: "Full habit integration; self-regulated lifting autonomy",
    notes:
      "Lifting technique is automatic and confident. Nutrition is habitual rather than restrictive. Measurable endurance and resilience.",
    stats: {
      benchBaseline: "87.5 kg (+45.8%)",
      squatBaseline: "125.0 kg (+56.2%)",
      vo2OrRecovery: "Resting HR: 58 bpm",
    },
  },
];

export function TransformationSection() {
  const [selectedIndex, setSelectedIndex] = useState(2); // Default to Day 90
  const activeData = TRANSFORMATION_TIMELINE[selectedIndex];

  return (
    <section
      id="transformation"
      className="relative w-full bg-[#0B0D0E] py-24 sm:py-32 border-t border-[#2D3339]/50"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col items-start max-w-3xl">
          <SectionLabel chapter="CHAPTER 03" label="TRANSFORMATION" />

          <h2 className="mt-5 text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#F8FAFC] uppercase">
            Your Progress. <br />
            <span className="text-[#76C043]">Your Journey.</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-[#9CA3AF] max-w-2xl">
            We do not promise synthetic overnight illusions. Real transformation
            is the product of consistent training sessions, progressive loads,
            and monitored biomarkers over time.
          </p>
        </div>

        {/* Interactive Milestone Navigation */}
        <div className="mt-14 sm:mt-20">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 p-2 rounded-2xl border border-[#2D3339] bg-[#121517]">
            {TRANSFORMATION_TIMELINE.map((item, idx) => {
              const isSelected = selectedIndex === idx;
              return (
                <button
                  key={item.day}
                  type="button"
                  onClick={() => setSelectedIndex(idx)}
                  className={`flex flex-col items-center sm:items-start p-4 sm:p-5 rounded-xl transition-all duration-200 text-left ${
                    isSelected
                      ? "bg-[#0B0D0E] border border-[#76C043]/50 shadow-[0_0_20px_rgba(118,192,67,0.15)]"
                      : "hover:bg-[#0B0D0E]/50 border border-transparent"
                  }`}
                >
                  <span
                    className={`font-mono text-xs uppercase tracking-widest ${
                      isSelected ? "text-[#76C043] font-bold" : "text-[#9CA3AF]"
                    }`}
                  >
                    Phase 0{idx + 1}
                  </span>
                  <span
                    className={`mt-1 text-base sm:text-xl font-black tracking-tight ${
                      isSelected ? "text-[#F8FAFC]" : "text-[#9CA3AF]"
                    }`}
                  >
                    {item.day}
                  </span>
                  <span className="hidden sm:inline text-xs text-[#9CA3AF] mt-1 truncate w-full">
                    {item.phase}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Detailed Transformation Panel for Selected Day */}
          <div className="mt-6 rounded-2xl border border-[#2D3339] bg-[#121517] p-6 sm:p-10 shadow-2xl">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
              {/* Left Column: Core Metrics */}
              <div className="lg:col-span-7 flex flex-col justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="font-mono text-sm font-bold text-[#76C043] bg-[#0B0D0E] px-3 py-1 rounded border border-[#2D3339]">
                      {activeData.day}
                    </span>
                    <span className="text-sm font-semibold uppercase tracking-wider text-[#9CA3AF]">
                      {activeData.phase}
                    </span>
                  </div>

                  <h3 className="mt-4 text-2xl sm:text-3xl font-bold tracking-tight text-[#F8FAFC]">
                    Milestone Achievement
                  </h3>
                  <p className="mt-2 text-base text-[#76C043] font-medium">
                    {activeData.milestone}
                  </p>

                  <div className="mt-6 p-5 rounded-xl bg-[#0B0D0E] border border-[#2D3339]">
                    <span className="text-xs font-mono uppercase tracking-widest text-[#9CA3AF]">
                      Coach Progress Notes
                    </span>
                    <p className="mt-2 text-sm sm:text-base leading-relaxed text-[#F8FAFC]/90">
                      &ldquo;{activeData.notes}&rdquo;
                    </p>
                  </div>
                </div>

                {/* Progress link CTA */}
                <div className="mt-8 pt-6 border-t border-[#2D3339] flex items-center justify-between">
                  <Link
                    href="#membership"
                    className="inline-flex items-center gap-2 text-sm font-bold tracking-wider uppercase text-[#76C043] hover:text-[#88dc4f] transition-colors"
                  >
                    <span>VIEW YOUR PROGRESS</span>
                    <span className="text-lg">→</span>
                  </Link>

                  <span className="text-xs font-mono text-[#9CA3AF]">
                    Audited Training Protocol
                  </span>
                </div>
              </div>

              {/* Right Column: Quantitative Telemetry Cards */}
              <div className="lg:col-span-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4">
                <div className="rounded-xl bg-[#0B0D0E] border border-[#2D3339] p-5">
                  <span className="text-xs font-mono uppercase tracking-widest text-[#9CA3AF]">
                    Training Consistency
                  </span>
                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="text-2xl font-black text-[#F8FAFC]">
                      {activeData.consistency}
                    </span>
                    <span className="text-xs font-mono text-[#76C043]">
                      Logged Verified
                    </span>
                  </div>
                </div>

                <div className="rounded-xl bg-[#0B0D0E] border border-[#2D3339] p-5">
                  <span className="text-xs font-mono uppercase tracking-widest text-[#9CA3AF]">
                    Sessions Completed
                  </span>
                  <div className="mt-2 flex items-baseline justify-between">
                    <span className="text-2xl font-black text-[#76C043]">
                      {activeData.sessionsCompleted}{" "}
                      <span className="text-xs text-[#9CA3AF] font-normal">
                        Workouts
                      </span>
                    </span>
                    <span className="text-xs font-mono text-[#9CA3AF]">
                      On Track
                    </span>
                  </div>
                </div>

                <div className="rounded-xl bg-[#0B0D0E] border border-[#2D3339] p-5 sm:col-span-2 lg:col-span-1">
                  <span className="text-xs font-mono uppercase tracking-widest text-[#9CA3AF]">
                    Strength & Volume Progression
                  </span>
                  <p className="mt-2 text-lg font-bold text-[#F8FAFC]">
                    {activeData.strengthProgression}
                  </p>

                  <div className="mt-3 grid grid-cols-3 gap-2 pt-3 border-t border-[#2D3339]/60 text-xs font-mono">
                    <div>
                      <span className="text-[#9CA3AF] block">Bench</span>
                      <span className="text-[#F8FAFC] font-semibold">
                        {activeData.stats.benchBaseline}
                      </span>
                    </div>
                    <div>
                      <span className="text-[#9CA3AF] block">Squat</span>
                      <span className="text-[#F8FAFC] font-semibold">
                        {activeData.stats.squatBaseline}
                      </span>
                    </div>
                    <div>
                      <span className="text-[#9CA3AF] block">Recovery</span>
                      <span className="text-[#76C043] font-semibold">
                        {activeData.stats.vo2OrRecovery}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default TransformationSection;
