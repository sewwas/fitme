"use client";

import React from "react";
import Link from "next/link";

const WHY_CARDS = [
  {
    icon: (
      <svg className="w-5 h-5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
    title: "Personalized Training",
    description: "Programs designed for your goals, fitness level and lifestyle.",
  },
  {
    icon: (
      <svg className="w-5 h-5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
    title: "Expert Coaches",
    description: "Certified trainers with real experience and support.",
  },
  {
    icon: (
      <svg className="w-5 h-5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
    title: "Modern Facilities",
    description: "Clean, safe and well-equipped environment.",
  },
  {
    icon: (
      <svg className="w-5 h-5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
    title: "Supportive Community",
    description: "Workout together, grow together.",
  },
];

export function WhyFitMeSection() {
  return (
    <section className="relative w-full bg-[#08090A] py-20 lg:py-28 border-t border-white/5 overflow-hidden">
      <div className="max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          {/* Left Column */}
          <div className="lg:col-span-5">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#76C043] mb-3">
              Why Fit Me
            </p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black uppercase tracking-tight text-white leading-[1.08]">
              More Than A Gym <br />
              <span className="text-[#76C043]">It&apos;s A Lifestyle</span>
            </h2>
            <p className="mt-5 text-sm sm:text-base text-[#9CA3AF] leading-relaxed">
              At Fit Me, we believe fitness is not just about looking good, it&apos;s about feeling strong,
              confident and living a healthier, happier life. We provide the right environment, expert
              support, and personalized programs to help you reach your goals.
            </p>
            <div className="mt-8">
              <Link
                href="#facilities"
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full border border-[#76C043]/60 bg-[#0E1113] hover:bg-[#76C043]/10 text-white hover:text-[#76C043] text-xs font-bold uppercase tracking-wider transition-all"
              >
                <span>Our Story</span>
                <svg className="w-3.5 h-3.5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Right Column: 4 Cards Grid */}
          <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-5">
            {WHY_CARDS.map((item) => (
              <div
                key={item.title}
                className="p-6 rounded-2xl bg-[#0D1012] border border-white/5 hover:border-[#76C043]/40 transition-all hover:-translate-y-1 group"
              >
                <div className="h-11 w-11 rounded-full bg-[#141A14] border border-[#76C043]/30 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                  {item.icon}
                </div>
                <h3 className="text-base font-bold text-white mb-2 group-hover:text-[#76C043] transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-[#9CA3AF] leading-relaxed">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default WhyFitMeSection;
