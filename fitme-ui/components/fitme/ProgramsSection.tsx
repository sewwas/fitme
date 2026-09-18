import React from "react";
import { SectionLabel } from "../ui/SectionLabel";
import { ProgramCard, ProgramItem } from "../ui/ProgramCard";

const FITME_PROGRAMS: ProgramItem[] = [
  {
    id: "strength",
    title: "STRENGTH",
    category: "Foundation & Power",
    description:
      "Master the foundational compound lifts—squat, bench press, deadlift, and overhead press—with periodized progressive overload.",
    difficulty: "Intermediate",
    sessionsPerWeek: "4 Sessions / Week",
    imageUrl:
      "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?q=80&w=800&auto=format&fit=crop",
    imageAlt: "Heavy barbell strength training in dark gym",
  },
  {
    id: "muscle-building",
    title: "MUSCLE BUILDING",
    category: "Hypertrophy System",
    description:
      "Targeted mechanical tension and volume protocols engineered for lean tissue development, symmetry, and metabolic stimulus.",
    difficulty: "Intermediate",
    sessionsPerWeek: "4–5 Sessions / Week",
    imageUrl:
      "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?q=80&w=800&auto=format&fit=crop",
    imageAlt: "Athlete performing controlled dumbbell press",
  },
  {
    id: "fat-loss",
    title: "FAT LOSS & RECOMP",
    category: "Metabolic Density",
    description:
      "Calibrated resistance circuits paired with customized energy balance protocols to preserve hard-earned muscle while stripping fat.",
    difficulty: "All Levels",
    sessionsPerWeek: "3–4 Sessions / Week",
    imageUrl:
      "https://images.unsplash.com/photo-1549060279-7e168fcee0c2?q=80&w=800&auto=format&fit=crop",
    imageAlt: "Dynamic conditioning and metabolic training",
  },
  {
    id: "athletic-performance",
    title: "ATHLETIC PERFORMANCE",
    category: "Speed & Durability",
    description:
      "Multi-planar power, rotational acceleration, plyometrics, and joint resilience designed for active field sport performers.",
    difficulty: "Advanced",
    sessionsPerWeek: "4 Sessions / Week",
    imageUrl:
      "https://images.unsplash.com/photo-1574680096145-d05b474e2155?q=80&w=800&auto=format&fit=crop",
    imageAlt: "High performance athletic training",
  },
  {
    id: "beginner",
    title: "BEGINNER FOUNDATIONS",
    category: "Movement Literacy",
    description:
      "Step into the gym with zero intimidation. Build movement competency, correct postural imbalances, and establish enduring training habits.",
    difficulty: "Beginner",
    sessionsPerWeek: "3 Sessions / Week",
    imageUrl:
      "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?q=80&w=800&auto=format&fit=crop",
    imageAlt: "Trainer guiding athlete on proper posture and form",
  },
];

export function ProgramsSection() {
  return (
    <section
      id="programs"
      className="relative w-full bg-[#0E1012] py-24 sm:py-32 border-t border-[#2D3339]/50"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 max-w-7xl">
          <div className="flex flex-col items-start max-w-2xl">
            <SectionLabel label="STRUCTURED TRAINING PATHS" />

            <h2 className="mt-5 text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#F8FAFC] uppercase">
              Choose <br />
              <span className="text-[#76C043]">Your Path</span>
            </h2>

            <p className="mt-4 text-base sm:text-lg text-[#9CA3AF]">
              Every body requires a distinct stimulus. Select a battle-tested
              pathway matched precisely to your schedule, training age, and
              aspirations.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-[#9CA3AF]">
              5 Tailored Pathways
            </span>
          </div>
        </div>

        {/* 5 Program Cards Grid */}
        <div className="mt-14 sm:mt-20 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {FITME_PROGRAMS.map((program) => (
            <ProgramCard key={program.id} program={program} />
          ))}
        </div>
      </div>
    </section>
  );
}

export default ProgramsSection;
