import React from "react";
import Image from "next/image";
import Link from "next/link";
import { SectionLabel } from "../ui/SectionLabel";

interface CoachProfile {
  name: string;
  role: string;
  specialties: string[];
  bio: string;
  imageUrl: string;
  credentials: string;
}

const COACHES: CoachProfile[] = [
  {
    name: "Sewwandi Jayawardene",
    role: "Head Coach & Founder",
    specialties: ["Biomechanics", "Barbell Strength", "Periodization"],
    bio: "Over 8 years of dedicated strength coaching. Obsessed with joint integrity, technical mastery, and transforming everyday lifters into resilient athletes.",
    credentials: "CSCS • Precision Nutrition L1",
    imageUrl:
      "https://images.unsplash.com/photo-1567013127542-490d757e51fc?q=80&w=800&auto=format&fit=crop",
  },
  {
    name: "Ruchira Perera",
    role: "Performance & Conditioning Specialist",
    specialties: ["Hypertrophy", "Metabolic Density", "Mobility"],
    bio: "Former competitive athlete specializing in muscular hypertrophy, structural balance, and fat loss without metabolic burnout.",
    credentials: "ACSM Certified • Kettlebell Master",
    imageUrl:
      "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=800&auto=format&fit=crop",
  },
  {
    name: "Janith Silva",
    role: "Strength & Rehabilitation Coach",
    specialties: ["Corrective Exercise", "Postural Rehab", "Youth Athletics"],
    bio: "Focuses on rebuilding pain-free movement patterns, shoulder and lower-back health, and transitioning novices to lifelong lifters.",
    credentials: "NASM-CES • FMS Certified",
    imageUrl:
      "https://images.unsplash.com/photo-1507398941214-572c25f4b1dc?q=80&w=800&auto=format&fit=crop",
  },
];

export function CoachesSection() {
  return (
    <section
      id="coaches"
      className="relative w-full bg-[#0B0D0E] py-24 sm:py-32 border-t border-[#2D3339]/50"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col items-start max-w-3xl">
          <SectionLabel label="THE COACHING SQUAD" />

          <h2 className="mt-5 text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#F8FAFC] uppercase">
            Meet Your <br />
            <span className="text-[#76C043]">Coaches</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-[#9CA3AF] max-w-2xl">
            True guidance means certified, empathetic mentorship. Our coaches are
            on the floor with you every day, calibrating your form and keeping
            you focused.
          </p>
        </div>

        {/* Coach Cards */}
        <div className="mt-14 sm:mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {COACHES.map((coach) => (
            <div
              key={coach.name}
              className="group relative flex flex-col justify-between overflow-hidden rounded-xl border border-[#2D3339] bg-[#121517] transition-all duration-300 hover:border-[#76C043]/50 hover:shadow-[0_12px_32px_rgba(0,0,0,0.6)]"
            >
              {/* Coach Image */}
              <div className="relative h-80 w-full overflow-hidden bg-[#0E1012]">
                <Image
                  src={coach.imageUrl}
                  alt={coach.name}
                  fill
                  sizes="(max-width: 768px) 100vw, 33vw"
                  className="object-cover object-top transition-transform duration-700 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#121517] via-[#121517]/30 to-transparent" />
                <div className="absolute top-4 right-4">
                  <span className="rounded bg-[#0B0D0E]/80 backdrop-blur-md px-2 py-1 text-[10px] font-mono font-semibold uppercase text-[#76C043] border border-[#2D3339]">
                    {coach.credentials}
                  </span>
                </div>
              </div>

              {/* Coach Details */}
              <div className="flex flex-1 flex-col justify-between p-6 sm:p-7">
                <div>
                  <h3 className="text-xl font-bold tracking-tight text-[#F8FAFC] group-hover:text-[#76C043] transition-colors duration-200">
                    {coach.name}
                  </h3>
                  <p className="text-xs font-semibold uppercase tracking-wider text-[#76C043] mt-1">
                    {coach.role}
                  </p>

                  <p className="mt-3.5 text-sm leading-relaxed text-[#9CA3AF]">
                    {coach.bio}
                  </p>

                  {/* Specialties Pills */}
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {coach.specialties.map((spec) => (
                      <span
                        key={spec}
                        className="rounded bg-[#0B0D0E] px-2.5 py-1 text-[10px] font-mono text-[#9CA3AF] border border-[#2D3339]"
                      >
                        {spec}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-6 pt-5 border-t border-[#2D3339]/60 flex items-center justify-between">
                  <Link
                    href="#membership"
                    className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#76C043] group-hover:translate-x-1 transition-transform"
                  >
                    <span>View Profile</span>
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                  </Link>
                  <span className="text-[11px] font-mono text-[#9CA3AF]">Pitigala Onsite</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default CoachesSection;
