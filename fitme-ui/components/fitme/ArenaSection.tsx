import React from "react";
import { SectionLabel } from "../ui/SectionLabel";
import { ImageCard } from "../ui/ImageCard";

const ARENA_CARDS = [
  {
    indexNumber: "01",
    title: "THE IRON SANCTUARY",
    subtitle: "Facility & Gear",
    description:
      "A distraction-free, professional athletic facility loaded with Olympic barbells, calibrated plates, racks, and specialty machinery.",
    imageUrl:
      "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?q=80&w=1000&auto=format&fit=crop",
    imageAlt: "The Iron Sanctuary modern training area with barbells and racks",
  },
  {
    indexNumber: "02",
    title: "HUMAN ARCHITECTURE",
    subtitle: "Coaching & Form",
    description:
      "High-touch 1-on-1 and small squad coaching. Real-time bio-mechanical cues to lift injury-free with undeniable intent.",
    imageUrl:
      "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?q=80&w=1000&auto=format&fit=crop",
    imageAlt: "Personal coach guiding athlete during barbell training",
  },
  {
    indexNumber: "03",
    title: "FUEL CALIBRATION",
    subtitle: "Nutritional Science",
    description:
      "Practical, non-dogmatic nutritional support tailored to Sri Lankan lifestyles and real-world dining habits for sustainable energy.",
    imageUrl:
      "https://images.unsplash.com/photo-1490645935967-10de6ba17061?q=80&w=1000&auto=format&fit=crop",
    imageAlt: "Wholesome nutrient-dense nutrition setup for athletes",
  },
];

export function ArenaSection() {
  return (
    <section
      id="arena"
      className="relative w-full bg-[#0B0D0E] py-24 sm:py-32 border-t border-[#2D3339]/50"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col items-start max-w-3xl">
          <SectionLabel chapter="CHAPTER 04" label="THE ARENA" />

          <h2 className="mt-5 text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#F8FAFC] uppercase">
            Heavy Iron. <br />
            <span className="text-[#76C043]">True Guidance.</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-[#9CA3AF] max-w-2xl">
            Located in Pitigala, Fit Me combines top-tier biomechanical
            equipment with elite coaching culture. No gimmicks, no fluff—just
            purposeful progression.
          </p>
        </div>

        {/* 3 Large Image Cards */}
        <div className="mt-14 sm:mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {ARENA_CARDS.map((card) => (
            <ImageCard
              key={card.indexNumber}
              indexNumber={card.indexNumber}
              title={card.title}
              subtitle={card.subtitle}
              description={card.description}
              imageUrl={card.imageUrl}
              imageAlt={card.imageAlt}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

export default ArenaSection;
