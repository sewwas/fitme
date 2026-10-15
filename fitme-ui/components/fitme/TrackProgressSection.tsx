"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "motion/react";
import { PORTAL_LOGIN_URL } from "./config";

export function TrackProgressSection() {
  return (
    <section className="relative w-full bg-[#08090A] py-20 lg:py-28 border-t border-white/5 overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full bg-[#76C043]/10 blur-[140px] pointer-events-none" />

      <div className="max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">

          {/* Left Column: Athlete image with floating progress glass card */}
          <div className="lg:col-span-5 relative flex justify-center">
            <div className="relative w-full max-w-[360px] h-[440px] rounded-2xl overflow-hidden border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.8)]">
              <Image
                src="/images/arena-coaching.jpg"
                alt="Track Your Progress"
                fill
                sizes="(max-width: 768px) 100vw, 400px"
                className="object-cover object-center"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#08090A] via-transparent to-transparent" />
            </div>

            {/* Floating Glassmorphic Progress HUD */}
            <div className="absolute -bottom-6 -right-2 sm:right-4 w-[240px] rounded-2xl bg-[#0D1012]/95 backdrop-blur-xl border border-[#76C043]/30 p-4 shadow-[0_15px_35px_rgba(0,0,0,0.8)]">
              <p className="text-[11px] font-bold uppercase tracking-wider text-white mb-3 flex items-center justify-between">
                <span>Your Progress</span>
                <span className="text-[#76C043] text-xs">● Active</span>
              </p>
              <div className="flex items-center gap-3 mb-3">
                <div className="relative h-14 w-14 rounded-full border-4 border-[#76C043] flex items-center justify-center shadow-[0_0_15px_rgba(118,192,67,0.35)] flex-shrink-0">
                  <span className="text-sm font-black text-white">78%</span>
                </div>
                <div className="text-xs space-y-1">
                  <p className="text-[#9CA3AF]">Workouts: <span className="text-white font-bold">12/16</span></p>
                  <p className="text-[#9CA3AF]">Calories: <span className="text-white font-bold">3,420</span></p>
                </div>
              </div>
              <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px]">
                <span className="text-[#9CA3AF]">Weight delta</span>
                <span className="text-[#76C043] font-bold">-4.2 kg</span>
              </div>
            </div>
          </div>

          {/* Middle Column: Copy & Checklist */}
          <div className="lg:col-span-4 lg:pl-6">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#76C043] mb-3">
              Track Your Progress
            </p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black uppercase tracking-tight text-white leading-[1.08]">
              See Real <br />
              <span className="text-[#76C043]">Results</span>
            </h2>
            <p className="mt-5 text-sm text-[#9CA3AF] leading-relaxed">
              Track your workouts, visualize your progress and stay accountable with our easy-to-use fitness tracking tools.
            </p>

            {/* Checklist */}
            <ul className="mt-6 space-y-3">
              {[
                "Track workouts & sets",
                "Monitor body composition",
                "Set and achieve goals",
                "Visual progress charts",
              ].map((item) => (
                <li key={item} className="flex items-center gap-3 text-xs sm:text-sm font-medium text-white">
                  <div className="h-5 w-5 rounded-full bg-[#76C043]/20 border border-[#76C043] flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span>{item}</span>
                </li>
              ))}
            </ul>

            <div className="mt-8">
              <Link
                href={PORTAL_LOGIN_URL}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full border border-[#76C043]/60 bg-[#0E1113] hover:bg-[#76C043]/10 text-white hover:text-[#76C043] text-xs font-bold uppercase tracking-wider transition-all"
              >
                <span>Start Tracking</span>
                <svg className="w-3.5 h-3.5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Right Column: Smartphone Mockup */}
          <div className="lg:col-span-3 flex justify-center">
            <div className="w-[230px] rounded-[36px] bg-[#0E1113] border-4 border-[#2D3339] p-3.5 shadow-[0_25px_60px_rgba(0,0,0,0.9)]">
              {/* Phone notch */}
              <div className="w-20 h-3.5 bg-[#1F2428] rounded-full mx-auto mb-3" />

              {/* Phone screen UI */}
              <div className="rounded-[24px] bg-[#08090A] p-3 text-center border border-white/5">
                <div className="flex items-center justify-center gap-1.5 mb-2">
                  <div className="h-4 w-4 rounded-full bg-[#76C043] flex items-center justify-center text-[8px] font-black text-black">✓</div>
                  <span className="text-[10px] font-bold text-white uppercase">Fit Me</span>
                </div>

                {/* Circular ring */}
                <div className="my-3 mx-auto h-20 w-20 rounded-full border-4 border-[#76C043] flex flex-col items-center justify-center shadow-[0_0_20px_rgba(118,192,67,0.4)]">
                  <span className="text-base font-black text-white leading-none">78%</span>
                  <span className="text-[8px] text-[#9CA3AF] uppercase">Daily Goal</span>
                </div>

                {/* Steps and calories */}
                <div className="grid grid-cols-2 gap-2 my-3 text-left">
                  <div className="p-1.5 rounded-lg bg-[#14181B] border border-white/5">
                    <p className="text-[8px] text-[#9CA3AF]">Steps</p>
                    <p className="text-xs font-bold text-white">8,450</p>
                  </div>
                  <div className="p-1.5 rounded-lg bg-[#14181B] border border-white/5">
                    <p className="text-[8px] text-[#9CA3AF]">Calories</p>
                    <p className="text-xs font-bold text-white">620</p>
                  </div>
                </div>

                {/* Weekly bar chart */}
                <p className="text-[8px] text-left text-[#9CA3AF] mb-1">Weekly Activity</p>
                <div className="h-10 flex items-end justify-between gap-1 px-1">
                  {[40, 65, 85, 55, 95, 75, 90].map((h, i) => (
                    <div
                      key={i}
                      style={{ height: `${h}%` }}
                      className="w-full bg-[#76C043] rounded-t-sm shadow-[0_0_6px_rgba(118,192,67,0.4)]"
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}

export default TrackProgressSection;
