import React from "react";
import Image from "next/image";
import Link from "next/link";
import { NAV_ITEMS } from "./navigation";

export function FitMeFooter() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full bg-[#08090A] border-t border-[#2D3339] text-[#9CA3AF]">
      <div className="max-w-[1750px] mx-auto px-4 sm:px-8 lg:px-14 xl:px-20 py-16 sm:py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 lg:gap-8">
          {/* Brand Col (2 cols on lg) */}
          <div className="lg:col-span-2">
            <Link href="#hero" className="flex items-center gap-3.5 group">
              <div className="relative h-11 w-11 overflow-hidden rounded-lg border border-[#2D3339] bg-[#121517]">
                <Image
                  src="/images/fitme-official-logo.jpg"
                  alt="Fit Me Logo"
                  fill
                  className="object-cover"
                />
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-black tracking-widest text-[#F8FAFC]">
                  FIT ME
                </span>
                <span className="text-[10px] font-bold tracking-widest text-[#76C043] uppercase">
                  Train with Purpose & Move with Confidence
                </span>
              </div>
            </Link>

            <p className="mt-5 text-sm leading-relaxed text-[#9CA3AF] max-w-sm">
              A premier modern athletic training sanctuary in Pitigala dedicated
              to structured biomechanics, Olympic lifting, sustainable nutrition,
              and measurable transformation.
            </p>

            {/* Social Icons */}
            <div className="mt-6 flex items-center gap-4">
              <a
                href="https://instagram.com"
                target="_blank"
                rel="noreferrer"
                aria-label="Instagram"
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#2D3339] bg-[#121517] text-[#9CA3AF] hover:text-[#76C043] hover:border-[#76C043] transition-colors"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
                </svg>
              </a>
              <a
                href="https://facebook.com"
                target="_blank"
                rel="noreferrer"
                aria-label="Facebook"
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#2D3339] bg-[#121517] text-[#9CA3AF] hover:text-[#76C043] hover:border-[#76C043] transition-colors"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M22.675 0h-21.35c-.732 0-1.325.593-1.325 1.325v21.351c0 .731.593 1.324 1.325 1.324h11.495v-9.294h-3.128v-3.622h3.128v-2.671c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.795.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.313h3.587l-.467 3.622h-3.12v9.293h6.116c.73 0 1.323-.593 1.323-1.325v-21.35c0-.732-.593-1.325-1.325-1.325z" />
                </svg>
              </a>
              <a
                href="https://wa.me/94707627878"
                target="_blank"
                rel="noreferrer"
                aria-label="WhatsApp"
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#2D3339] bg-[#121517] text-[#9CA3AF] hover:text-[#76C043] hover:border-[#76C043] transition-colors"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981z" />
                </svg>
              </a>
            </div>
          </div>

          {/* Navigation Links */}
          <div>
            <h4 className="text-xs font-mono font-bold uppercase tracking-widest text-[#F8FAFC]">
              Navigation
            </h4>
            <ul className="mt-4 space-y-2.5 text-sm">
              {NAV_ITEMS.map((item) => (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className="hover:text-[#76C043] transition-colors"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact Information (Pitigala) */}
          <div>
            <h4 className="text-xs font-mono font-bold uppercase tracking-widest text-[#F8FAFC]">
              Pitigala Arena
            </h4>
            <div className="mt-4 space-y-3 text-sm">
              <p className="leading-relaxed text-[#9CA3AF]">
                Fit Me Arena <br />
                New Town, Elpitiya Road, <br />
                Pitigala, 80420
              </p>
              <p>
                <span className="block text-xs font-mono text-[#76C043]">
                  Direct Hotline
                </span>
                <a
                  href="tel:0707627878"
                  className="font-bold text-[#F8FAFC] hover:text-[#76C043] transition-colors"
                >
                  070 762 7878
                </a>
              </p>
              <p className="text-xs font-mono text-[#9CA3AF]">
                Open Daily: 05:30 AM – 09:30 PM
              </p>
            </div>
          </div>

          {/* Member Access Portal Links */}
          <div>
            <h4 className="text-xs font-mono font-bold uppercase tracking-widest text-[#F8FAFC]">
              Portals
            </h4>
            <ul className="mt-4 space-y-2.5 text-sm">
              <li>
                <Link
                  href="/dashboard/member/"
                  className="hover:text-[#76C043] transition-colors flex items-center gap-1.5"
                >
                  <span>Member Dashboard</span>
                  <span className="text-[10px] text-[#76C043] font-mono">→</span>
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard/coach/"
                  className="hover:text-[#76C043] transition-colors"
                >
                  Coach Portal
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard/admin/"
                  className="hover:text-[#76C043] transition-colors"
                >
                  Admin Console
                </Link>
              </li>
              <li>
                <Link
                  href="/user/login"
                  className="hover:text-[#76C043] transition-colors"
                >
                  Sign In
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Legal Row */}
        <div className="mt-16 pt-8 border-t border-[#2D3339] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-[#9CA3AF]">
          <p>© {currentYear} FIT ME PVT LTD. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <Link href="#faq" className="hover:text-[#76C043] transition-colors">
              Privacy Policy
            </Link>
            <Link href="#faq" className="hover:text-[#76C043] transition-colors">
              Terms of Membership
            </Link>
            <Link href="#faq" className="hover:text-[#76C043] transition-colors">
              Facility Rules
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default FitMeFooter;
