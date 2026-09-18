"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { PrimaryButton } from "../ui/PrimaryButton";
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
          <Link
            href="#hero"
            className="flex items-center gap-3.5 group focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#76C043]"
          >
            <div className="relative h-10 w-10 overflow-hidden rounded-lg border border-[#2D3339] bg-[#121517] transition-all duration-200 group-hover:border-[#76C043]">
              <Image
                src="/images/fitme-official-logo.jpg"
                alt="Fit Me Logo"
                fill
                priority
                className="object-cover"
              />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-black tracking-widest text-[#F8FAFC] group-hover:text-[#76C043] transition-colors duration-200">
                FIT ME
              </span>
              <span className="text-[10px] font-semibold tracking-wider text-[#76C043] uppercase">
                Train with Purpose
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-7">
            {NAV_ITEMS.map((item) => {
              const isActive = activeSection === item.href.replace("#", "");
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`relative text-xs font-semibold uppercase tracking-widest transition-colors duration-200 py-1 ${
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

          {/* Desktop CTA Button */}
          <div className="hidden sm:flex items-center gap-4">
            <PrimaryButton
              href="#membership"
              size="sm"
              className="text-xs font-bold"
            >
              Start Your Transformation
            </PrimaryButton>
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
