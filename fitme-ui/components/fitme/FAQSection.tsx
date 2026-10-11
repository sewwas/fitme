"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "motion/react";

const FAQS = [
  {
    q: "What are the membership options?",
    a: "We offer flexible monthly and annual plans ranging from Basic (gym & lockers) to Standard, Premium (with PT & nutrition), and Elite tiers. No lock-in contracts.",
  },
  {
    q: "Can I try a free trial?",
    a: "Yes! First-time visitors can book a complimentary day trial to experience our facilities, coaching atmosphere and equipment firsthand.",
  },
  {
    q: "What should I bring to my first session?",
    a: "Bring clean athletic training shoes, a personal workout towel, a water bottle, and your passion to train. We provide lockable storage and showers.",
  },
  {
    q: "Are personal trainers included in the membership?",
    a: "Premium plans include 2 personal training sessions per month, while Elite plans feature dedicated coach supervision. 1-on-1 packages can also be added anytime.",
  },
  {
    q: "What are the gym hours?",
    a: "Fit Me Pitigala is open Monday through Saturday from 5:30 AM to 10:00 PM, and Sundays from 6:00 AM to 8:00 PM.",
  },
];

export function FAQSection() {
  const [openIdx, setOpenIdx] = useState<number | null>(0);

  const toggle = (idx: number) => {
    setOpenIdx(openIdx === idx ? null : idx);
  };

  return (
    <section id="faq" className="relative w-full bg-[#08090A] py-20 lg:py-28 border-t border-white/5 overflow-hidden">
      <div className="max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">

          {/* Left Column */}
          <div className="lg:col-span-5">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#76C043] mb-3">
              Frequently Asked
            </p>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black uppercase tracking-tight text-white leading-none">
              <span className="text-[#76C043]">Questions</span>
            </h2>
            <p className="mt-5 text-sm sm:text-base text-[#9CA3AF] leading-relaxed">
              Find answers to the most common questions about memberships, training and our facilities.
            </p>
            <div className="mt-8">
              <Link
                href="#contact"
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full border border-[#76C043]/60 bg-[#0E1113] hover:bg-[#76C043]/10 text-white hover:text-[#76C043] text-xs font-bold uppercase tracking-wider transition-all"
              >
                <span>View All FAQs</span>
                <svg className="w-3.5 h-3.5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Right Column: Accordion */}
          <div className="lg:col-span-7 space-y-3">
            {FAQS.map((faq, idx) => {
              const isOpen = openIdx === idx;
              return (
                <div
                  key={faq.q}
                  className="rounded-xl bg-[#0D1012] border border-white/5 overflow-hidden transition-colors hover:border-[#76C043]/30"
                >
                  <button
                    type="button"
                    onClick={() => toggle(idx)}
                    className="w-full p-4 sm:p-5 text-left flex items-center justify-between gap-4 font-semibold text-sm sm:text-base text-white hover:text-[#76C043] transition-colors"
                  >
                    <span>{faq.q}</span>
                    <svg
                      className={`w-4 h-4 text-[#76C043] flex-shrink-0 transform transition-transform duration-200 ${
                        isOpen ? "rotate-90" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7" />
                    </svg>
                  </button>

                  <AnimatePresence>
                    {isOpen && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div className="px-5 pb-5 pt-1 text-xs sm:text-sm text-[#9CA3AF] leading-relaxed border-t border-white/5">
                          {faq.a}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>

        </div>
      </div>
    </section>
  );
}

export default FAQSection;
