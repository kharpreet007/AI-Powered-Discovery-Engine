"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 z-50 bg-surface/20 backdrop-blur-2xl border-r border-white/10 shadow-2xl flex-col py-8 px-4 gap-y-6 hidden md:flex">
        <div className="flex items-center gap-3 px-6 py-6 border-b border-white/5">
          <img alt="Blinkit Power BI Logo" className="w-10 h-10 object-contain rounded-xl" src="https://upload.wikimedia.org/wikipedia/commons/2/2f/Blinkit-yellow-app-icon.svg"/>
          <div>
            <h1 className="text-white font-title-lg text-[22px] tracking-tight leading-tight">Blinkit</h1>
            <p className="text-[10px] text-on-surface-variant tracking-widest uppercase">Power BI</p>
          </div>
        </div>
        <button className="mt-4 py-3 px-4 bg-primary-container text-on-primary-container font-bold rounded-xl flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-95 animate-engine cursor-pointer">
          <span className="material-symbols-outlined">add</span>
          New Analysis
        </button>
        <nav className="flex flex-col gap-1 mt-6">
          <Link href="/" className={`${pathname === '/' ? 'bg-primary-container/10 text-primary-container border-l-4 border-primary-container' : 'text-on-surface-variant hover:bg-white/5 hover:text-on-surface'} flex items-center gap-3 py-3 px-4 animate-engine`}>
            <span className="material-symbols-outlined" style={pathname === '/' ? {fontVariationSettings: "'FILL' 1"} : {}}>dashboard</span>
            <span className="font-label-caps text-label-caps tracking-widest uppercase text-xs">Dashboard</span>
          </Link>
          <Link href="/pipeline" className={`${pathname === '/pipeline' ? 'bg-primary-container/10 text-primary-container border-l-4 border-primary-container' : 'text-on-surface-variant hover:bg-white/5 hover:text-on-surface'} flex items-center gap-3 py-3 px-4 animate-engine`}>
            <span className="material-symbols-outlined" style={pathname === '/pipeline' ? {fontVariationSettings: "'FILL' 1"} : {}}>settings_input_component</span>
            <span className="font-label-caps text-label-caps tracking-widest uppercase text-xs">Pipeline</span>
          </Link>
          <Link href="/chat" className={`${pathname === '/chat' ? 'bg-primary-container/10 text-primary-container border-l-4 border-primary-container' : 'text-on-surface-variant hover:bg-white/5 hover:text-on-surface'} flex items-center gap-3 py-3 px-4 animate-engine`}>
            <span className="material-symbols-outlined" style={pathname === '/chat' ? {fontVariationSettings: "'FILL' 1"} : {}}>forum</span>
            <span className="font-label-caps text-label-caps tracking-widest uppercase text-xs">Chat</span>
          </Link>
        </nav>
        <div className="mt-auto flex flex-col gap-1">
          <Link href="/workflow-analyzer" className={`${pathname === '/workflow-analyzer' ? 'bg-primary-container/10 text-primary-container border-l-4 border-primary-container' : 'text-on-surface-variant hover:bg-white/5 hover:text-on-surface'} flex items-center gap-3 py-3 px-4 animate-engine`}>
            <span className="material-symbols-outlined" style={pathname === '/workflow-analyzer' ? {fontVariationSettings: "'FILL' 1"} : {}}>analytics</span>
            <span className="font-label-caps text-label-caps tracking-widest uppercase text-xs">Workflow Analyzer</span>
          </Link>
        </div>
      </aside>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full h-16 bg-[#1A1A1A] border-t border-white/10 z-50 flex items-center justify-around px-2 shadow-[0_-4px_20px_rgba(0,0,0,0.5)]">
        <Link href="/" className={`flex flex-col items-center justify-center w-full h-full ${pathname === '/' ? 'text-primary-container' : 'text-on-surface-variant'}`}>
          <span className="material-symbols-outlined" style={pathname === '/' ? {fontVariationSettings: "'FILL' 1"} : {}}>dashboard</span>
          <span className="text-[10px] mt-1 font-medium">Dashboard</span>
        </Link>
        <Link href="/pipeline" className={`flex flex-col items-center justify-center w-full h-full ${pathname === '/pipeline' ? 'text-primary-container' : 'text-on-surface-variant'}`}>
          <span className="material-symbols-outlined" style={pathname === '/pipeline' ? {fontVariationSettings: "'FILL' 1"} : {}}>settings_input_component</span>
          <span className="text-[10px] mt-1 font-medium">Pipeline</span>
        </Link>
        <Link href="/chat" className={`flex flex-col items-center justify-center w-full h-full ${pathname === '/chat' ? 'text-primary-container' : 'text-on-surface-variant'}`}>
          <span className="material-symbols-outlined" style={pathname === '/chat' ? {fontVariationSettings: "'FILL' 1"} : {}}>forum</span>
          <span className="text-[10px] mt-1 font-medium">Chat</span>
        </Link>
        <Link href="/workflow-analyzer" className={`flex flex-col items-center justify-center w-full h-full ${pathname === '/workflow-analyzer' ? 'text-primary-container' : 'text-on-surface-variant'}`}>
          <span className="material-symbols-outlined" style={pathname === '/workflow-analyzer' ? {fontVariationSettings: "'FILL' 1"} : {}}>analytics</span>
          <span className="text-[10px] mt-1 font-medium">Analyzer</span>
        </Link>
      </nav>
    </>
  );
}
