"use client";

import React, { useState } from "react";

export interface AccordionItemData {
  id: string;
  question: string;
  answer: string;
}

interface AccordionProps {
  items: AccordionItemData[];
  defaultOpenIndex?: number;
}

export function Accordion({ items, defaultOpenIndex }: AccordionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(
    defaultOpenIndex !== undefined ? defaultOpenIndex : 0
  );

  const toggle = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div className="divide-y divide-[#2D3339] border-y border-[#2D3339]">
      {items.map((item, index) => {
        const isOpen = openIndex === index;
        const buttonId = `faq-btn-${item.id}`;
        const panelId = `faq-panel-${item.id}`;

        return (
          <div key={item.id} className="group">
            <button
              id={buttonId}
              type="button"
              aria-expanded={isOpen}
              aria-controls={panelId}
              onClick={() => toggle(index)}
              className="flex w-full items-center justify-between py-6 text-left transition-colors duration-200 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#76C043]"
            >
              <span className={`text-base md:text-lg font-medium tracking-tight transition-colors duration-200 ${
                isOpen ? "text-[#76C043]" : "text-[#F8FAFC] group-hover:text-[#76C043]"
              }`}>
                {item.question}
              </span>
              <span className={`ml-4 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[#2D3339] bg-[#0E1012] transition-transform duration-300 ${
                isOpen ? "rotate-180 border-[#76C043] text-[#76C043]" : "text-[#9CA3AF] group-hover:border-[#76C043]/50"
              }`}>
                <svg
                  className="h-3.5 w-3.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </span>
            </button>

            <div
              id={panelId}
              role="region"
              aria-labelledby={buttonId}
              className={`overflow-hidden transition-all duration-300 ease-in-out ${
                isOpen ? "max-h-96 opacity-100 pb-6" : "max-h-0 opacity-0"
              }`}
            >
              <p className="text-sm md:text-base leading-relaxed text-[#9CA3AF] pr-8">
                {item.answer}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default Accordion;
