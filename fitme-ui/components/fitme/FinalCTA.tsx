"use client";

import React from "react";
import Image from "next/image";
import { PrimaryButton } from "../ui/PrimaryButton";
import { SecondaryButton } from "../ui/SecondaryButton";
import { SectionLabel } from "../ui/SectionLabel";
import { FadeIn } from "../ui/MotionWrapper";

export function FinalCTA() {
  return (
    <section className="relative w-full bg-[#0B0D0E] py-28 sm:py-36 overflow-hidden border-t border-[#2D3339]/60">
      {/* Background Ambience with Subtle Cover Image */}
      <div className="absolute inset-0 z-0 opacity-20">
        <Image
          src="/images/fitme-official-cover.jpg"
          alt="Fit Me Arena background"
          fill
          className="object-cover object-center filter grayscale contrast-125"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0B0D0E] via-[#0B0D0E]/80 to-[#0B0D0E]" />
      </div>

      {/* Radial Glow with Breathing Pulse */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-[#76C043]/15 blur-[140px] pointer-events-none animate-ambient-glow" />

      <div className="relative z-10 max-w-[1750px] mx-auto px-4 sm:px-8 lg:px-14 xl:px-20 text-center">
        <FadeIn direction="up" distance={20} className="max-w-4xl mx-auto">
          <div className="inline-block mb-6">
            <SectionLabel label="JOIN THE DISCIPLINE" />
          </div>

          <h2 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-[#F8FAFC] uppercase leading-[1.05]">
            Your Day One <br />
            <span className="text-[#76C043] drop-shadow-[0_0_35px_rgba(118,192,67,0.4)]">
              Starts Here.
            </span>
          </h2>

          <p className="mt-6 text-base sm:text-xl text-[#9CA3AF] max-w-xl mx-auto font-medium">
            Train with purpose. Move with confidence. Track your progress.
          </p>

          {/* Buttons */}
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
            <div className="relative w-full sm:w-auto group">
              <div className="absolute -inset-0.5 rounded-lg bg-[#76C043]/30 blur opacity-75 group-hover:opacity-100 transition duration-300" />
              <PrimaryButton
                href="#membership"
                size="lg"
                fullWidth
                className="sm:w-auto relative"
              >
                Start Your Transformation
              </PrimaryButton>
            </div>

            <SecondaryButton
              href="/dashboard/member/"
              size="lg"
              fullWidth
              className="sm:w-auto"
            >
              Member Login
            </SecondaryButton>
          </div>

          {/* Small Location Anchor */}
          <p className="mt-8 text-xs font-mono text-[#9CA3AF]">
            Fit Me Arena • New Town, Elpitiya Road, Pitigala, 80420
          </p>
        </FadeIn>
      </div>
    </section>
  );
}

export default FinalCTA;
