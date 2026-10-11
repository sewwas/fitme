"use client";

import React, { useState } from "react";
import Image from "next/image";
import { motion } from "motion/react";

const TESTIMONIALS = [
  {
    name: "Kasun Perera",
    role: "Member for 6 months",
    avatar: "/images/coach-janith.jpg",
    quote:
      "Fit Me changed my life. The trainers are amazing and the atmosphere is so motivating. I've never felt stronger or healthier!",
  },
  {
    name: "Natasha Silva",
    role: "Member for 4 months",
    avatar: "/images/coach-ruchira.jpg",
    quote:
      "The personalized training plan helped me lose weight and gain confidence. Best fitness decision I've made!",
  },
  {
    name: "Dinesh Fernando",
    role: "Member for 8 months",
    avatar: "/images/coach-sewwandi.jpg",
    quote:
      "Top-class equipment, great coaches and a friendly community. I love being part of Fit Me!",
  },
];

export function TestimonialsSection() {
  const [activeIdx, setActiveIdx] = useState(0);

  const prev = () => setActiveIdx((i) => (i === 0 ? TESTIMONIALS.length - 1 : i - 1));
  const next = () => setActiveIdx((i) => (i === TESTIMONIALS.length - 1 ? 0 : i + 1));

  return (
    <section id="testimonials" className="relative w-full bg-[#060708] py-20 lg:py-28 border-t border-white/5 overflow-hidden">
      <div className="max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24">
        {/* Header Row with Navigation Arrows */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-12">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#76C043] mb-3">
              Real Stories
            </p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black uppercase tracking-tight text-white leading-none">
              Member <span className="text-[#76C043]">Testimonials</span>
            </h2>
            <p className="mt-4 text-sm sm:text-base text-[#9CA3AF]">
              Real people. Real results. Here&apos;s what our members have to say.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={prev}
              aria-label="Previous testimonial"
              className="h-10 w-10 rounded-full border border-white/10 bg-[#0E1113] hover:border-[#76C043] hover:text-[#76C043] text-[#9CA3AF] flex items-center justify-center transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              type="button"
              onClick={next}
              aria-label="Next testimonial"
              className="h-10 w-10 rounded-full border border-white/10 bg-[#0E1113] hover:border-[#76C043] hover:text-[#76C043] text-[#9CA3AF] flex items-center justify-center transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>

        {/* 3 Testimonials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((item) => (
            <div
              key={item.name}
              className="p-6 rounded-2xl bg-[#0D1012] border border-white/5 hover:border-[#76C043]/30 transition-all duration-300 hover:-translate-y-1 flex flex-col justify-between"
            >
              {/* Member Profile */}
              <div>
                <div className="flex items-center gap-3.5 mb-4">
                  <div className="relative h-12 w-12 rounded-full overflow-hidden border-2 border-[#76C043] shadow-[0_0_12px_rgba(118,192,67,0.3)] flex-shrink-0">
                    <Image
                      src={item.avatar}
                      alt={item.name}
                      fill
                      className="object-cover"
                    />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">{item.name}</h3>
                    <p className="text-xs text-[#9CA3AF]">{item.role}</p>
                    {/* 5 Stars */}
                    <div className="flex items-center gap-1 mt-1 text-[#76C043]">
                      {[...Array(5)].map((_, i) => (
                        <svg key={i} className="w-3.5 h-3.5 fill-current" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                    </div>
                  </div>
                </div>

                <p className="text-xs sm:text-sm text-[#C5CBD3] leading-relaxed italic">
                  &ldquo;{item.quote}&rdquo;
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default TestimonialsSection;
