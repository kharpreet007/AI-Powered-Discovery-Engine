"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Topbar({ title }: { title: string }) {
  const pathname = usePathname();

  return (
    <header className="fixed top-0 w-full z-40 bg-surface/10 backdrop-blur-xl border-b border-white/10 h-20 transition-all duration-300">
      <div className="flex justify-between items-center px-container-padding h-full max-w-[1600px] mx-auto md:pl-72">
        <div className="flex items-center gap-8">
          <h2 className="font-display-lg text-[32px] tracking-tighter text-primary-fixed hidden lg:block">{title}</h2>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative hidden sm:block">
            <input className="bg-white/5 border border-white/10 rounded-full py-2 pl-10 pr-4 text-sm focus:border-primary-container outline-none focus:ring-1 focus:ring-primary-container w-64 animate-engine text-on-surface placeholder:text-on-surface-variant/50" placeholder="Search insights..." type="text"/>
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">search</span>
          </div>
          <button className="material-symbols-outlined text-on-surface-variant hover:text-primary-container animate-engine cursor-pointer">notifications</button>
        </div>
      </div>
    </header>
  );
}
