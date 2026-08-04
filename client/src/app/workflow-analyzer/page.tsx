"use client";
import { useState } from "react";
import Topbar from "@/components/Topbar";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function WorkflowAnalyzer() {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadSummary = async () => {
    try {
      setIsDownloading(true);
      const res = await fetch(`${API_URL}/api/reports/summary`);
      if (!res.ok) throw new Error("Failed to download summary");
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "Blinkit_Discovery_Insights.md";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error downloading summary:", error);
      alert("Failed to download insights summary. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  };

  const steps = [
    {
      id: "01",
      title: "Multi-Channel Data Aggregation",
      icon: "hub",
      color: "text-blue-400",
      bgHover: "hover:border-blue-400/30",
      techDesc: "Automated cron jobs scrape unstructured, raw user feedback across Reddit (API), App Store (Reviews), and YouTube (Comments) to build a massive raw JSONL dataset.",
      pmRationale: "We cannot rely purely on internal support tickets. To discover unknown problems, we must listen to users where they natively complain without bias. Aggregating across multiple channels prevents echo-chamber hypotheses.",
    },
    {
      id: "02",
      title: "AI Structuring & Semantic Extraction",
      icon: "psychology",
      color: "text-purple-400",
      bgHover: "hover:border-purple-400/30",
      techDesc: "Raw data is piped through a Large Language Model (Gemini/Groq). The LLM drops spam, determines relevance, and forces unstructured text into a strict Pydantic JSON schema (Behavior, Frustration, Sentiment).",
      pmRationale: "Raw data is useless without structure. By forcing the LLM to extract 'Frustrations' and 'Behaviors', we convert qualitative noise into quantifiable, queryable PM attributes that we can measure over time.",
    },
    {
      id: "03",
      title: "Vector Embedding & Storage",
      icon: "database",
      color: "text-emerald-400",
      bgHover: "hover:border-emerald-400/30",
      techDesc: "The structured JSON objects are converted into dense vector embeddings using HuggingFace models and stored inside ChromaDB, a semantic vector database designed for high-speed similarity search.",
      pmRationale: "Keyword search ('search for bug') misses context. Vector search allows us to ask 'Why are users abandoning carts?' and instantly retrieve semantically similar complaints, even if they don't share exact keywords.",
    },
    {
      id: "04",
      title: "Synthesis & RAG Engine",
      icon: "insights",
      color: "text-primary-container",
      bgHover: "hover:border-primary-container/30",
      techDesc: "The Dashboard aggregates metadata for macro-trends, while the Chat Engine uses Retrieval-Augmented Generation (RAG) to dynamically synthesize context-aware answers grounded in real citations.",
      pmRationale: "This closes the loop. The dashboard tells us WHAT is happening at scale, and the RAG Chat Engine allows us to interrogate the WHY. It acts as an autonomous user research assistant for instant hypothesis validation.",
    }
  ];

  return (
    <>
      <Topbar title="Workflow Analyzer" />
      <main className="min-h-screen pt-24 md:pl-64 pb-20 md:pb-0 relative overflow-hidden bg-background">
        <div className="bg-bloom top-[-20%] left-[-10%] opacity-40"></div>
        <div className="bg-bloom bottom-[-10%] right-[-10%] opacity-30"></div>
        
        <div className="max-w-5xl mx-auto px-6 relative z-10">
          <div className="mb-16 text-center space-y-4">
            <h1 className="font-display-lg text-headline-lg text-on-surface">Discovery Engine Architecture</h1>
            <p className="text-on-surface-variant max-w-2xl mx-auto">
              A collaborative look at how our data pipeline transforms qualitative noise into structured product strategy.
            </p>
          </div>

          <div className="relative space-y-8">
            {/* Connecting Line */}
            <div className="absolute left-8 md:left-1/2 top-10 bottom-10 w-0.5 bg-gradient-to-b from-blue-400/20 via-purple-400/20 to-primary-container/20 -translate-x-1/2 hidden md:block"></div>

            {steps.map((step, index) => {
              const isEven = index % 2 === 0;
              return (
                <div key={step.id} className={`relative flex flex-col md:flex-row items-center gap-8 ${isEven ? 'md:flex-row-reverse' : ''} group`}>
                  
                  {/* Timeline Node */}
                  <div className="absolute left-8 md:left-1/2 -translate-x-1/2 w-16 h-16 rounded-2xl bg-surface-container-high border border-white/10 flex items-center justify-center shadow-xl z-10 group-hover:scale-110 transition-transform duration-500 hidden md:flex">
                    <span className={`material-symbols-outlined text-3xl ${step.color}`}>{step.icon}</span>
                  </div>

                  {/* Spacer for alternating layout */}
                  <div className="hidden md:block w-1/2"></div>

                  {/* Content Card */}
                  <div className={`w-full md:w-1/2 ${isEven ? 'md:pr-16' : 'md:pl-16'}`}>
                    <div className={`glass-card p-8 rounded-3xl border border-white/5 shadow-2xl relative overflow-hidden transition-all duration-500 ${step.bgHover} hover:-translate-y-1`}>
                      <div className="shimmer absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity pointer-events-none"></div>
                      
                      <div className="flex items-center gap-4 mb-6">
                        <span className={`font-mono text-3xl font-bold ${step.color} opacity-40`}>{step.id}</span>
                        <h3 className="text-xl font-bold text-on-surface">{step.title}</h3>
                      </div>

                      <div className="space-y-6">
                        {/* Technical Description */}
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <span className="material-symbols-outlined text-sm text-on-surface-variant">terminal</span>
                            <span className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">How it works (Engineering)</span>
                          </div>
                          <p className="text-sm text-on-surface/80 leading-relaxed">
                            {step.techDesc}
                          </p>
                        </div>

                        {/* PM Rationale */}
                        <div className="bg-primary-container/10 border border-primary-container/20 rounded-xl p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="material-symbols-outlined text-sm text-primary-container">lightbulb</span>
                            <span className="text-xs font-bold uppercase tracking-widest text-primary-container">Why it matters (Product)</span>
                          </div>
                          <p className="text-sm text-primary-container/90 leading-relaxed font-medium">
                            {step.pmRationale}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-32 mb-16 text-center space-y-4">
            <h2 className="font-display-lg text-4xl text-on-surface">How Emergent Themes Are Identified</h2>
            <p className="text-on-surface-variant max-w-2xl mx-auto">
              We don't rely on random AI hallucinations. Our theme identification is grounded in hard mathematics and refined by LLM synthesis.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative z-10">
            <div className="glass-card p-8 rounded-3xl border border-white/5 hover:border-blue-400/30 transition-all duration-300 group">
              <div className="w-12 h-12 rounded-xl bg-blue-400/10 text-blue-400 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <span className="material-symbols-outlined">calculate</span>
              </div>
              <h3 className="text-lg font-bold text-on-surface mb-3">1. Mathematical Clustering</h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                First, the engine scans the Vector Database metadata. It looks for highly frequent, repeating intersections of specific <span className="text-blue-400 font-mono text-xs">category_mentioned</span> and <span className="text-blue-400 font-mono text-xs">barrier_type</span> tags to find statistical anomalies.
              </p>
            </div>

            <div className="glass-card p-8 rounded-3xl border border-white/5 hover:border-purple-400/30 transition-all duration-300 group">
              <div className="w-12 h-12 rounded-xl bg-purple-400/10 text-purple-400 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <span className="material-symbols-outlined">format_quote</span>
              </div>
              <h3 className="text-lg font-bold text-on-surface mb-3">2. Quote Extraction</h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                Once a mathematical cluster is identified (e.g., 45 mentions of "Quality Concerns" in "Fruits"), the engine pulls the top 5 raw, verbatim user quotes from that exact cluster to provide real-world context.
              </p>
            </div>

            <div className="glass-card p-8 rounded-3xl border border-white/5 hover:border-primary-container/30 transition-all duration-300 group">
              <div className="w-12 h-12 rounded-xl bg-primary-container/10 text-primary-container flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <span className="material-symbols-outlined">auto_awesome</span>
              </div>
              <h3 className="text-lg font-bold text-on-surface mb-3">3. PM-Grade Synthesis</h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                Finally, those raw quotes are sent to the AI Synthesizer. It acts as a Senior PM, reading the context and generating a punchy, highly actionable theme title (e.g., <i>"Stale Produce Deterring Repeat Purchases"</i>).
              </p>
            </div>
          </div>

          <div className="mt-32 mb-16 text-center space-y-4">
            <h2 className="font-display-lg text-4xl text-on-surface">Insight Generation & Quality Validation</h2>
            <p className="text-on-surface-variant max-w-2xl mx-auto">
              Generating an insight is easy; proving it is hard. Here is how we guarantee that every strategic takeaway is grounded in actual user reality.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 relative z-10">
            {/* How Insights Are Generated */}
            <div className="glass-card p-8 rounded-3xl border border-white/5 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                <span className="material-symbols-outlined text-[100px] text-tertiary-container">model_training</span>
              </div>
              <h3 className="text-2xl font-bold text-on-surface mb-6 flex items-center gap-3">
                <span className="material-symbols-outlined text-tertiary-container">memory</span>
                How Insights Are Generated
              </h3>
              
              <div className="space-y-6 relative z-10">
                <div className="flex gap-4">
                  <div className="mt-1 flex-shrink-0 w-8 h-8 rounded-full bg-white/5 flex items-center justify-center border border-white/10 text-on-surface-variant">
                    <span className="material-symbols-outlined text-sm">search</span>
                  </div>
                  <div>
                    <h4 className="font-bold text-on-surface text-sm mb-1">Semantic Retrieval</h4>
                    <p className="text-sm text-on-surface-variant leading-relaxed">When a PM asks a question, the engine converts it into a dense vector and retrieves the Top-K most mathematically relevant chunks of user feedback from ChromaDB.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="mt-1 flex-shrink-0 w-8 h-8 rounded-full bg-white/5 flex items-center justify-center border border-white/10 text-on-surface-variant">
                    <span className="material-symbols-outlined text-sm">merge</span>
                  </div>
                  <div>
                    <h4 className="font-bold text-on-surface text-sm mb-1">Context Injection</h4>
                    <p className="text-sm text-on-surface-variant leading-relaxed">The retrieved feedback (the "Micro Quotes") is merged with the high-level metadata statistics (the "Macro Stats") into a unified prompt context.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="mt-1 flex-shrink-0 w-8 h-8 rounded-full bg-white/5 flex items-center justify-center border border-white/10 text-on-surface-variant">
                    <span className="material-symbols-outlined text-sm">edit_document</span>
                  </div>
                  <div>
                    <h4 className="font-bold text-on-surface text-sm mb-1">LLM Synthesis</h4>
                    <p className="text-sm text-on-surface-variant leading-relaxed">The LLM is explicitly instructed to act as a Senior PM, synthesizing the hard data and raw quotes into a strategic, actionable answer.</p>
                  </div>
                </div>
              </div>
            </div>

            {/* How Quality is Validated */}
            <div className="glass-card p-8 rounded-3xl border border-white/5 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                <span className="material-symbols-outlined text-[100px] text-emerald-400">verified_user</span>
              </div>
              <h3 className="text-2xl font-bold text-on-surface mb-6 flex items-center gap-3">
                <span className="material-symbols-outlined text-emerald-400">verified</span>
                Quality & Trust Validation
              </h3>
              
              <div className="space-y-6 relative z-10">
                <div className="flex gap-4">
                  <div className="mt-1 flex-shrink-0 w-8 h-8 rounded-full bg-emerald-400/10 flex items-center justify-center border border-emerald-400/20 text-emerald-400">
                    <span className="material-symbols-outlined text-sm">link</span>
                  </div>
                  <div>
                    <h4 className="font-bold text-on-surface text-sm mb-1">Deterministic Citations</h4>
                    <p className="text-sm text-on-surface-variant leading-relaxed">The engine is forced to inject exact Source IDs into its responses. Every single insight can be traced back to the raw, unedited user quote with one click.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="mt-1 flex-shrink-0 w-8 h-8 rounded-full bg-emerald-400/10 flex items-center justify-center border border-emerald-400/20 text-emerald-400">
                    <span className="material-symbols-outlined text-sm">gavel</span>
                  </div>
                  <div>
                    <h4 className="font-bold text-on-surface text-sm mb-1">Anti-Hallucination Guardrails</h4>
                    <p className="text-sm text-on-surface-variant leading-relaxed">The system prompt strictly demands that the AI grounds its answers mathematically in the [MACRO STATS]. If the data isn't there, it refuses to guess.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="mt-1 flex-shrink-0 w-8 h-8 rounded-full bg-emerald-400/10 flex items-center justify-center border border-emerald-400/20 text-emerald-400">
                    <span className="material-symbols-outlined text-sm">fact_check</span>
                  </div>
                  <div>
                    <h4 className="font-bold text-on-surface text-sm mb-1">Continuous Tuning</h4>
                    <p className="text-sm text-on-surface-variant leading-relaxed">Because the RAG context is stateless, bad insights are easily fixed by adjusting the embedding similarity threshold (Top-K) or refining the strict Pydantic extraction schema upstream.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Download Summary Section */}
          <div className="mt-32 mb-16 text-center space-y-8 relative z-10">
            <div className="max-w-2xl mx-auto">
              <h2 className="font-display-lg text-4xl text-on-surface mb-4">Export Strategic Insights</h2>
              <p className="text-on-surface-variant mb-8">
                Generate a comprehensive Executive Summary of the latest macro statistics and emergent themes using our AI Engine.
              </p>
              <button 
                onClick={handleDownloadSummary}
                disabled={isDownloading}
                className="group relative inline-flex items-center gap-3 px-8 py-4 bg-primary-container text-on-primary-container rounded-full font-bold shadow-lg hover:shadow-primary-container/25 hover:-translate-y-1 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
              >
                <div className="absolute inset-0 rounded-full bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                {isDownloading ? (
                  <>
                    <span className="material-symbols-outlined animate-spin">progress_activity</span>
                    Generating Report...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined group-hover:animate-bounce">download</span>
                    Download AI Insights Summary
                  </>
                )}
              </button>
            </div>
          </div>

        </div>
      </main>
    </>
  );
}
