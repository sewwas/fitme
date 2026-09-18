"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { PrimaryButton } from "../ui/PrimaryButton";

interface NavItem {
  name: string;
  href: string;
}

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  navItems: NavItem[];
  activeSection: string;
}

export function MobileMenu({
  isOpen,
  onClose,
  navItems,
  activeSection,
}: MobileMenuProps) {
  // Prevent body scrolling when menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  // Keyboard Escape listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Navigation Menu"
      className="fixed inset-0 z-50 flex flex-col bg-[#0B0D0E] md:hidden"
    >
      {/* Top Header in Menu */}
      <div className="flex h-20 items-center justify-between px-6 border-b border-[#2D3339]">
        <div className="flex items-center gap-3">
          <div className="relative h-9 w-9 overflow-hidden rounded-md border border-[#2D3339]">
            <Image
              src="/images/fitme-official-logo.jpg"
              alt="Fit Me Logo"
              fill
              className="object-cover"
            />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-black tracking-wider text-[#F8FAFC]">
              FIT ME
            </span>
            <span className="text-[9px] font-bold tracking-widest text-[#76C043] uppercase">
              Train with Purpose
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label="Close navigation menu"
          className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#2D3339] text-[#9CA3AF] transition-colors hover:text-[#F8FAFC] hover:border-[#76C043]"
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
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-6 py-8">
        <ul className="flex flex-col space-y-4">
          {navItems.map((item, idx) => {
            const isActive = activeSection === item.href.replace("#", "");
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  onClick={onClose}
                  className={`flex items-center justify-between py-2 text-lg font-bold uppercase tracking-wider transition-colors duration-200 ${
                    isActive
                      ? "text-[#76C043]"
                      : "text-[#F8FAFC] hover:text-[#76C043]"
                  }`}
                >
                  <span>{item.name}</span>
                  <span className="font-mono text-xs text-[#9CA3AF]">
                    0{idx + 1}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Contact Info in Mobile Menu */}
        <div className="mt-10 rounded-xl border border-[#2D3339] bg-[#121517] p-5">
          <p className="text-xs uppercase tracking-widest text-[#76C043] font-mono mb-1">
            Pitigala Facility
          </p>
          <p className="text-xs text-[#9CA3AF] leading-relaxed">
            New Town, Elpitiya Road, Pitigala, 80420
          </p>
          <a
            href="tel:0707627878"
            className="mt-2 inline-flex items-center gap-2 text-sm font-bold text-[#F8FAFC] hover:text-[#76C043]"
          >
            <svg className="w-4 h-4 text-[#76C043]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            070 762 7878
          </a>
        </div>
      </nav>

      {/* Primary CTA in Mobile Menu */}
      <div className="p-6 border-t border-[#2D3339] bg-[#0E1012]">
        <PrimaryButton
          href="#membership"
          onClick={onClose}
          fullWidth
          size="lg"
        >
          Start Your Transformation
        </PrimaryButton>
      </div>
    </div>
  );
}

export default MobileMenu;
