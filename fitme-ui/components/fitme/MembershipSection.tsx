"use client";

import React from "react";
import Link from "next/link";
import { motion } from "motion/react";

const PLANS = [
  {
    name: "Basic",
    price: "4,500",
    popular: false,
    features: [
      "Gym access",
      "Locker room access",
    ],
  },
  {
    name: "Standard",
    price: "7,500",
    popular: true,
    features: [
      "All Basic features",
      "Group classes",
      "Progress tracking",
    ],
  },
  {
    name: "Premium",
    price: "11,500",
    popular: false,
    features: [
      "All Standard features",
      "Personal training (2x/mo)",
      "Nutrition guidance",
    ],
  },
  {
    name: "Elite",
    price: "15,000",
    popular: false,
    features: [
      "All Premium features",
      "Unlimited personal training",
      "VIP locker & perks",
    ],
  },
];

export function MembershipSection() {
  return (
    <section id="pricing" className="relative w-full bg-[#060708] py-20 lg:py-28 border-t border-white/5 overflow-hidden">
      <div className="max-w-[1750px] mx-auto px-5 sm:px-10 lg:px-16 xl:px-24">
        {/* Header Block */}
        <div className="max-w-2xl mb-14">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-[#76C043] mb-3">
            Membership Plans
          </p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black uppercase tracking-tight text-white leading-none">
            Flexible Plans <br />
            <span className="text-[#76C043]">For Every Goal</span>
          </h2>
          <p className="mt-4 text-sm sm:text-base text-[#9CA3AF]">
            Choose a plan that fits your lifestyle and start your fitness journey today.
          </p>
          <div className="mt-6">
            <Link
              href="#membership-details"
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full border border-[#76C043]/60 bg-[#0E1113] hover:bg-[#76C043]/10 text-white hover:text-[#76C043] text-xs font-bold uppercase tracking-wider transition-all"
            >
              <span>Get Started</span>
              <svg className="w-3.5 h-3.5 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>
        </div>

        {/* 4 Pricing Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`relative flex flex-col justify-between p-6 rounded-2xl transition-all duration-300 ${
                plan.popular
                  ? "bg-[#0E140E] border-2 border-[#76C043] shadow-[0_0_40px_rgba(118,192,67,0.25)] -translate-y-2"
                  : "bg-[#0D1012] border border-white/5 hover:border-white/20 hover:-translate-y-1"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-[#76C043] text-black text-[10px] font-black uppercase tracking-wider shadow-[0_0_12px_rgba(118,192,67,0.6)]">
                  Most Popular
                </div>
              )}

              <div>
                <h3 className="text-lg font-bold text-white mb-2">{plan.name}</h3>
                <div className="flex items-baseline gap-1.5 mb-6">
                  <span className="text-xs text-[#9CA3AF] font-bold">LKR</span>
                  <span className="text-3xl font-black text-white">{plan.price}</span>
                  <span className="text-xs text-[#9CA3AF]">/month</span>
                </div>

                {/* Features List */}
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feat) => (
                    <li key={feat} className="flex items-center gap-2.5 text-xs text-[#C5CBD3]">
                      <svg className="w-4 h-4 text-[#76C043] flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                      </svg>
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Action Button */}
              <Link
                href="http://localhost:8000/register/"
                className={`w-full py-2.5 rounded-xl text-center text-xs font-black uppercase tracking-wider transition-all block ${
                  plan.popular
                    ? "bg-[#76C043] hover:bg-[#85D538] text-black shadow-[0_0_20px_rgba(118,192,67,0.4)]"
                    : "bg-[#14181B] hover:bg-[#1A2024] text-white border border-white/10 hover:border-[#76C043]"
                }`}
              >
                Join Now
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default MembershipSection;
