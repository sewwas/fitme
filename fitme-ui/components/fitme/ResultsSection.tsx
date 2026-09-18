"use client";

import React from "react";
import { SectionLabel } from "../ui/SectionLabel";
import { FadeIn, StaggerContainer, StaggerItem } from "../ui/MotionWrapper";

interface MemberStory {
  quote: string;
  name: string;
  role: string;
  timeframe: string;
  focus: string;
}

const MEMBER_STORIES: MemberStory[] = [
  {
    quote:
      "Joining Fit Me removed all the guesswork. For the first time in years, I train with a clear daily plan. My chronic lower back discomfort disappeared once we fixed my deadlift hinge mechanics.",
    name: "Kasun Ranasinghe",
    role: "Local Business Owner, Pitigala",
    timeframe: "Member for 9 months",
    focus: "Strength & Postural Health",
  },
  {
    quote:
      "The coaches here hold you to high standards while keeping the environment respectful and calm. I never felt self-conscious, even when starting out as a complete novice.",
    name: "Dilini Senanayake",
    role: "Software Professional",
    timeframe: "Member for 6 months",
    focus: "Hypertrophy & Conditioning",
  },
  {
    quote:
      "The emphasis on logging every lift and bi-weekly check-ins kept me accountable when work was stressful. Sustainable habits, genuine equipment, and passionate guidance.",
    name: "Sahan Jayawardena",
    role: "Civil Engineer",
    timeframe: "Member for 1 year",
    focus: "Athletic Conditioning",
  },
];

export function ResultsSection() {
  return (
    <section
      id="results"
      className="relative w-full bg-[#0E1012] py-24 sm:py-32 border-t border-[#2D3339]/50"
    >
      <div className="max-w-[1750px] mx-auto px-4 sm:px-8 lg:px-14 xl:px-20">
        {/* Header */}
        <FadeIn direction="up" distance={20} className="flex flex-col items-start max-w-3xl">
          <SectionLabel label="VERIFIED TESTIMONIALS" />

          <h2 className="mt-5 text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#F8FAFC] uppercase">
            Real People. <br />
            <span className="text-[#76C043]">Real Progress.</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-[#9CA3AF] max-w-2xl">
            Real discipline produces real adaptation. Here is what members of the
            Pitigala training community experience when they commit to the
            method.
          </p>
        </FadeIn>

        {/* Testimonial Cards with Motion Stagger */}
        <StaggerContainer
          staggerDelay={0.12}
          className="mt-14 sm:mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8"
        >
          {MEMBER_STORIES.map((story, idx) => (
            <StaggerItem key={idx}>
              <div className="flex h-full flex-col justify-between rounded-xl border border-[#2D3339] bg-[#121517] p-8 card-hover-border">
                <div>
                  {/* Quote Icon */}
                  <div className="text-[#76C043] font-serif text-4xl leading-none mb-4">
                    “
                  </div>
                  <p className="text-sm sm:text-base leading-relaxed text-[#F8FAFC]/90">
                    {story.quote}
                  </p>
                </div>

                <div className="mt-8 pt-6 border-t border-[#2D3339]/70">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-bold text-sm text-[#F8FAFC]">
                        {story.name}
                      </h4>
                      <p className="text-xs text-[#9CA3AF] mt-0.5">
                        {story.role}
                      </p>
                    </div>
                    <span className="inline-flex items-center gap-1 rounded bg-[#76C043]/10 border border-[#76C043]/30 px-2 py-0.5 text-[10px] font-mono text-[#76C043]">
                      Verified
                    </span>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-[11px] font-mono text-[#9CA3AF]">
                    <span>{story.timeframe}</span>
                    <span className="text-[#76C043]">{story.focus}</span>
                  </div>
                </div>
              </div>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  );
}

export default ResultsSection;
