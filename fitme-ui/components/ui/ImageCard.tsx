import React from "react";
import Image from "next/image";

interface ImageCardProps {
  title: string;
  subtitle: string;
  description: string;
  imageUrl: string;
  imageAlt: string;
  indexNumber: string;
}

export function ImageCard({
  title,
  subtitle,
  description,
  imageUrl,
  imageAlt,
  indexNumber,
}: ImageCardProps) {
  return (
    <div className="group relative h-[440px] w-full overflow-hidden rounded-xl border border-[#2D3339] bg-[#121517] transition-all duration-300 hover:border-[#76C043]/50 hover:shadow-[0_16px_40px_rgba(0,0,0,0.7)]">
      {/* Background Image with Zoom */}
      <Image
        src={imageUrl}
        alt={imageAlt}
        fill
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        className="object-cover transition-transform duration-700 ease-out group-hover:scale-105"
      />

      {/* Cinematic Overlays */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#0B0D0E] via-[#0B0D0E]/60 to-transparent" />
      <div className="absolute inset-0 bg-[#0B0D0E]/30 transition-opacity duration-300 group-hover:opacity-10" />

      {/* Number Badge */}
      <div className="absolute top-6 left-6 flex items-center gap-2">
        <span className="font-mono text-xs font-semibold tracking-widest text-[#76C043] bg-[#0B0D0E]/80 backdrop-blur-md px-2.5 py-1 rounded border border-[#2D3339]">
          {indexNumber}
        </span>
        <span className="text-xs uppercase tracking-widest text-[#9CA3AF] font-mono">
          {subtitle}
        </span>
      </div>

      {/* Content at Bottom */}
      <div className="absolute bottom-0 inset-x-0 p-6 md:p-8 flex flex-col justify-end">
        <h3 className="text-2xl font-bold tracking-tight text-[#F8FAFC] group-hover:text-[#76C043] transition-colors duration-200">
          {title}
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-[#9CA3AF]">
          {description}
        </p>
        <div className="mt-4 flex items-center gap-2 text-xs font-semibold tracking-widest uppercase text-[#76C043] opacity-0 translate-y-2 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0">
          <span>EXPLORE FACILITY</span>
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </div>
  );
}

export default ImageCard;
