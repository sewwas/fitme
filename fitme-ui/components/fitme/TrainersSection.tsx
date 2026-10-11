"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "motion/react";

const TRAINERS = [
  {
    name: "Sajan Silva",
    role: "Head Trainer & Strength Coach",
    experience: "8+ Years Experience",
    image: "/images/coach-janith.jpg",
  },
  {
    name: "Nelka Perera",
    role: "Fitness & Nutrition Coach",
    experience: "6+ Years Experience",
    image: "/images/coach-ruchira.jpg",
  },
  {
    name: "Ravi Fernando",
    role: "Performance Coach",
    experience: "5+ Years Experience",
    image: "/images/coach-sewwandi.jpg",
  },
];

export function TrainersSection() {
  return (
    <section id="trainers" className="relative w-full bg-[#08090A] py-20 lg:py-28 border-t border-white/5 overflow-hidden">
      <div className="max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">

          {/* Left Column: Copy & CTA */}
          <div className="lg:col-span-5">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#76C043] mb-3">
              Meet Our Trainers
            </p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black uppercase tracking-tight text-white leading-[1.08]">
              Expert Guidance. <br />
              <span className="text-[#76C043]">Real Support.</span>
            </h2>
            <p className="mt-5 text-sm sm:text-base text-[#9CA3AF] leading-relaxed">
              Our certified trainers are here to guide, motivate and help you achieve your best.
            </p>
            <div className="mt-8">
              <Link
                href="#pricing"
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full border border-[#76C043]/60 bg-[#0E1113] hover:bg-[#76C043]/10 text-white hover:text-[#76C043] text-xs font-bold uppercase tracking-wider transition-all"
              >
                <span>Meet Our Team</span>
                <svg className="w-3.5 h-3.5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Right Column: 3 Trainer Cards */}
          <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-5">
            {TRAINERS.map((trainer, idx) => (
              <div
                key={trainer.name}
                className="group p-4 rounded-2xl bg-[#0D1012] border border-white/5 hover:border-[#76C043]/40 transition-all duration-300 hover:-translate-y-1 flex flex-col items-center text-center shadow-[0_10px_30px_rgba(0,0,0,0.6)]"
              >
                {/* Trainer Portrait */}
                <div className="relative w-full h-56 rounded-xl overflow-hidden mb-4 bg-[#121517]">
                  <Image
                    src={trainer.image}
                    alt={trainer.name}
                    fill
                    sizes="(max-width: 768px) 100vw, 33vw"
                    className="object-cover object-center group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#0D1012] via-transparent to-transparent opacity-80" />
                </div>

                <h3 className="text-base font-bold text-white group-hover:text-[#76C043] transition-colors">
                  {trainer.name}
                </h3>
                <p className="text-xs text-[#9CA3AF] mt-0.5 mb-3 leading-tight">
                  {trainer.role}
                </p>

                {/* Experience Badge */}
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#141A14] border border-[#76C043]/30 text-[10px] font-bold text-[#76C043] uppercase tracking-wide">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#76C043]" />
                  {trainer.experience}
                </span>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}

export default TrainersSection;
