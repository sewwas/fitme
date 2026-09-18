import React from "react";
import Link from "next/link";

interface PrimaryButtonProps {
  children: React.ReactNode;
  href?: string;
  onClick?: () => void;
  className?: string;
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  icon?: React.ReactNode;
}

export function PrimaryButton({
  children,
  href,
  onClick,
  className = "",
  size = "md",
  fullWidth = false,
  icon,
}: PrimaryButtonProps) {
  const sizeClasses = {
    sm: "px-4 py-2 text-xs",
    md: "px-6 py-3.5 text-sm",
    lg: "px-8 py-4 text-base",
  }[size];

  const baseClasses = `
    group relative inline-flex items-center justify-center gap-2.5 
    font-semibold tracking-wider uppercase 
    bg-[#76C043] text-[#0B0D0E] 
    transition-all duration-200 ease-out 
    hover:bg-[#88dc4f] hover:shadow-[0_0_24px_rgba(118,192,67,0.35)] 
    active:scale-[0.98] 
    focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#76C043] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0B0D0E]
    disabled:opacity-50 disabled:pointer-events-none
    ${fullWidth ? "w-full" : "w-auto"}
    ${sizeClasses}
    ${className}
  `;

  const content = (
    <>
      <span>{children}</span>
      {icon ? (
        <span className="transition-transform duration-200 group-hover:translate-x-1">
          {icon}
        </span>
      ) : (
        <svg
          className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M5 12h14M12 5l7 7-7 7" />
        </svg>
      )}
    </>
  );

  if (href) {
    return (
      <Link href={href} className={baseClasses}>
        {content}
      </Link>
    );
  }

  return (
    <button type="button" onClick={onClick} className={baseClasses}>
      {content}
    </button>
  );
}

export default PrimaryButton;
