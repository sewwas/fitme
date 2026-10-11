"use client";

import React from "react";
import { FitMeHeader } from "@/components/fitme/FitMeHeader";
import { HeroSection } from "@/components/fitme/HeroSection";
import { WhyFitMeSection } from "@/components/fitme/WhyFitMeSection";
import { ProgramsSection } from "@/components/fitme/ProgramsSection";
import { TrackProgressSection } from "@/components/fitme/TrackProgressSection";
import { ChoosePathSection } from "@/components/fitme/ChoosePathSection";
import { FacilitiesSection } from "@/components/fitme/FacilitiesSection";
import { TestimonialsSection } from "@/components/fitme/TestimonialsSection";
import { TrainersSection } from "@/components/fitme/TrainersSection";
import { MembershipSection } from "@/components/fitme/MembershipSection";
import { FAQSection } from "@/components/fitme/FAQSection";
import { FinalCTA } from "@/components/fitme/FinalCTA";
import { FitMeFooter } from "@/components/fitme/FitMeFooter";

export default function HomePage() {
  return (
    <div className="relative min-h-screen bg-[#070809] text-[#F8FAFC]">
      {/* 1. Header Navigation */}
      <FitMeHeader />

      <main>
        {/* 2. Hero Section: Transform Your Journey */}
        <HeroSection />

        {/* 3. Why Fit Me: More Than A Gym / It's A Lifestyle */}
        <WhyFitMeSection />

        {/* 4. Training Programs: Build The Best Version Of You */}
        <ProgramsSection />

        {/* 5. Track Your Progress: See Real Results (HUD + Phone Mockup) */}
        <TrackProgressSection />

        {/* 6. Choose Your Path: Your Goals. Our Support. */}
        <ChoosePathSection />

        {/* 7. Our Facilities: World-Class Gym Experience */}
        <FacilitiesSection />

        {/* 8. Member Testimonials: Real Stories */}
        <TestimonialsSection />

        {/* 9. Meet Our Trainers: Expert Guidance. Real Support. */}
        <TrainersSection />

        {/* 10. Membership Plans: Flexible Plans For Every Goal */}
        <MembershipSection />

        {/* 11. Frequently Asked Questions */}
        <FAQSection />

        {/* 12. Final CTA: Take The First Step */}
        <FinalCTA />
      </main>

      {/* 13. Footer */}
      <FitMeFooter />
    </div>
  );
}
