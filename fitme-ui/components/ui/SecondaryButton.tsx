import React from "react";
import Link from "next/link";

interface SecondaryButtonProps {
  children: React.ReactNode;
  href?: string;
  onClick?: () => void;
  className?: string;
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  icon?: React.ReactNode;
}

export function SecondaryButton({
  children,
  href,
  onClick,
  className = "",
  size = "md",
  fullWidth = false,
  icon,
}: SecondaryButtonProps) {
  const sizeClasses = {
    sm: "px-4 py-2 text-xs",
    md: "px-6 py-3.5 text-sm",
    lg: "px-8 py-4 text-base",
  }[size];

  const baseClasses = `
    group relative inline-flex items-center justify-center gap-2.5 
    font-semibold tracking-wider uppercase 
    bg-[#121517] text-[#F8FAFC] 
    border border-[#2D3339] 
    transition-all duration-200 ease-out 
    hover:border-[#76C043]/60 hover:text-[#76C043] hover:bg-[#121517]/90 
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
      {icon && (
        <span className="transition-transform duration-200 group-hover:translate-x-1">
          {icon}
        </span>
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

export default SecondaryButton;
