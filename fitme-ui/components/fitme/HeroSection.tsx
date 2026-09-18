"use client";

import React from "react";
import Image from "next/image";
import { motion } from "motion/react";
import { PrimaryButton } from "../ui/PrimaryButton";
import { SecondaryButton } from "../ui/SecondaryButton";
import { SectionLabel } from "../ui/SectionLabel";

export function HeroSection() {
  return (
    <section
      id="hero"
      className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-[#0B0D0E] pt-24 pb-16 lg:py-0"
    >
      {/* Hero Background Image with Cinematic Treatment */}
      <div className="absolute inset-0 z-0 overflow-hidden">
        <div className="relative w-full h-full animate-hero-zoom">
          <Image
            src="https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=2070&auto=format&fit=crop"
            alt="Athlete training with purpose in high-end moody gym setting"
            fill
            priority
            sizes="100vw"
            className="object-cover object-center lg:object-[70%_35%]"
          />
        </div>

        {/* Multi-layer Dark Gradient for Flawless Readability */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#0B0D0E] via-[#0B0D0E]/85 to-[#0B0D0E]/30 hidden lg:block" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0B0D0E] via-[#0B0D0E]/80 to-[#0B0D0E]/40 lg:bg-gradient-to-t lg:from-[#0B0D0E] lg:via-transparent lg:to-[#0B0D0E]/60" />

        {/* Subtle Lime Ambient Practical Lighting (controlled, breathing) */}
        <div className="absolute -top-32 left-1/4 h-96 w-96 rounded-full bg-[#76C043] blur-3xl pointer-events-none animate-ambient-glow" />
        <div className="absolute bottom-10 right-1/4 h-80 w-80 rounded-full bg-[#76C043]/30 blur-3xl pointer-events-none animate-ambient-glow" style={{ animationDelay: "4s" }} />

        {/* Black Vignette overlay */}
        <div className="absolute inset-0 shadow-[inset_0_0_120px_rgba(11,13,14,0.9)] pointer-events-none" />
      </div>

      {/* Hero Content Container */}
      <div className="relative z-10 w-full max-w-[1750px] mx-auto px-4 sm:px-8 lg:px-14 xl:px-20 py-12 lg:py-28">
        <div className="max-w-2xl lg:max-w-3xl">
          {/* Chapter 01 Label */}
          <motion.div
            initial={{ opacity: 0, y: -16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.21, 0.47, 0.32, 0.98] }}
            className="mb-6"
          >
            <SectionLabel chapter="CHAPTER 01" label="THE CHOICE" />
          </motion.div>

          {/* Large Bold Typography with Staggered Cascade */}
          <h1 className="text-5xl sm:text-7xl lg:text-8xl font-black tracking-tighter text-[#F8FAFC] uppercase leading-[0.92] overflow-hidden">
            <motion.span
              className="block"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1, ease: [0.21, 0.47, 0.32, 0.98] }}
            >
              Transform
            </motion.span>
            <motion.span
              className="block text-transparent bg-clip-text bg-gradient-to-r from-[#F8FAFC] via-[#F8FAFC] to-[#9CA3AF]"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.22, ease: [0.21, 0.47, 0.32, 0.98] }}
            >
              Your
            </motion.span>
            <motion.span
              className="block text-[#76C043] drop-shadow-[0_0_35px_rgba(118,192,67,0.3)]"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.34, ease: [0.21, 0.47, 0.32, 0.98] }}
            >
              Journey
            </motion.span>
          </h1>

          {/* Supporting Copy */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.45, ease: [0.21, 0.47, 0.32, 0.98] }}
            className="mt-6 sm:mt-8 text-base sm:text-lg lg:text-xl leading-relaxed text-[#9CA3AF] max-w-xl font-normal"
          >
            Train with purpose. Move with confidence. Build a sustainable
            fitness routine with structured training, personal coaching, and
            measurable progress.
          </motion.p>

          {/* CTA Row with Subtle Pulse on Primary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.58, ease: [0.21, 0.47, 0.32, 0.98] }}
            className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-stretch sm:items-center gap-4"
          >
            <div className="relative group">
              <div className="absolute -inset-0.5 rounded-lg bg-[#76C043]/30 blur opacity-75 group-hover:opacity-100 transition duration-300 group-hover:blur-md" />
              <PrimaryButton href="#membership" size="lg" className="relative">
                Start Your Transformation
              </PrimaryButton>
            </div>
            <SecondaryButton href="#programs" size="lg">
              Explore Programs
            </SecondaryButton>
          </motion.div>

          {/* Small Trust Row */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.9, delay: 0.75 }}
            className="mt-12 sm:mt-16 pt-8 border-t border-[#2D3339]/80 max-w-lg"
          >
            <p className="text-[11px] font-mono font-semibold tracking-widest text-[#9CA3AF] uppercase flex flex-wrap items-center gap-x-3 gap-y-2">
              <span className="text-[#F8FAFC]">COACHING</span>
              <span className="text-[#76C043] animate-pulse">•</span>
              <span className="text-[#F8FAFC]">TRAINING</span>
              <span className="text-[#76C043] animate-pulse">•</span>
              <span className="text-[#F8FAFC]">NUTRITION</span>
              <span className="text-[#76C043] animate-pulse">•</span>
              <span className="text-[#F8FAFC]">PROGRESS TRACKING</span>
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export default HeroSection;
