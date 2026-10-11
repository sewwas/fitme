"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";

export function HeroSection() {
  return (
    <section
      id="hero"
      className="relative min-h-[92vh] w-full flex items-center overflow-hidden bg-[#070809] pt-20"
    >
      {/* ── BACKGROUND: Fit Me Banner with athletes on the right ─────── */}
      <div className="absolute inset-0 z-0">
        <Image
          src="/images/fitme-banner.png"
          alt="Fit Me - Transform Your Journey"
          fill
          priority
          sizes="100vw"
          className="object-cover object-[78%_center] sm:object-right lg:object-[85%_center]"
        />
        {/* Left Dark Gradient Overlay so text is 100% readable and crisp without background ghosting */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#070809] from-40% via-[#070809]/95 via-65% to-transparent w-full lg:w-[72%]" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#070809] via-transparent to-transparent h-40 bottom-0" />
      </div>

      {/* ── Green Ambient Glow Behind Content ────────────────────────── */}
      <div
        className="absolute top-1/4 left-10 h-96 w-96 rounded-full bg-[#76C043]/15 blur-[120px] pointer-events-none z-[1]"
        aria-hidden="true"
      />

      {/* ── MAIN HERO CONTAINER ──────────────────────────────────────── */}
      <div className="relative z-10 w-full max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24 py-12 lg:py-20 flex flex-col justify-between min-h-[calc(92vh-80px)]">
        <div className="max-w-[620px] my-auto">
          {/* ── Kicker: FITNESS · HEALTH · BETTER YOU ── */}
          <div className="mb-4 inline-flex items-center gap-2 text-xs font-bold tracking-[0.25em] text-[#76C043] uppercase">
            <span>Fitness</span>
            <span>·</span>
            <span>Health</span>
            <span>·</span>
            <span>Better You</span>
          </div>

          {/* ── Main Headline: TRANSFORM YOUR JOURNEY ── */}
          <h1 className="font-black italic uppercase leading-[0.88] tracking-tight">
            <span className="block text-[clamp(2.8rem,7vw,5.5rem)] text-white">
              Transform
            </span>
            <span className="block text-[clamp(2.8rem,7vw,5.5rem)] text-white">
              Your
            </span>
            <span className="block text-[clamp(3rem,7.5vw,5.8rem)] text-[#76C043] drop-shadow-[0_0_35px_rgba(118,192,67,0.7)] font-black">
              Journey
            </span>
          </h1>

          {/* ── Subtitle: Train with Purpose & Move with Confidence ── */}
          <p className="mt-5 text-base sm:text-lg text-[#C5CBD3] font-normal max-w-lg leading-relaxed">
            Train with Purpose &amp; Move with Confidence
          </p>

          {/* ── CTA Button: START YOUR JOURNEY -> ── */}
          <div className="mt-8 flex items-center gap-4 flex-wrap">
            <Link
              href="#pricing"
              className="inline-flex items-center gap-2.5 px-8 py-3.5 rounded-full bg-[#76C043] hover:bg-[#85D538] text-black text-sm font-black uppercase tracking-wider shadow-[0_0_30px_rgba(118,192,67,0.45)] transition-all hover:scale-105 active:scale-95"
            >
              <span>Start Your Journey</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>
        </div>

        {/* ── Floating Cursive: Stronger Healthier Happier on right (desktop) ── */}
        <div className="hidden xl:block absolute right-16 top-1/3 text-right pointer-events-none select-none">
          <p className="font-serif italic text-3xl xl:text-4xl text-[#76C043] leading-snug drop-shadow-[0_0_20px_rgba(118,192,67,0.8)]" style={{ fontFamily: 'Georgia, serif' }}>
            Stronger<br />
            Healthier<br />
            Happier
          </p>
        </div>

        {/* ── 3 Feature Badges at Bottom ───────────────────────────── */}
        <div className="mt-12 pt-8 border-t border-white/10 grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-3xl">
          {/* Badge 1: Expert Trainers */}
          <div className="flex items-center gap-3.5">
            <div className="h-10 w-10 rounded-full bg-[#121517] border border-[#76C043]/40 flex items-center justify-center text-[#76C043] shadow-[0_0_12px_rgba(118,192,67,0.2)] flex-shrink-0">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-bold text-white leading-tight">Expert Trainers</p>
              <p className="text-xs text-[#9CA3AF]">Real guidance</p>
            </div>
          </div>

          {/* Badge 2: Modern Equipment */}
          <div className="flex items-center gap-3.5">
            <div className="h-10 w-10 rounded-full bg-[#121517] border border-[#76C043]/40 flex items-center justify-center text-[#76C043] shadow-[0_0_12px_rgba(118,192,67,0.2)] flex-shrink-0">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-bold text-white leading-tight">Modern Equipment</p>
              <p className="text-xs text-[#9CA3AF]">World-class gear</p>
            </div>
          </div>

          {/* Badge 3: Flexible Plans */}
          <div className="flex items-center gap-3.5">
            <div className="h-10 w-10 rounded-full bg-[#121517] border border-[#76C043]/40 flex items-center justify-center text-[#76C043] shadow-[0_0_12px_rgba(118,192,67,0.2)] flex-shrink-0">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-bold text-white leading-tight">Flexible Plans</p>
              <p className="text-xs text-[#9CA3AF]">Fit your schedule</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HeroSection;
