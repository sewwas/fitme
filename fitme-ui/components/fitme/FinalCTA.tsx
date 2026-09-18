import React from "react";
import Image from "next/image";
import { PrimaryButton } from "../ui/PrimaryButton";
import { SecondaryButton } from "../ui/SecondaryButton";
import { SectionLabel } from "../ui/SectionLabel";

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

      {/* Radial Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full bg-[#76C043]/10 blur-[120px] pointer-events-none" />

      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-block mb-6">
          <SectionLabel label="JOIN THE DISCIPLINE" />
        </div>

        <h2 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-[#F8FAFC] uppercase leading-[1.05]">
          Your Day One <br />
          <span className="text-[#76C043] drop-shadow-[0_0_30px_rgba(118,192,67,0.3)]">
            Starts Here.
          </span>
        </h2>

        <p className="mt-6 text-base sm:text-xl text-[#9CA3AF] max-w-xl mx-auto font-medium">
          Train with purpose. Move with confidence. Track your progress.
        </p>

        {/* Buttons */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
          <PrimaryButton
            href="#membership"
            size="lg"
            fullWidth
            className="sm:w-auto"
          >
            Start Your Transformation
          </PrimaryButton>

          <SecondaryButton
            href="http://127.0.0.1:8000/dashboard/member/"
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
      </div>
    </section>
  );
}

export default FinalCTA;
