"use client";

import React from "react";
import { SectionLabel } from "../ui/SectionLabel";
import { PrimaryButton } from "../ui/PrimaryButton";
import { SecondaryButton } from "../ui/SecondaryButton";
import { FadeIn, StaggerContainer, StaggerItem } from "../ui/MotionWrapper";

export interface PricingTier {
  id: string;
  name: string;
  badge?: string;
  priceFormatted: string;
  billingPeriod: string;
  description: string;
  features: string[];
  isPopular?: boolean;
  ctaText: string;
}

export const DEFAULT_TIERS: PricingTier[] = [
  {
    id: "starter",
    name: "STARTER",
    priceFormatted: "LKR 5,500",
    billingPeriod: "/ month",
    description: "For independent lifters seeking top-tier facility and equipment access.",
    features: [
      "Full Open Arena & Iron access",
      "Standard locker & shower facilities",
      "Initial movement screening",
      "Access to community workshops",
      "Fit Me mobile workout logging",
    ],
    isPopular: false,
    ctaText: "Start Starter Plan",
  },
  {
    id: "transform",
    name: "TRANSFORM",
    badge: "MOST POPULAR",
    priceFormatted: "LKR 9,500",
    billingPeriod: "/ month",
    description: "Our signature coaching & periodized training pathway for committed progress.",
    features: [
      "Everything in Starter plan",
      "Periodized training program design",
      "Bi-weekly coach check-ins & metric tracking",
      "Nutrition calibration & macro guidelines",
      "Priority equipment booking during peak hours",
      "Direct WhatsApp coach support",
    ],
    isPopular: true,
    ctaText: "Start Your Transformation",
  },
  {
    id: "elite",
    name: "ELITE",
    badge: "1-ON-1 COACHING",
    priceFormatted: "LKR 18,500",
    billingPeriod: "/ month",
    description: "High-touch personal training with bespoke daily biometric optimization.",
    features: [
      "Everything in Transform plan",
      "8 Dedicated 1-on-1 private coaching sessions",
      "Comprehensive monthly body composition scans",
      "Custom supplement & recovery protocols",
      "Tailored lifestyle & sleep architecture",
      "24/7 dedicated coach line",
    ],
    isPopular: false,
    ctaText: "Join Elite Mentorship",
  },
];

interface MembershipSectionProps {
  tiers?: PricingTier[];
}

export function MembershipSection({ tiers = DEFAULT_TIERS }: MembershipSectionProps) {
  return (
    <section
      id="membership"
      className="relative w-full bg-[#0E1012] py-24 sm:py-32 border-t border-[#2D3339]/50"
    >
      <div className="max-w-[1750px] mx-auto px-4 sm:px-8 lg:px-14 xl:px-20">
        {/* Header */}
        <FadeIn direction="up" distance={20} className="flex flex-col items-start max-w-3xl">
          <SectionLabel label="INVEST IN EXCELLENCE" />

          <h2 className="mt-5 text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#F8FAFC] uppercase">
            Find Your <br />
            <span className="text-[#76C043]">Fit</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-[#9CA3AF] max-w-2xl">
            Transparent, zero-contract memberships built around genuine accountability.
            Choose the tier that matches your training ambition.
          </p>
        </FadeIn>

        {/* Pricing Cards with Staggered Motion */}
        <StaggerContainer
          staggerDelay={0.12}
          className="mt-14 sm:mt-20 grid grid-cols-1 lg:grid-cols-3 gap-8 items-stretch"
        >
          {tiers.map((tier) => (
            <StaggerItem key={tier.id} className="h-full">
              <div
                className={`relative flex h-full flex-col justify-between rounded-2xl border p-8 sm:p-10 transition-all duration-300 ${
                  tier.isPopular
                    ? "bg-[#121517] border-[#76C043] shadow-[0_16px_50px_rgba(118,192,67,0.18)] scale-100 lg:-translate-y-2.5"
                    : "bg-[#0B0D0E] border-[#2D3339] card-hover-border hover:bg-[#121517]/80"
                }`}
              >
                {/* Popular Badge */}
                {tier.badge && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="rounded-full bg-[#76C043] px-3.5 py-1 text-[10px] font-mono font-black uppercase tracking-widest text-[#0B0D0E] shadow-[0_0_15px_rgba(118,192,67,0.5)]">
                      {tier.badge}
                    </span>
                  </div>
                )}

                <div>
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold tracking-tight text-[#F8FAFC]">
                      {tier.name}
                    </h3>
                  </div>

                  {/* Price Display */}
                  <div className="mt-6 flex items-baseline gap-2">
                    <span className="text-4xl sm:text-5xl font-black text-[#F8FAFC] tracking-tight">
                      {tier.priceFormatted}
                    </span>
                    <span className="text-sm font-mono text-[#9CA3AF]">
                      {tier.billingPeriod}
                    </span>
                  </div>

                  <p className="mt-4 text-sm leading-relaxed text-[#9CA3AF]">
                    {tier.description}
                  </p>

                  {/* Features List */}
                  <ul className="mt-8 space-y-3.5 border-t border-[#2D3339] pt-8">
                    {tier.features.map((feat, fIdx) => (
                      <li key={fIdx} className="flex items-start gap-3 text-sm text-[#F8FAFC]/90">
                        <svg
                          className="w-5 h-5 shrink-0 text-[#76C043] mt-0.5"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Bottom CTA */}
                <div className="mt-10 pt-6 border-t border-[#2D3339]/60">
                  {tier.isPopular ? (
                    <PrimaryButton
                      href="tel:0707627878"
                      fullWidth
                      size="md"
                    >
                      Start Your Transformation
                    </PrimaryButton>
                  ) : (
                    <SecondaryButton
                      href="tel:0707627878"
                      fullWidth
                      size="md"
                    >
                      {tier.ctaText}
                    </SecondaryButton>
                  )}
                  <p className="text-center text-[11px] font-mono text-[#9CA3AF] mt-3">
                    Call 070 762 7878 or visit facility to enroll
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

export default MembershipSection;
