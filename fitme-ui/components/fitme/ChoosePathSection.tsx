"use client";

import React from "react";
import Link from "next/link";
import { motion } from "motion/react";

const PATHS = [
  {
    title: "Get Stronger",
    description: "Build muscle & power",
    icon: (
      <svg className="w-6 h-6 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
  },
  {
    title: "Lose Weight",
    description: "Burn fat & boost energy",
    icon: (
      <svg className="w-6 h-6 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
      </svg>
    ),
  },
  {
    title: "Improve Health",
    description: "Feel better, live longer",
    icon: (
      <svg className="w-6 h-6 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>
    ),
  },
  {
    title: "Be Your Best",
    description: "Confidence & performance",
    icon: (
      <svg className="w-6 h-6 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
];

export function ChoosePathSection() {
  return (
    <section className="relative w-full bg-[#060708] py-20 lg:py-28 border-t border-white/5 overflow-hidden">
      <div className="max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">

          {/* Left Column */}
          <div className="lg:col-span-5">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#76C043] mb-3">
              Choose Your Path
            </p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black uppercase tracking-tight text-white leading-[1.08]">
              Your Goals. <br />
              <span className="text-[#76C043]">Our Support.</span>
            </h2>
            <p className="mt-5 text-sm sm:text-base text-[#9CA3AF] leading-relaxed">
              No matter where you are on your fitness journey, we have a path for you. Pick the program that fits your goals and let&apos;s get started.
            </p>
            <div className="mt-8">
              <Link
                href="#programs"
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full border border-[#76C043]/60 bg-[#0E1113] hover:bg-[#76C043]/10 text-white hover:text-[#76C043] text-xs font-bold uppercase tracking-wider transition-all"
              >
                <span>Explore All Paths</span>
                <svg className="w-3.5 h-3.5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Right Column: 4 Goal Path Cards */}
          <div className="lg:col-span-7 grid grid-cols-2 sm:grid-cols-4 gap-4">
            {PATHS.map((item) => (
              <div
                key={item.title}
                className="p-5 rounded-2xl bg-[#0D1012] border border-white/5 hover:border-[#76C043]/40 flex flex-col items-center text-center transition-all duration-300 hover:-translate-y-1 group"
              >
                <div className="h-14 w-14 rounded-full bg-[#141A14] border border-[#76C043]/30 flex items-center justify-center mb-4 group-hover:scale-110 shadow-[0_0_15px_rgba(118,192,67,0.2)] transition-transform">
                  {item.icon}
                </div>
                <h3 className="text-sm font-bold text-white mb-1.5 group-hover:text-[#76C043] transition-colors">
                  {item.title}
                </h3>
                <p className="text-[11px] text-[#9CA3AF] leading-relaxed">
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

export default ChoosePathSection;
