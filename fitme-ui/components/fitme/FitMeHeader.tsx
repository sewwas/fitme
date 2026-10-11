"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { PrimaryButton } from "../ui/PrimaryButton";
import { SecondaryButton } from "../ui/SecondaryButton";
import { MobileMenu } from "./MobileMenu";

import { NAV_ITEMS } from "./navigation";

export function FitMeHeader() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("hero");

  // Scroll listener for opacity & active section tracking
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 40);

      // Simple intersection check for nav highlight
      const sections = NAV_ITEMS.map((item) => item.href.replace("#", ""));
      for (const sectionId of sections) {
        const el = document.getElementById(sectionId);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 180 && rect.bottom >= 180) {
            setActiveSection(sectionId);
            break;
          }
        }
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <header
        className={`fixed top-0 inset-x-0 z-40 transition-all duration-300 ${
          isScrolled
            ? "bg-[#0B0D0E]/90 backdrop-blur-md border-b border-[#2D3339] py-3.5 shadow-[0_4px_20px_rgba(0,0,0,0.5)]"
            : "bg-gradient-to-b from-[#0B0D0E]/90 via-[#0B0D0E]/40 to-transparent py-5"
        }`}
      >
        <div className="max-w-[1750px] mx-auto px-4 sm:px-8 lg:px-14 xl:px-20 flex items-center justify-between">
          {/* Brand Logo & Tagline */}
          {/* Brand Logo */}
          <Link
            href="#hero"
            className="flex items-center gap-3 group focus-visible:outline-none"
          >
            <div className="relative h-9 w-9 overflow-hidden rounded-full border border-[#76C043] shadow-[0_0_12px_rgba(118,192,67,0.35)] bg-[#0B0D0E]">
              <Image
                src="/images/fitme-logo.png"
                alt="Fit Me"
                fill
                priority
                className="object-cover"
              />
            </div>
            <span className="text-xl font-bold tracking-tight text-white group-hover:text-[#76C043] transition-colors">
              Fit Me
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-6">
            {NAV_ITEMS.map((item) => {
              const isActive = activeSection === item.href.replace("#", "");
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`relative text-xs font-medium tracking-wide transition-colors duration-200 py-1 ${
                    isActive
                      ? "text-[#76C043]"
                      : "text-[#9CA3AF] hover:text-[#F8FAFC]"
                  }`}
                >
                  {item.name}
                  {isActive && (
                    <span className="absolute -bottom-1 inset-x-0 h-0.5 bg-[#76C043] shadow-[0_0_8px_#76C043]" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Desktop Actions */}
          <div className="hidden sm:flex items-center gap-4">
            {/* Search Icon */}
            <button
              type="button"
              aria-label="Search"
              className="p-2 text-[#9CA3AF] hover:text-[#76C043] transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>

            <Link
              href="http://localhost:8000/login/"
              className="text-xs font-semibold text-[#9CA3AF] hover:text-[#F8FAFC] px-2 py-1 transition-colors"
            >
              Member Login
            </Link>

            <Link
              href="#pricing"
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#76C043] hover:bg-[#85D538] text-black text-xs font-bold shadow-[0_0_20px_rgba(118,192,67,0.35)] transition-all hover:scale-105 active:scale-95"
            >
              <span>Join Now</span>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>

          {/* Mobile Hamburger Button */}
          <div className="flex items-center gap-3 sm:hidden">
            <button
              type="button"
              onClick={() => setIsMobileMenuOpen(true)}
              aria-label="Open mobile navigation"
              className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#2D3339] bg-[#121517] text-[#9CA3AF] transition-colors hover:text-[#F8FAFC] hover:border-[#76C043]"
            >
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Drawer */}
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        navItems={NAV_ITEMS}
        activeSection={activeSection}
      />
    </>
  );
}

export default FitMeHeader;
