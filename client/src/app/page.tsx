"use client";
import Topbar from "@/components/Topbar";
import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);

const CHART_COLORS = ['#FACC15', '#60A5FA', '#F87171', '#A78BFA', '#34D399', '#F472B6'];

function DonutChart({ data, title, totalLabel }: { data: any[], title: string, totalLabel?: string }) {
  if (!data || data.length === 0) return <div className="text-sm text-on-surface-variant h-32 flex items-center justify-center">No data</div>;
  
  let cumulativePercent = 0;
  
  return (
    <div className="flex flex-col h-full">
      <h4 className="text-on-surface-variant text-[12px] uppercase font-bold tracking-wider mb-4">{title}</h4>
      <div className="flex items-center gap-6 mt-auto">
        <div className="relative w-24 h-24 flex-shrink-0">
          <svg viewBox="0 0 42 42" className="w-full h-full -rotate-90">
            {/* Background circle */}
            <circle cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="rgba(255,255,255,0.05)" strokeWidth="6"></circle>
            {/* Data slices */}
            {data.map((item, i) => {
              const dashArray = `${item.percentage} ${100 - item.percentage}`;
              const dashOffset = 100 - cumulativePercent;
              cumulativePercent += item.percentage;
              return (
                <circle 
                  key={i}
                  cx="21" cy="21" r="15.91549430918954" 
                  fill="transparent" 
                  stroke={CHART_COLORS[i % CHART_COLORS.length]} 
                  strokeWidth="6"
                  strokeDasharray={dashArray}
                  strokeDashoffset={dashOffset}
                  className="transition-all duration-1000 ease-out hover:stroke-[8px]"
                ></circle>
              );
            })}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-white font-bold text-lg leading-none">{data[0]?.value || 0}</span>
            {totalLabel && <span className="text-[8px] text-on-surface-variant uppercase mt-1">{totalLabel}</span>}
          </div>
        </div>
        
        <div className="flex-1 min-w-0 flex flex-col justify-center space-y-2">
          {data.slice(0, 4).map((item, i) => (
            <div key={i} className="flex items-center gap-2 group/item">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}></span>
              <span className="text-white/90 text-[11px] line-clamp-2 leading-tight flex-1 group-hover/item:text-white transition-colors" title={item.name}>{item.name}</span>
              <span className="text-on-surface-variant font-mono text-[10px]">{item.percentage}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [sourceItems, setSourceItems] = useState<any[]>([]);
  const [isLoadingItems, setIsLoadingItems] = useState(false);
  const [expandedTheme, setExpandedTheme] = useState<string | null>(null);
  const [selectedThemeModal, setSelectedThemeModal] = useState<string | null>(null);
  const [themeItems, setThemeItems] = useState<any[]>([]);
  const [isLoadingThemeItems, setIsLoadingThemeItems] = useState(false);
  
  useEffect(() => {
    const fetchStats = () => {
      fetch(`${API_URL}/api/stats`)
        .then(res => res.json())
        .then(data => setStats(data))
        .catch(err => console.error(err));
    };
    
    // Initial fetch
    fetchStats();
    
    // Poll every 5 seconds for real-time updates
    const interval = setInterval(fetchStats, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const openSourceModal = async (source: string) => {
    setSelectedSource(source);
    setSourceItems([]);
    setIsLoadingItems(true);
    try {
      const res = await fetch(`${API_URL}/api/items/${source}`);
      if (res.ok) {
        const data = await res.json();
        setSourceItems(data.items || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingItems(false);
    }
  };

  const openThemeModal = async (themeObj: any) => {
    setSelectedThemeModal(themeObj.title);
    setThemeItems([]);
    setIsLoadingThemeItems(true);
    try {
      const res = await fetch(`${API_URL}/api/items/theme?barrier=${encodeURIComponent(themeObj.barrier)}&category=${encodeURIComponent(themeObj.category)}`);
      if (res.ok) {
        const data = await res.json();
        setThemeItems(data.items || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingThemeItems(false);
    }
  };

  return (
    <>
      <Topbar title="Insights Overview" />
      <main className="md:pl-64 pt-20 min-h-screen relative">
        <div className="bg-bloom top-[-10%] left-[-10%]"></div>
        <div className="bg-bloom bottom-[-10%] right-[-10%]"></div>
        
        <div className="max-w-[1600px] mx-auto px-container-padding py-8 space-y-8">
          {/* Hero Stats & Volume Funnel */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-gutter">
            <div className="lg:col-span-8 glass-panel rounded-xl p-8 overflow-hidden relative">
              <div className="flex justify-between items-start mb-10">
                <div>
                  <h3 className="font-headline-lg text-headline-lg text-white mb-2">Volume Funnel</h3>
                  <p className="text-on-surface-variant text-body-sm">Data processing stages from raw ingestion to theme classification.</p>
                </div>
                <div className="text-right">
                  <span className="text-primary-fixed font-bold text-[48px] font-display-lg leading-none">{stats?.total_items || 0}</span>
                  <p className="text-on-surface-variant text-[10px] tracking-widest uppercase mt-2">Tagged Themes</p>
                </div>
              </div>
              
              <div className="relative flex items-center justify-between gap-1 h-32 mt-4">
                <div className="flex-1 glass-panel h-full flex flex-col items-center justify-center relative overflow-hidden group">
                  <div className="absolute inset-0 bg-primary-container/5 translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
                  <span className="font-display-lg text-white text-[24px]">{stats?.volume_funnel?.total?.raw || 0}</span>
                  <span className="text-[10px] text-on-surface-variant uppercase font-bold tracking-tighter">Raw Data</span>
                </div>
                <div className="w-8 flex items-center justify-center">
                  <span className="material-symbols-outlined text-on-surface-variant">chevron_right</span>
                </div>
                <div className="flex-1 glass-panel h-full flex flex-col items-center justify-center relative overflow-hidden group">
                  <div className="absolute inset-0 bg-primary-container/10 translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
                  <span className="font-display-lg text-white text-[24px]">{stats?.volume_funnel?.total?.clean || 0}</span>
                  <span className="text-[10px] text-on-surface-variant uppercase font-bold tracking-tighter">Cleaned</span>
                </div>
                <div className="w-8 flex items-center justify-center">
                  <span className="material-symbols-outlined text-on-surface-variant">chevron_right</span>
                </div>
                <div className="flex-1 glass-panel h-full flex flex-col items-center justify-center relative overflow-hidden group">
                  <div className="absolute inset-0 bg-primary-container/15 translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
                  <span className="font-display-lg text-white text-[24px]">{stats?.volume_funnel?.total?.embedded || 0}</span>
                  <span className="text-[10px] text-on-surface-variant uppercase font-bold tracking-tighter">Embedded</span>
                </div>
                <div className="w-8 flex items-center justify-center">
                  <span className="material-symbols-outlined text-on-surface-variant">chevron_right</span>
                </div>
                <div className="flex-1 glass-panel h-full flex flex-col items-center justify-center relative border-primary-container/30 border-2 overflow-hidden group">
                  <div className="absolute inset-0 bg-primary-container/20 translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
                  <span className="font-display-lg text-primary-container text-[24px]">{stats?.volume_funnel?.total?.relevant || 0}</span>
                  <span className="text-[10px] text-primary-container uppercase font-bold tracking-tighter">Relevant</span>
                </div>
              </div>
            </div>

            <div className="lg:col-span-4 flex flex-col gap-gutter">
              <div className="glass-panel rounded-xl p-6 flex-1 flex flex-col justify-between group">
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant font-label-caps text-label-caps">Confidence Score</span>
                  <span className="material-symbols-outlined text-primary-container" style={{fontVariationSettings: "'FILL' 1"}}>verified</span>
                </div>
                <div className="mt-4">
                  <div className="text-[48px] font-display-lg text-white leading-none">94%</div>
                  <div className="w-full h-2 bg-white/10 rounded-full mt-4 overflow-hidden">
                    <div className="h-full bg-primary-container glow-yellow w-[94%] animate-engine origin-left"></div>
                  </div>
                </div>
                <p className="text-on-surface-variant text-body-sm mt-4">Statistically significant agreement across 12 unique LLM validation agents.</p>
              </div>
              <div className="glass-panel rounded-xl p-6 flex-1 flex flex-col justify-between">
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant font-label-caps text-label-caps">Citation Density</span>
                  <span className="material-symbols-outlined text-tertiary-container">link</span>
                </div>
                <div className="mt-4 flex items-end gap-2">
                  <div className="text-[48px] font-display-lg text-white leading-none">8.4</div>
                  <span className="text-on-surface-variant mb-2">refs / theme</span>
                </div>
                <div className="flex gap-1 mt-4">
                  <div className="h-1 flex-1 bg-tertiary-container/40"></div>
                  <div className="h-1 flex-1 bg-tertiary-container/60"></div>
                  <div className="h-1 flex-1 bg-tertiary-container/80"></div>
                  <div className="h-1 flex-1 bg-tertiary-container"></div>
                  <div className="h-1 flex-1 bg-white/10"></div>
                </div>
              </div>
            </div>
          </section>

          {/* Source Breakdown */}
          <section className="space-y-4">
            <div className="flex justify-between items-end">
              <h3 className="font-headline-lg text-headline-lg text-white">Source Breakdown</h3>
              <button className="text-primary-container text-body-sm hover:underline cursor-pointer">Manage Sources</button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-gutter">
              {/* YouTube */}
              <div onClick={() => openSourceModal('youtube')} className={`glass-panel rounded-xl p-6 relative overflow-hidden group cursor-pointer hover:border-primary-container/50 transition-opacity ${(stats?.source_counts?.youtube || 0) > 0 ? 'opacity-100' : 'opacity-60 hover:opacity-100'}`}>
                <div className="absolute -right-4 -top-4 w-24 h-24 bg-red-600/10 blur-3xl rounded-full transition-all group-hover:scale-150"></div>
                <div className="flex items-center gap-3 mb-6 relative z-10">
                  <div className="w-10 h-10 rounded-lg bg-red-600/20 flex items-center justify-center text-red-500">
                    <span className="material-symbols-outlined">play_circle</span>
                  </div>
                  <span className="font-title-md text-white">YouTube</span>
                </div>
                <div className="text-[32px] font-display-lg text-white relative z-10">{stats?.source_counts?.youtube || 0}</div>
                <p className="text-on-surface-variant text-[10px] uppercase font-bold relative z-10 mt-1">Comments Parsed</p>
              </div>
              
              {/* Play Store */}
              <div onClick={() => openSourceModal('playstore')} className={`glass-panel rounded-xl p-6 relative overflow-hidden group cursor-pointer hover:border-primary-container/50 transition-opacity ${(stats?.source_counts?.playstore || 0) > 0 ? 'opacity-100' : 'opacity-60 hover:opacity-100'}`}>
                <div className="absolute -right-4 -top-4 w-24 h-24 bg-green-500/10 blur-3xl rounded-full transition-all group-hover:scale-150"></div>
                <div className="flex items-center gap-3 mb-6 relative z-10">
                  <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center text-green-400">
                    <span className="material-symbols-outlined">replace_image</span>
                  </div>
                  <span className="font-title-md text-white">Play Store</span>
                </div>
                <div className="text-[32px] font-display-lg text-white relative z-10">{stats?.source_counts?.playstore || 0}</div>
                <p className="text-on-surface-variant text-[10px] uppercase font-bold relative z-10 mt-1">Reviews Scanned</p>
              </div>

              {/* Reddit */}
              <div onClick={() => openSourceModal('reddit')} className={`glass-panel rounded-xl p-6 relative overflow-hidden group cursor-pointer hover:border-primary-container/50 transition-opacity ${(stats?.source_counts?.reddit || 0) > 0 ? 'opacity-100' : 'opacity-60 hover:opacity-100'}`}>
                <div className="flex items-center gap-3 mb-6 relative z-10">
                  <div className="w-10 h-10 rounded-lg bg-orange-600/10 flex items-center justify-center text-orange-400">
                    <span className="material-symbols-outlined">forum</span>
                  </div>
                  <span className="font-title-md text-white">Reddit</span>
                </div>
                <div className="text-[32px] font-display-lg text-white relative z-10">{stats?.source_counts?.reddit || 0}</div>
                <p className="text-on-surface-variant text-[10px] uppercase font-bold relative z-10 mt-1">Posts Scanned</p>
              </div>

              {/* App Store */}
              <div onClick={() => openSourceModal('appstore')} className={`glass-panel rounded-xl p-6 relative overflow-hidden group cursor-pointer hover:border-primary-container/50 transition-opacity ${(stats?.source_counts?.appstore || 0) > 0 ? 'opacity-100' : 'opacity-60 hover:opacity-100'}`}>
                <div className="flex items-center gap-3 mb-6 relative z-10">
                  <div className="w-10 h-10 rounded-lg bg-blue-400/10 flex items-center justify-center text-blue-300">
                    <span className="material-symbols-outlined">file_download</span>
                  </div>
                  <span className="font-title-md text-white">App Store</span>
                </div>
                <div className="text-[32px] font-display-lg text-white relative z-10">{stats?.source_counts?.appstore || 0}</div>
                <p className="text-on-surface-variant text-[10px] uppercase font-bold relative z-10 mt-1">Reviews Scanned</p>
              </div>
            </div>
          </section>

          {/* Emergent Themes Panel */}
          <section className="space-y-4">
            <div className="flex justify-between items-end">
              <div>
                <h3 className="font-headline-lg text-headline-lg text-white flex items-baseline gap-3">
                  Emergent Themes 
                  <span className="text-[20px] text-on-surface-variant/60 font-normal tracking-normal">(What&apos;s happening)</span>
                </h3>
                <p className="text-on-surface-variant text-body-sm">AI-identified clusters with high frequency and impact.</p>
              </div>
              <div className="flex gap-2">
                <button className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg hover:border-primary-container text-body-sm animate-engine cursor-pointer">Export CSV</button>
                <button className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg hover:border-primary-container text-body-sm animate-engine cursor-pointer">Sort: Impact</button>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 items-start">
              {stats?.emergent_themes ? (
                stats.emergent_themes.map((themeObj: any, idx: number) => {
                  return (
                    <div key={idx} className="glass-panel rounded-xl p-6 group cursor-pointer animate-engine hover:border-primary-container/30 transition-all flex flex-col h-full">
                      <div className="flex justify-between items-start mb-4">
                        <div className="px-3 py-1 bg-primary-container/20 border border-primary-container/40 rounded-full text-[10px] text-primary-container font-bold uppercase tracking-wider">Dynamic Theme</div>
                      </div>
                      <h4 className="font-headline-lg text-[20px] text-white mb-2">{themeObj.title}</h4>
                      <p className="text-on-surface-variant text-body-sm mb-6">{themeObj.description}</p>
                      
                      <div className="flex items-center justify-between mt-auto">
                        <div className="text-right cursor-pointer group/mentions ml-auto" onClick={(e) => { e.stopPropagation(); openThemeModal(themeObj); }}>
                          <span className="text-white font-bold text-sm group-hover/mentions:underline decoration-primary-container underline-offset-4">{themeObj.mentions} Mentions</span>
                          <div className="w-24 h-1.5 bg-white/10 rounded-full mt-2 ml-auto">
                            <div className="h-full bg-primary-container w-[75%] rounded-full"></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="col-span-full text-center text-on-surface-variant py-8 animate-pulse">Loading dynamic themes...</div>
              )}
            </div>
          </section>

          {/* Sneak Peek Insights Panel */}
          <section className="space-y-4 mt-8">
            <div className="flex justify-between items-end">
              <div>
                <h3 className="font-headline-lg text-headline-lg text-white flex items-baseline gap-3">
                  Sneak Peek Insights
                  <span className="text-[20px] text-on-surface-variant/60 font-normal tracking-normal">(Quick Category Intelligence)</span>
                </h3>
                <p className="text-on-surface-variant text-body-sm">High-level categorical analysis extracted from user feedback.</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-start">
              {stats?.sneak_peek ? (
                <>
                  <div className="glass-panel rounded-xl p-6 group animate-engine hover:border-[#FACC15]/30 transition-all flex flex-col h-full border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                      <span className="material-symbols-outlined text-[64px] text-[#FACC15]">workspace_premium</span>
                    </div>
                    <DonutChart data={stats.sneak_peek.most_popular} title="Most Popular Categories" totalLabel="Leading" />
                  </div>

                  <div className="glass-panel rounded-xl p-6 group animate-engine hover:border-[#60A5FA]/30 transition-all flex flex-col h-full border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                      <span className="material-symbols-outlined text-[64px] text-[#60A5FA]">shopping_bag</span>
                    </div>
                    <DonutChart data={stats.sneak_peek.top_behaviors} title="Top Shopping Behaviors" totalLabel="Mentions" />
                  </div>

                  <div className="glass-panel rounded-xl p-6 group animate-engine hover:border-[#F87171]/30 transition-all flex flex-col h-full border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                      <span className="material-symbols-outlined text-[64px] text-[#F87171]">explore</span>
                    </div>
                    <DonutChart data={stats.sneak_peek.shopping_intent} title="Shopping Intent" totalLabel="Mentions" />
                  </div>

                  <div className="glass-panel rounded-xl p-6 group animate-engine hover:border-[#A78BFA]/30 transition-all flex flex-col h-full border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                      <span className="material-symbols-outlined text-[64px] text-[#A78BFA]">bolt</span>
                    </div>
                    <DonutChart data={stats.sneak_peek.purchase_drivers} title="Purchase Drivers" totalLabel="Mentions" />
                  </div>
                </>
              ) : (
                <div className="col-span-full text-center text-on-surface-variant py-8 animate-pulse">Loading sneak peek insights...</div>
              )}
            </div>
          </section>

        </div>
      </main>

      {/* Raw Data Modal */}
      {selectedSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm cursor-pointer" onClick={() => setSelectedSource(null)}></div>
          <div className="relative bg-surface-container-high border border-white/10 rounded-2xl w-full max-w-3xl max-h-[80vh] flex flex-col shadow-2xl">
            <div className="p-6 border-b border-white/10 flex justify-between items-center">
              <h3 className="text-white font-headline-lg text-2xl capitalize">{selectedSource} Raw Data</h3>
              <button onClick={() => setSelectedSource(null)} className="text-on-surface-variant hover:text-white cursor-pointer">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-grow flex flex-col gap-4">
              {isLoadingItems ? (
                <div className="text-center text-on-surface-variant py-8 animate-pulse">Loading items...</div>
              ) : sourceItems.length === 0 ? (
                <div className="text-center text-on-surface-variant py-8">No data found for this source.</div>
              ) : (
                sourceItems.map((item, idx) => (
                  <div key={idx} className="bg-surface border border-white/5 p-4 rounded-xl">
                    <div className="flex gap-2 items-center mb-2">
                       <span className="text-[10px] bg-primary-container/20 text-primary-container px-2 py-0.5 rounded font-bold uppercase">{item.metadata?.theme || 'Uncategorized'}</span>
                       {item.metadata?.sentiment && (
                         <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${item.metadata.sentiment === 'positive' ? 'bg-green-500/20 text-green-400' : item.metadata.sentiment === 'negative' ? 'bg-red-500/20 text-red-400' : 'bg-white/10 text-white'}`}>{item.metadata.sentiment}</span>
                       )}
                    </div>
                    <p className="text-on-surface text-sm leading-relaxed">{item.text}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Theme Data Modal */}
      {selectedThemeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm cursor-pointer" onClick={() => setSelectedThemeModal(null)}></div>
          <div className="relative bg-surface-container-high border border-white/10 rounded-2xl w-full max-w-3xl max-h-[80vh] flex flex-col shadow-2xl">
            <div className="p-6 border-b border-white/10 flex justify-between items-center">
              <h3 className="text-white font-headline-lg text-2xl capitalize">{selectedThemeModal} Mentions</h3>
              <button onClick={() => setSelectedThemeModal(null)} className="text-on-surface-variant hover:text-white cursor-pointer">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-grow flex flex-col gap-4">
              {isLoadingThemeItems ? (
                <div className="text-center text-on-surface-variant py-8 animate-pulse">Loading items...</div>
              ) : themeItems.length === 0 ? (
                <div className="text-center text-on-surface-variant py-8">No data found for this theme.</div>
              ) : (
                themeItems.map((item, idx) => (
                  <div key={idx} className="bg-surface border border-white/5 p-4 rounded-xl">
                    <div className="flex gap-2 items-center mb-2">
                       <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${item.source === 'youtube' ? 'bg-red-500/20 text-red-400' : item.source === 'playstore' ? 'bg-green-500/20 text-green-400' : item.source === 'appstore' ? 'bg-blue-400/20 text-blue-300' : 'bg-orange-500/20 text-orange-400'}`}>{item.source || 'Unknown'}</span>
                       {item.metadata?.sentiment && (
                         <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${item.metadata.sentiment === 'positive' ? 'bg-green-500/20 text-green-400' : item.metadata.sentiment === 'negative' ? 'bg-red-500/20 text-red-400' : 'bg-white/10 text-white'}`}>{item.metadata.sentiment}</span>
                       )}
                    </div>
                    <p className="text-on-surface text-sm leading-relaxed">{item.text}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
