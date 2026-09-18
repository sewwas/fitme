import React from "react";
import { FitMeHeader } from "@/components/fitme/FitMeHeader";
import { HeroSection } from "@/components/fitme/HeroSection";
import { ResistanceSection } from "@/components/fitme/ResistanceSection";
import { MethodSection } from "@/components/fitme/MethodSection";
import { TransformationSection } from "@/components/fitme/TransformationSection";
import { ProgramsSection } from "@/components/fitme/ProgramsSection";
import { ArenaSection } from "@/components/fitme/ArenaSection";
import { ResultsSection } from "@/components/fitme/ResultsSection";
import { CoachesSection } from "@/components/fitme/CoachesSection";
import { MembershipSection } from "@/components/fitme/MembershipSection";
import { FAQSection } from "@/components/fitme/FAQSection";
import { FinalCTA } from "@/components/fitme/FinalCTA";
import { FitMeFooter } from "@/components/fitme/FitMeFooter";

export default function HomePage() {
  return (
    <div className="relative min-h-screen bg-[#0B0D0E] text-[#F8FAFC]">
      {/* 1. Fixed Header */}
      <FitMeHeader />

      <main>
        {/* 2. Chapter 01: Hero - The Choice */}
        <HeroSection />

        {/* 3. Chapter 02: The Resistance */}
        <ResistanceSection />

        {/* 4. The Fit Me Method */}
        <MethodSection />

        {/* 5. Chapter 03: Transformation */}
        <TransformationSection />

        {/* 6. Programs: Choose Your Path */}
        <ProgramsSection />

        {/* 7. Chapter 04: The Arena */}
        <ArenaSection />

        {/* 8. Real Results */}
        <ResultsSection />

        {/* 9. Coaches */}
        <CoachesSection />

        {/* 10. Membership */}
        <MembershipSection />

        {/* 11. FAQ */}
        <FAQSection />

        {/* 12. Final CTA */}
        <FinalCTA />
      </main>

      {/* 13. Footer */}
      <FitMeFooter />
    </div>
  );
}
