"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "motion/react";

export function FinalCTA() {
  return (
    <section className="relative w-full bg-[#060708] py-16 sm:py-20 border-t border-white/5 overflow-hidden">
      {/* Background with Dark Gym Wallpaper */}
      <div className="absolute inset-0 z-0 opacity-40">
        <Image
          src="/images/fitme-gym-power-zone.jpeg"
          alt="Fit Me Arena - Start Your Transformation"
          fill
          sizes="100vw"
          className="object-cover object-center"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[#060708] via-[#060708]/85 to-[#060708]" />
      </div>

      {/* Ambient Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-64 w-96 rounded-full bg-[#76C043]/15 blur-[100px] pointer-events-none" />

      <div className="relative z-10 max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-8 p-8 sm:p-12 rounded-3xl bg-[#0B0D0E]/80 backdrop-blur-md border border-[#76C043]/30 shadow-[0_0_50px_rgba(0,0,0,0.8)]">
          <div className="max-w-2xl text-center lg:text-left">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#76C043] mb-2">
              Your Journey Starts Today
            </p>
            <h2 className="text-2xl sm:text-4xl lg:text-5xl font-black uppercase tracking-tight text-white leading-tight">
              Take The <span className="text-[#76C043]">First Step</span>
            </h2>
            <p className="mt-3 text-sm sm:text-base text-[#9CA3AF]">
              Join Fit Me and become the strongest, healthiest and happiest version of yourself.
            </p>
          </div>

          <div className="flex-shrink-0">
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
      </div>
    </section>
  );
}

export default FinalCTA;
