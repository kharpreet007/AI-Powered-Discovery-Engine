"use client";
import Topbar from "@/components/Topbar";
import { useState, useEffect } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function PipelinePage() {
  const [status, setStatus] = useState<any>(null);
  const [dbStats, setDbStats] = useState<any>(null);
  
  const [adminToken, setAdminToken] = useState("dev_token_123");

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_URL}/api/stats`, {
        headers: { "Authorization": `Bearer ${adminToken}` }
      });
      if (res.ok) setDbStats(await res.json());
    } catch (e) {}
  };

  const pollStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/ingest/status`, {
        headers: { "Authorization": `Bearer ${adminToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStats();
    pollStatus();
    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const triggerPipeline = async (demo: boolean) => {
    try {
      const res = await fetch(`${API_URL}/api/ingest`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${adminToken}`
        },
        body: JSON.stringify({ mode: demo ? "demo" : "full" })
      });
      if (!res.ok) {
        alert("Failed to start pipeline: " + res.statusText);
      }
      pollStatus();
    } catch (e) {
      console.error(e);
      alert("Failed to start pipeline");
    }
  };

  const getStagePercent = () => {
    if (!status) return 0;
    if (status.status === "completed") return 100;
    if (status.status === "idle" || status.status === "failed") return 0;
    return (status.progress / (status.total_steps || 4)) * 100;
  };

  const isStageActive = (stageName: string) => {
    if (!status?.is_ingesting) return false;
    const stageMap: any = { 'Extraction': 'fetching', 'Cleaning': 'cleaning', 'Relevance Filtering': 'extracting', 'Embedding': 'embedding' };
    return status.status === stageMap[stageName];
  };

  const isStageComplete = (stageIndex: number) => {
    if (!status) return false;
    if (status.status === 'completed') return true;
    const currentIndex = status.progress || 0;
    return stageIndex < currentIndex;
  };

  return (
    <>
      <Topbar title="Pipeline Flow" />
      <main className="md:pl-64 pt-24 min-h-screen relative overflow-hidden pb-20 md:pb-0">
        <div className="bg-bloom top-[-10%] left-[-10%]"></div>
        <div className="bg-bloom bottom-[-10%] right-[-10%]"></div>
        <div className="max-w-[1400px] mx-auto px-container-padding relative z-10 pb-12">
          
          <div className="flex justify-between items-end mb-12">
            <div>
              <h1 className="font-display-lg text-[48px] text-white mb-2">Pipeline Control Panel</h1>
              <p className="text-on-surface-variant font-body-lg">Command center for real-time data ingestion and intelligence orchestration.</p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <div className="flex items-center gap-4 glass-panel px-4 py-2 rounded-full">
                <span className={`w-3 h-3 rounded-full ${status?.is_ingesting ? 'bg-primary-container animate-pulse shadow-[0_0_8px_#F8CB46]' : 'bg-surface-variant'}`}></span>
                <span className="text-label-caps text-primary-container font-bold tracking-widest uppercase">
                  {status?.is_ingesting ? 'System Live' : 'System Idle'}
                </span>
                <span className="text-on-surface-variant text-body-sm opacity-50 ml-2">Uptime: 99.98%</span>
              </div>
              <div className="text-on-surface-variant text-body-sm">
                <span className="font-bold">Last Sync:</span> {dbStats?.last_updated || 'Just Now'}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-12 gap-card-gap">
            {/* Left Column: Controls & Log */}
            <section className="col-span-12 lg:col-span-4 flex flex-col gap-card-gap">
              
              {/* Trigger Actions */}
              <div className="glass-panel p-8 rounded-2xl">
                <div className="flex items-center gap-3 mb-6">
                  <span className="material-symbols-outlined text-primary-container">rocket_launch</span>
                  <h2 className="font-title-md text-[20px] text-white">Manual Triggers</h2>
                </div>
                <div className="grid grid-cols-1 gap-6">
                  <div className="bg-white/5 border border-white/10 p-4 rounded-xl flex flex-col gap-2">
                    <label className="text-on-surface-variant text-[10px] uppercase tracking-widest font-bold">Admin Token</label>
                    <input 
                      type="password" 
                      value={adminToken} 
                      onChange={(e) => setAdminToken(e.target.value)}
                      className="bg-black/20 border border-white/10 rounded-lg p-2 text-white text-sm outline-none focus:border-primary-container transition-colors"
                      placeholder="Enter admin token..."
                    />
                  </div>
                  <button onClick={() => triggerPipeline(true)} disabled={status?.is_ingesting} className="group relative overflow-hidden bg-white/5 border border-white/10 p-6 rounded-xl text-left hover:bg-white/10 transition-all active:scale-95 disabled:opacity-50 cursor-pointer">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-primary-container font-title-md text-[20px]">Quick Demo Ingestion</span>
                      <span className="material-symbols-outlined opacity-0 group-hover:opacity-100 transition-opacity">bolt</span>
                    </div>
                    <p className="text-body-sm text-on-surface-variant">Process limited sample records for rapid testing.</p>
                  </button>
                  <button onClick={() => triggerPipeline(false)} disabled={status?.is_ingesting} className="group relative overflow-hidden bg-primary-container p-6 rounded-xl text-left text-on-primary-container hover:brightness-110 shadow-lg shadow-primary-container/20 transition-all active:scale-95 disabled:opacity-50 cursor-pointer">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-title-md text-[20px] font-bold">Full Pipeline Ingestion</span>
                      <span className="material-symbols-outlined">database</span>
                    </div>
                    <p className="text-body-sm opacity-80">Orchestrate end-to-end processing for the entire data warehouse.</p>
                  </button>
                </div>
              </div>

              {/* Activity Log / Raw Stream */}
              <div className="glass-panel rounded-2xl overflow-hidden flex-grow flex flex-col">
                <div className="px-8 py-4 bg-white/5 flex justify-between items-center border-b border-white/10">
                  <h3 className="font-title-md text-[20px] text-white">Live Operations Log</h3>
                  <div className="flex gap-4">
                    <button className="text-body-sm text-on-surface-variant hover:text-white cursor-pointer">Clear</button>
                  </div>
                </div>
                <div className="p-6 font-mono text-[12px] flex-grow overflow-y-auto space-y-1 bg-black/40 flex flex-col-reverse h-48">
                  {status?.logs?.length > 0 ? (
                    [...status.logs].reverse().map((logStr: string, idx: number) => {
                      const parts = logStr.split('|');
                      if (parts.length < 3) return (
                         <div key={idx} className="flex gap-4 text-on-surface-variant/40"><span className="text-on-surface">{logStr}</span></div>
                      );
                      const time = parts[0].split(' ')[1]?.split(',')[0] || parts[0];
                      const level = parts[1];
                      const msg = parts.slice(2).join('|');

                      let levelColor = "text-on-surface";
                      if (level === "INFO") levelColor = "text-tertiary-container";
                      if (level === "WARNING") levelColor = "text-yellow-400";
                      if (level === "ERROR") levelColor = "text-error";

                      return (
                        <div key={idx} className="flex gap-4 text-on-surface-variant/40">
                          <span className="w-[70px] flex-shrink-0">[{time}]</span>
                          <span className={`w-[60px] flex-shrink-0 ${levelColor}`}>{level}</span>
                          <span className="text-on-surface">{msg}</span>
                        </div>
                      );
                    })
                  ) : (
                    <div className="flex gap-4 text-on-surface-variant/40">
                      <span className="text-on-surface">Awaiting pipeline initialization... System ready.</span>
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* Workflow Visualization */}
            <section className="col-span-12 lg:col-span-8">
              <div className="glass-panel p-8 rounded-2xl h-full flex flex-col">
                <div className="flex justify-between items-center mb-12">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary-container">account_tree</span>
                    <h2 className="font-title-md text-[20px] text-white">Live Workflow Visualization</h2>
                  </div>
                  <div className="text-right">
                    <div className="text-label-caps text-on-surface-variant opacity-50 mb-1 tracking-widest uppercase text-xs">CURRENT STATUS</div>
                    <div className="text-primary-container font-bold tracking-widest text-title-md flex items-center justify-end gap-2 uppercase">
                      <span className={status?.is_ingesting ? "animate-pulse" : ""}>{status?.status || 'IDLE'}</span>
                      {status?.is_ingesting && <span className="material-symbols-outlined text-sm animate-spin" style={{fontVariationSettings: "'wght' 700"}}>sync</span>}
                    </div>
                  </div>
                </div>

                <div className="relative flex-grow flex flex-col justify-center gap-16 py-12">
                  <div className="absolute inset-0 opacity-10 pointer-events-none overflow-hidden"></div>
                  
                  <div className="relative">
                    <div className="pipeline-track mb-12">
                      <div className="pipeline-fill" style={{width: `${getStagePercent()}%`}}></div>
                    </div>
                    
                    <div className="grid grid-cols-4 gap-4 relative z-10">
                      
                      {/* Fetching */}
                      <div className="text-center group">
                        <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-4 transition-all ${isStageActive('Extraction') || isStageComplete(0) ? 'bg-primary-container text-on-primary-container shadow-[0_0_15px_#F8CB46]' : 'border border-white/20 text-on-surface-variant'}`}>
                          <span className="material-symbols-outlined" style={{fontVariationSettings: isStageComplete(0) ? "'FILL' 1" : "'FILL' 0"}}>cloud_download</span>
                        </div>
                        <div className={`text-label-caps font-bold transition-colors uppercase tracking-widest text-xs ${isStageActive('Extraction') || isStageComplete(0) ? 'text-on-surface-variant group-hover:text-white' : 'text-on-surface-variant/40'}`}>Fetching</div>
                        <div className="text-[10px] text-primary-container/60 mt-1">{isStageComplete(0) ? 'Complete' : isStageActive('Extraction') ? 'In Progress' : 'Queued'}</div>
                      </div>

                      {/* Cleaning */}
                      <div className="text-center group">
                        <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-4 transition-all ${isStageActive('Cleaning') || isStageComplete(1) ? 'bg-primary-container text-on-primary-container shadow-[0_0_15px_#F8CB46]' : 'border border-white/20 text-on-surface-variant'}`}>
                          <span className="material-symbols-outlined" style={{fontVariationSettings: isStageComplete(1) ? "'FILL' 1" : "'FILL' 0"}}>cleaning_services</span>
                        </div>
                        <div className={`text-label-caps font-bold transition-colors uppercase tracking-widest text-xs ${isStageActive('Cleaning') || isStageComplete(1) ? 'text-on-surface-variant group-hover:text-white' : 'text-on-surface-variant/40'}`}>Cleaning</div>
                        <div className="text-[10px] text-primary-container/60 mt-1">{isStageComplete(1) ? 'Complete' : isStageActive('Cleaning') ? 'In Progress' : 'Queued'}</div>
                      </div>

                      {/* Extracting (Relevance) */}
                      <div className={`text-center group relative ${!isStageActive('Relevance Filtering') && !isStageComplete(2) ? 'opacity-40' : ''}`}>
                        <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-4 transition-all ${isStageActive('Relevance Filtering') ? 'w-16 h-16 -mt-2 bg-surface-container-high border-2 border-primary-container text-primary-container shadow-[0_0_25px_rgba(248,203,70,0.4)] animate-pulse-subtle' : isStageComplete(2) ? 'bg-primary-container text-on-primary-container shadow-[0_0_15px_#F8CB46]' : 'border border-white/20 text-on-surface-variant'}`}>
                          <span className={`material-symbols-outlined ${isStageActive('Relevance Filtering') ? 'text-2xl' : ''}`} style={{fontVariationSettings: isStageActive('Relevance Filtering') || isStageComplete(2) ? "'FILL' 1" : "'FILL' 0"}}>auto_awesome</span>
                        </div>
                        <div className={`text-label-caps font-bold transition-all uppercase tracking-widest text-xs ${isStageActive('Relevance Filtering') ? 'text-primary-container active-stage group-hover:brightness-125' : 'text-on-surface-variant group-hover:text-white'}`}>Extracting</div>
                        <div className={`text-[10px] mt-1 ${isStageActive('Relevance Filtering') ? 'text-primary-container font-medium' : isStageComplete(2) ? 'text-primary-container/60' : 'text-on-surface-variant/40'}`}>{isStageComplete(2) ? 'Complete' : isStageActive('Relevance Filtering') ? 'In Progress' : 'Queued'}</div>
                        {isStageActive('Relevance Filtering') && <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-px h-12 bg-gradient-to-t from-primary-container to-transparent opacity-50"></div>}
                      </div>

                      {/* Embedding */}
                      <div className={`text-center group ${!isStageActive('Embedding') && !isStageComplete(3) ? 'opacity-40' : ''}`}>
                        <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-4 transition-all ${isStageActive('Embedding') || isStageComplete(3) ? 'bg-primary-container text-on-primary-container shadow-[0_0_15px_#F8CB46]' : 'border border-white/20 text-on-surface-variant'}`}>
                          <span className="material-symbols-outlined" style={{fontVariationSettings: "'FILL' 0"}}>layers</span>
                        </div>
                        <div className={`text-label-caps font-bold transition-colors uppercase tracking-widest text-xs ${isStageActive('Embedding') || isStageComplete(3) ? 'text-on-surface-variant group-hover:text-white' : 'text-on-surface-variant/40'}`}>Embedding</div>
                        <div className={`text-[10px] mt-1 ${isStageComplete(3) ? 'text-primary-container/60' : isStageActive('Embedding') ? 'text-primary-container font-medium' : 'text-on-surface-variant/40'}`}>{isStageComplete(3) ? 'Complete' : isStageActive('Embedding') ? 'In Progress' : 'Queued'}</div>
                      </div>

                    </div>
                  </div>
                </div>

                <div className="mt-auto pt-12 border-t border-white/5">
                  <h3 className="font-title-md text-[16px] text-white mb-6 uppercase tracking-widest opacity-80 flex items-center gap-2"><span className="material-symbols-outlined text-sm">speed</span> Run Meter</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {['playstore', 'appstore', 'youtube', 'reddit'].map((source) => {
                      const stats = dbStats?.volume_funnel?.sources?.[source] || { raw: 0, clean: 0, embedded: 0 };
                      
                      const icons: any = {
                        playstore: { icon: 'shop', color: 'text-green-400', bg: 'bg-green-500/10' },
                        appstore: { icon: 'phone_iphone', color: 'text-blue-400', bg: 'bg-blue-500/10' },
                        youtube: { icon: 'play_circle', color: 'text-red-500', bg: 'bg-red-500/10' },
                        reddit: { icon: 'forum', color: 'text-orange-500', bg: 'bg-orange-500/10' }
                      };
                      const config = icons[source];

                      return (
                        <div key={source} className="glass-panel p-4 rounded-xl border border-white/5 hover:border-white/20 transition-all flex flex-col h-full gap-4">
                          <div className="flex items-center gap-2 h-10">
                            <div className={`w-8 h-8 flex-shrink-0 rounded-lg ${config.bg} ${config.color} flex items-center justify-center`}>
                              <span className="material-symbols-outlined text-sm">{config.icon}</span>
                            </div>
                            <span className="text-white font-bold capitalize tracking-wide text-sm leading-tight">{source === 'appstore' ? 'App Store' : source === 'playstore' ? 'Play Store' : source}</span>
                          </div>
                          
                          <div className="flex flex-col gap-3 mt-auto">
                            <div className="flex justify-between items-center border-b border-white/5 pb-2">
                              <span className="text-on-surface-variant text-[10px] uppercase tracking-widest font-bold opacity-60">Extracted</span>
                              <span className="text-white font-mono text-base">{stats.raw}</span>
                            </div>
                            <div className="flex justify-between items-center border-b border-white/5 pb-2">
                              <span className="text-on-surface-variant text-[10px] uppercase tracking-widest font-bold opacity-60">Cleaned</span>
                              <span className="text-white font-mono text-base">{stats.clean}</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-primary-container text-[10px] uppercase tracking-widest font-bold opacity-80">Embedded</span>
                              <span className="text-primary-container font-mono text-base font-bold">{stats.embedded}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </section>



          </div>
        </div>
      </main>
    </>
  );
}
