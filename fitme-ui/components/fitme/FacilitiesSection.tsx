"use client";

import React, { useState } from "react";
import Image from "next/image";

const REAL_FACILITIES = [
  {
    id: "arena",
    title: "Main Training Arena",
    badge: "Pitigala Main Arena",
    description: "Wide open floor with high-end black & lime equipment layout",
    image: "/images/fitme-gym-arena-wide.jpeg",
    icon: (
      <svg className="w-5 h-5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
  },
  {
    id: "cardio",
    title: "Cardio Zone",
    badge: "Cardio & Endurance Area",
    description: "Million commercial treadmills, Concept2 rowers & spin bikes",
    image: "/images/fitme-cardio-zone.jpeg",
    icon: (
      <svg className="w-5 h-5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>
    ),
  },
  {
    id: "power",
    title: "Power & Squat Zone",
    badge: "Oxizen Power & Smith Machines",
    description: "Power rack, Smith machine, Olympic barbells & plate trees",
    image: "/images/fitme-gym-power-zone.jpeg",
    icon: (
      <svg className="w-5 h-5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    id: "dumbbells",
    title: "Free Weights & Dumbbells",
    badge: "Free Weight Sanctuary",
    description: "Complete dumbbell rack, kettlebells, flat/incline benches & mirrors",
    image: "/images/fitme-gym-dumbbells.jpeg",
    icon: (
      <svg className="w-5 h-5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
      </svg>
    ),
  },
  {
    id: "machines",
    title: "Selectorized Cable Line",
    badge: "Isolation & Machine Line",
    description: "Lat pulldown, assisted chin/dip, preacher curl & leg curl machines",
    image: "/images/fitme-gym-machine-line.jpeg",
    icon: (
      <svg className="w-5 h-5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
      </svg>
    ),
  },
  {
    id: "reception",
    title: "Reception & Member Lounge",
    badge: "Official Fit Me Reception",
    description: "Welcome desk with 3D illuminated Fit Me brand crest & support",
    image: "/images/fitme-reception-desk.jpeg",
    icon: (
      <svg className="w-5 h-5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 14v5m4-5v5m4-5v5M3 11h18M5 11V7a4 4 0 018 0v4" />
      </svg>
    ),
  },
];

const ALL_REAL_PHOTOS = [
  { src: "/images/fitme-gym-arena-wide.jpeg", label: "Main Arena Floor" },
  { src: "/images/fitme-cardio-zone.jpeg", label: "Cardio & Treadmills" },
  { src: "/images/fitme-gym-power-zone.jpeg", label: "Power & Squat Racks" },
  { src: "/images/fitme-gym-dumbbells.jpeg", label: "Dumbbells & Barbells" },
  { src: "/images/fitme-gym-freeweights.jpeg", label: "Preacher Curl & Plates" },
  { src: "/images/fitme-gym-machine-line.jpeg", label: "Cable & Machine Line" },
  { src: "/images/fitme-gym-benches.jpeg", label: "Incline & Flat Benches" },
  { src: "/images/fitme-gym-cables.jpeg", label: "Oxizen Cable Machine" },
  { src: "/images/fitme-gym-strength-zone.jpeg", label: "Smith & Strength Zone" },
  { src: "/images/fitme-gym-leg-machines.jpeg", label: "Leg Press & Changing Rooms" },
  { src: "/images/fitme-reception-desk.jpeg", label: "Front Reception Desk" },
];

export function FacilitiesSection() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [showAllModal, setShowAllModal] = useState(false);
  const current = REAL_FACILITIES[activeIndex];

  return (
    <section id="facilities" className="relative w-full bg-[#08090A] py-20 lg:py-28 border-t border-white/5 overflow-hidden">
      <div className="max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24">
        
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#76C043] mb-3">
              Our Facilities
            </p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black uppercase tracking-tight text-white leading-[1.08]">
              World-Class <br />
              <span className="text-[#76C043]">Gym Experience</span>
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowAllModal(true)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-[#76C043]/60 bg-[#0E1113] hover:bg-[#76C043]/15 text-white hover:text-[#76C043] text-xs font-bold uppercase tracking-wider transition-all"
            >
              <svg className="w-4 h-4 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>Explore All 11 Real Photos</span>
            </button>
          </div>
        </div>

        {/* Main Grid: Interactive Real Image on Left + Facility Badges on Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">

          {/* Left Column: Interactive Real Gym Photo */}
          <div className="lg:col-span-6 flex flex-col gap-4">
            <div className="relative h-[380px] sm:h-[440px] lg:h-[480px] rounded-2xl overflow-hidden border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.8)] group">
              <Image
                key={current.image}
                src={current.image}
                alt={current.title}
                fill
                priority
                sizes="(max-width: 1024px) 100vw, 50vw"
                className="object-cover object-center transition-all duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#08090A] via-transparent to-transparent opacity-85" />
              
              {/* Live Badge */}
              <div className="absolute bottom-6 left-6 inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-[#08090A]/85 backdrop-blur-md border border-[#76C043]/40 text-xs font-bold text-white shadow-[0_0_15px_rgba(0,0,0,0.8)]">
                <span className="h-2 w-2 rounded-full bg-[#76C043] animate-pulse" />
                <span>{current.badge}</span>
              </div>

              {/* Photo Counter */}
              <div className="absolute top-5 right-5 px-3 py-1 rounded-full bg-black/70 backdrop-blur-sm border border-white/10 text-[11px] font-bold text-white">
                {activeIndex + 1} / {REAL_FACILITIES.length}
              </div>
            </div>

            {/* Thumbnail Navigation Strip */}
            <div className="grid grid-cols-6 gap-2 pt-1">
              {REAL_FACILITIES.map((facility, idx) => (
                <button
                  key={facility.id}
                  onClick={() => setActiveIndex(idx)}
                  className={`relative h-14 sm:h-16 rounded-xl overflow-hidden border transition-all ${
                    activeIndex === idx
                      ? "border-[#76C043] shadow-[0_0_12px_rgba(118,192,67,0.5)] scale-105"
                      : "border-white/10 opacity-60 hover:opacity-100 hover:border-white/40"
                  }`}
                >
                  <Image
                    src={facility.image}
                    alt={facility.title}
                    fill
                    sizes="100px"
                    className="object-cover"
                  />
                </button>
              ))}
            </div>
          </div>

          {/* Right Column: 6 Interactive Facility Cards */}
          <div className="lg:col-span-6">
            <p className="text-sm sm:text-base text-[#9CA3AF] leading-relaxed mb-6">
              Train in a clean, modern, and fully air-conditioned fitness arena located in Pitigala, Sri Lanka. Equipped with certified Olympic bars, high-grade machines, and pristine amenities.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {REAL_FACILITIES.map((facility, idx) => {
                const isSelected = activeIndex === idx;
                return (
                  <button
                    key={facility.id}
                    onClick={() => setActiveIndex(idx)}
                    className={`text-left p-4 rounded-xl border transition-all duration-200 flex items-center gap-3.5 ${
                      isSelected
                        ? "bg-[#141A14] border-[#76C043] shadow-[0_0_20px_rgba(118,192,67,0.15)] translate-x-1"
                        : "bg-[#0D1012] border-white/5 hover:border-white/20 hover:bg-[#12161A]"
                    }`}
                  >
                    <div className={`h-10 w-10 rounded-lg border flex items-center justify-center flex-shrink-0 transition-colors ${
                      isSelected
                        ? "bg-[#76C043] text-black border-[#76C043]"
                        : "bg-[#141A14] text-[#76C043] border-[#76C043]/30"
                    }`}>
                      {facility.icon}
                    </div>
                    <div>
                      <h3 className={`text-sm font-bold transition-colors ${
                        isSelected ? "text-[#76C043]" : "text-white"
                      }`}>
                        {facility.title}
                      </h3>
                      <p className="text-[11px] text-[#9CA3AF] leading-snug line-clamp-1">
                        {facility.description}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

        </div>
      </div>

      {/* ── ALL REAL PHOTOS MODAL ────────────────────────────────────── */}
      {showAllModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md p-4 sm:p-8">
          <div className="relative w-full max-w-5xl bg-[#0D1012] border border-[#76C043]/40 rounded-3xl p-6 sm:p-8 max-h-[90vh] overflow-y-auto shadow-[0_0_50px_rgba(0,0,0,0.9)]">
            <div className="flex items-center justify-between pb-6 border-b border-white/10 mb-6">
              <div>
                <h3 className="text-xl sm:text-2xl font-black text-white uppercase tracking-tight">
                  Fit Me Pitigala — <span className="text-[#76C043]">Real Gym Interior</span>
                </h3>
                <p className="text-xs sm:text-sm text-[#9CA3AF] mt-1">
                  All 11 authentic photographs taken inside our facility
                </p>
              </div>
              <button
                onClick={() => setShowAllModal(false)}
                className="h-10 w-10 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            {/* Photo Gallery Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {ALL_REAL_PHOTOS.map((photo, i) => (
                <div key={i} className="group relative h-56 rounded-2xl overflow-hidden border border-white/10 hover:border-[#76C043]/60 transition-all">
                  <Image
                    src={photo.src}
                    alt={photo.label}
                    fill
                    sizes="(max-width: 768px) 100vw, 33vw"
                    className="object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-80" />
                  <div className="absolute bottom-3 left-3 right-3 text-xs font-bold text-white">
                    <span className="text-[#76C043]">●</span> {photo.label}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 text-center">
              <button
                onClick={() => setShowAllModal(false)}
                className="px-8 py-3 rounded-full bg-[#76C043] text-black text-xs font-black uppercase tracking-wider hover:bg-[#85D538] transition-colors"
              >
                Close Gallery
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default FacilitiesSection;
