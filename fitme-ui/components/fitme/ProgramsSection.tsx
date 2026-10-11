"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "motion/react";

const PROGRAMS = [
  {
    title: "Strength Training",
    description: "Build muscle, increase power. Get stronger.",
    image: "/images/program-strength.jpg",
    icon: (
      <svg className="w-4 h-4 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
  },
  {
    title: "Weight Loss",
    description: "Burn fat, boost energy. Feel lighter.",
    image: "/images/program-hiit.jpg",
    icon: (
      <svg className="w-4 h-4 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
      </svg>
    ),
  },
  {
    title: "Functional Training",
    description: "Move better. Perform stronger. Live healthier.",
    image: "/images/program-functional.jpg",
    icon: (
      <svg className="w-4 h-4 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    title: "Athletic Performance",
    description: "Improve speed, agility and endurance.",
    image: "/images/program-hypertrophy.jpg",
    icon: (
      <svg className="w-4 h-4 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
];

export function ProgramsSection() {
  return (
    <section id="programs" className="relative w-full bg-[#060708] py-20 lg:py-28 border-t border-white/5 overflow-hidden">
      <div className="max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">
          {/* Left Column: Heading & Copy */}
          <div className="lg:col-span-4 lg:sticky lg:top-28">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#76C043] mb-3">
              Training Programs
            </p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black uppercase tracking-tight text-white leading-[1.08]">
              Build The Best <br />
              <span className="text-[#76C043]">Version Of You</span>
            </h2>
            <p className="mt-5 text-sm sm:text-base text-[#9CA3AF] leading-relaxed">
              Choose from a variety of programs designed to meet your fitness goals — from strength
              and weight loss to performance and overall wellness.
            </p>
            <div className="mt-8">
              <Link
                href="#pricing"
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full border border-[#76C043]/60 bg-[#0E1113] hover:bg-[#76C043]/10 text-white hover:text-[#76C043] text-xs font-bold uppercase tracking-wider transition-all"
              >
                <span>View All Programs</span>
                <svg className="w-3.5 h-3.5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Right Column: 4 Vertical Program Cards */}
          <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {PROGRAMS.map((program) => (
              <div
                key={program.title}
                className="group relative flex flex-col justify-end overflow-hidden rounded-2xl bg-[#0D1012] border border-white/5 hover:border-[#76C043]/40 min-h-[380px] p-5 transition-all duration-300 hover:-translate-y-1.5 shadow-[0_10px_30px_rgba(0,0,0,0.6)]"
              >
                {/* Background Image */}
                <div className="absolute inset-0 z-0">
                  <Image
                    src={program.image}
                    alt={program.title}
                    fill
                    sizes="(max-width: 768px) 100vw, 25vw"
                    className="object-cover object-center transition-transform duration-500 group-hover:scale-105 opacity-60"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#070809] via-[#070809]/65 to-transparent" />
                </div>

                {/* Content Overlay */}
                <div className="relative z-10 flex flex-col justify-end h-full">
                  <div className="h-9 w-9 rounded-full bg-[#141A14]/90 backdrop-blur-sm border border-[#76C043]/40 flex items-center justify-center mb-3">
                    {program.icon}
                  </div>
                  <h3 className="text-base font-black uppercase text-white tracking-wide group-hover:text-[#76C043] transition-colors leading-tight mb-1.5">
                    {program.title}
                  </h3>
                  <p className="text-xs text-[#C5CBD3] leading-relaxed line-clamp-2">
                    {program.description}
                  </p>
                  <div className="mt-4 flex items-center justify-end text-[#76C043]">
                    <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default ProgramsSection;
