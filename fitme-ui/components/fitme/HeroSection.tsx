import React from "react";
import Image from "next/image";
import { PrimaryButton } from "../ui/PrimaryButton";
import { SecondaryButton } from "../ui/SecondaryButton";
import { SectionLabel } from "../ui/SectionLabel";

export function HeroSection() {
  return (
    <section
      id="hero"
      className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-[#0B0D0E] pt-24 pb-16 lg:py-0"
    >
      {/* Hero Background Image with Cinematic Treatment */}
      <div className="absolute inset-0 z-0">
        <Image
          src="https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=2070&auto=format&fit=crop"
          alt="Athlete training with purpose in high-end moody gym setting"
          fill
          priority
          sizes="100vw"
          className="object-cover object-center lg:object-[70%_35%] scale-102 transition-transform duration-1000 ease-out"
        />

        {/* Multi-layer Dark Gradient for Flawless Readability */}
        {/* Horizontal gradient: deep black on left, clear on right for desktop */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#0B0D0E] via-[#0B0D0E]/85 to-[#0B0D0E]/30 hidden lg:block" />
        {/* Vertical gradient: for mobile & overall vertical grounding */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#0B0D0E] via-[#0B0D0E]/80 to-[#0B0D0E]/40 lg:bg-gradient-to-t lg:from-[#0B0D0E] lg:via-transparent lg:to-[#0B0D0E]/60" />

        {/* Subtle Lime Ambient Practical Lighting (controlled, not garish) */}
        <div className="absolute -top-32 left-1/4 h-96 w-96 rounded-full bg-[#76C043]/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 right-1/4 h-80 w-80 rounded-full bg-[#76C043]/5 blur-3xl pointer-events-none" />

        {/* Black Vignette overlay */}
        <div className="absolute inset-0 shadow-[inset_0_0_120px_rgba(11,13,14,0.9)] pointer-events-none" />
      </div>

      {/* Hero Content Container */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-28">
        <div className="max-w-2xl lg:max-w-3xl">
          {/* Chapter 01 Label */}
          <div className="mb-6">
            <SectionLabel chapter="CHAPTER 01" label="THE CHOICE" />
          </div>

          {/* Large Bold Typography */}
          <h1 className="text-5xl sm:text-7xl lg:text-8xl font-black tracking-tighter text-[#F8FAFC] uppercase leading-[0.92]">
            Transform <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#F8FAFC] via-[#F8FAFC] to-[#9CA3AF]">
              Your
            </span>{" "}
            <br />
            <span className="text-[#76C043] drop-shadow-[0_0_35px_rgba(118,192,67,0.25)]">
              Journey
            </span>
          </h1>

          {/* Supporting Copy */}
          <p className="mt-6 sm:mt-8 text-base sm:text-lg lg:text-xl leading-relaxed text-[#9CA3AF] max-w-xl font-normal">
            Train with purpose. Move with confidence. Build a sustainable
            fitness routine with structured training, personal coaching, and
            measurable progress.
          </p>

          {/* CTA Row */}
          <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
            <PrimaryButton href="#membership" size="lg">
              Start Your Transformation
            </PrimaryButton>
            <SecondaryButton href="#programs" size="lg">
              Explore Programs
            </SecondaryButton>
          </div>

          {/* Small Trust Row */}
          <div className="mt-12 sm:mt-16 pt-8 border-t border-[#2D3339]/80 max-w-lg">
            <p className="text-[11px] font-mono font-semibold tracking-widest text-[#9CA3AF] uppercase flex flex-wrap items-center gap-x-3 gap-y-2">
              <span className="text-[#F8FAFC]">COACHING</span>
              <span className="text-[#76C043]">•</span>
              <span className="text-[#F8FAFC]">TRAINING</span>
              <span className="text-[#76C043]">•</span>
              <span className="text-[#F8FAFC]">NUTRITION</span>
              <span className="text-[#76C043]">•</span>
              <span className="text-[#F8FAFC]">PROGRESS TRACKING</span>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HeroSection;
