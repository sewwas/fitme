"use client";

import React from "react";
import { SectionLabel } from "../ui/SectionLabel";
import { Accordion, AccordionItemData } from "../ui/Accordion";
import { FadeIn } from "../ui/MotionWrapper";

const FAQ_ITEMS: AccordionItemData[] = [
  {
    id: "who-is-fit-me-for",
    question: "Who is Fit Me for?",
    answer:
      "Fit Me is engineered for anyone who values structure, safety, and measurable progress over chaotic gym routines. Whether you are a beginner looking to lift with confidence or an experienced athlete breaking through a plateau, our method is calibrated to your baseline.",
  },
  {
    id: "previous-gym-experience",
    question: "Do I need previous gym experience?",
    answer:
      "No. Over 60% of our new members have never touched an Olympic barbell before joining. Our Beginner Foundations program starts from mobility, postural alignment, and movement patterns so you never feel out of place.",
  },
  {
    id: "assessment-work",
    question: "How does the assessment work?",
    answer:
      "Your day one includes a comprehensive 45-minute baseline session where we screen your joint mobility, review any previous injuries, discuss your weekly schedule, and measure baseline biometrics. This becomes the foundation of your plan.",
  },
  {
    id: "program-customization",
    question: "How are programs customized?",
    answer:
      "Your training program is constructed based on your assessment results, training frequency (3, 4, or 5 days/week), and specific goals (strength, hypertrophy, metabolic health, or athletic performance). Workouts are updated in 4 to 8 week progressive blocks.",
  },
  {
    id: "change-programs",
    question: "Can I change programs?",
    answer:
      "Yes. Fitness is dynamic. When your lifestyle changes or when you achieve a specific milestone (e.g. transitioning from Fat Loss to Hypertrophy), your coach will recalibrate your training block during your routine progress review.",
  },
  {
    id: "nutrition-guidance",
    question: "Do you provide nutrition guidance?",
    answer:
      "Yes. We offer sustainable, non-restrictive nutrition coaching tailored to local Sri Lankan whole foods and dining patterns. We calculate your daily caloric and protein targets without demanding extreme or unsustainable crash dieting.",
  },
  {
    id: "membership-work",
    question: "How does membership work?",
    answer:
      "Memberships are monthly, straightforward, and zero-contract. You can join online or visit our Pitigala facility directly. Every membership tier includes full access to our facility, equipment, and coach support.",
  },
];

export function FAQSection() {
  return (
    <section
      id="faq"
      className="relative w-full bg-[#0B0D0E] py-24 sm:py-32 border-t border-[#2D3339]/50"
    >
      <div className="max-w-5xl mx-auto px-4 sm:px-8 lg:px-12">
        {/* Header */}
        <FadeIn direction="up" distance={20} className="flex flex-col items-start">
          <SectionLabel label="QUESTIONS & ANSWERS" />

          <h2 className="mt-5 text-3xl sm:text-5xl font-black tracking-tight text-[#F8FAFC] uppercase">
            Frequently Asked <br />
            <span className="text-[#76C043]">Questions</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-[#9CA3AF]">
            Everything you need to know about getting started at Fit Me.
          </p>
        </FadeIn>

        {/* Accordion Component with FadeIn */}
        <FadeIn direction="up" distance={20} delay={0.15} className="mt-12 sm:mt-16">
          <Accordion items={FAQ_ITEMS} defaultOpenIndex={0} />
        </FadeIn>

        {/* Still have questions prompt */}
        <FadeIn direction="up" distance={16} delay={0.25} className="mt-12">
          <div className="rounded-xl border border-[#2D3339] bg-[#121517] p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 card-hover-border">
            <div>
              <h4 className="text-base font-bold text-[#F8FAFC]">
                Have a specific question not listed here?
              </h4>
              <p className="text-sm text-[#9CA3AF] mt-0.5">
                Talk directly with our coaching staff in Pitigala.
              </p>
            </div>
            <a
              href="tel:0707627878"
              className="inline-flex items-center gap-2 rounded-lg border border-[#76C043]/40 bg-[#76C043]/10 px-5 py-2.5 text-xs font-mono font-bold uppercase text-[#76C043] hover:bg-[#76C043] hover:text-[#0B0D0E] hover:shadow-[0_0_18px_rgba(118,192,67,0.4)] transition-all"
            >
              <span>Call 070 762 7878</span>
            </a>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

export default FAQSection;
