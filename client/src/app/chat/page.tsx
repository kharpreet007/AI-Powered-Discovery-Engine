"use client";
import Topbar from "@/components/Topbar";
import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Message = {
  role: "user" | "ai";
  content: string;
  citations: any[];
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [filterSource, setFilterSource] = useState("all");
  const [filterSentiment, setFilterSentiment] = useState("all");
  const [selectedCitation, setSelectedCitation] = useState<any | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const extraQuestions = [
    "What role do habits play in shopping behavior?",
    "What information do users need before trying a new category?",
    "What frustrations emerge repeatedly?",
    "Which user segments are more likely to experiment?",
    "What unmet needs emerge consistently across discussions?"
  ];

  const handleSuggestionClick = (q: string) => {
    setShowSuggestions(false);
    handleSubmit(q);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (query?: string) => {
    const text = query || inputValue;
    if (!text.trim()) return;

    setInputValue("");
    const newMessages = [...messages, { role: "user", content: text, citations: [] }];
    setMessages(newMessages as Message[]);
    setIsTyping(true);

    // Build filters payload
    const filters: any = {};
    if (filterSource !== "all") filters["source"] = filterSource;
    if (filterSentiment !== "all") filters["sentiment"] = filterSentiment;

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            messages: newMessages.map(m => ({ role: m.role, content: m.content })), 
            filters: Object.keys(filters).length > 0 ? filters : undefined,
            top_k: 8 
          })
      });

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      
      let aiContent = "";
      let aiCitations: any[] = [];
      
      // Add empty AI message to append to
      setMessages(prev => [...prev, { role: "ai", content: "", citations: [] }]);
      setIsTyping(false);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.event === "token") {
                aiContent += data.data;
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1].content = aiContent;
                  return newMsgs;
                });
              } else if (data.event === "citation") {
                aiCitations.push(data.data);
                setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1].citations = aiCitations;
                  return newMsgs;
                });
              }
            } catch (e) {
              // Ignore parse errors on partial chunks
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setIsTyping(false);
    }
  };

  return (
    <>
      <Topbar title="Discovery Chat" />
      <main className="h-screen pt-20 pb-20 md:pb-0 md:pl-64 flex flex-col relative overflow-hidden">
        <div className="bg-bloom top-[-10%] left-[-10%]"></div>
        <div className="bg-bloom bottom-[-10%] right-[-10%]"></div>

        
        <div className="flex-1 overflow-y-auto px-6 py-8 chat-container flex flex-col gap-8 max-w-4xl mx-auto w-full z-10">
          
          {messages.length === 0 ? (
            <div className="mt-12 text-center space-y-10">
              <div className="space-y-4">
                <h2 className="font-display-lg text-headline-lg text-on-surface">Hey Harpreet, <br/>How can I help your research today?</h2>
                <p className="text-on-surface-variant max-w-lg mx-auto">Access millions of user data points across Reddit, Play Store, and internal surveys through our RAG-enhanced intelligence engine.</p>
              </div>
              
              <div className="flex flex-col gap-4 text-left max-w-2xl mx-auto">
                {[
                  { q: "Why do users repeatedly buy from the same categories?" },
                  { q: "What prevents users from exploring new categories?" },
                  { q: "How do users discover products today?" }
                ].map((item, i) => (
                  <button key={i} onClick={() => handleSubmit(item.q)} className="glass-card p-4 rounded-xl hover:border-primary-container/50 hover:bg-white/5 transition-all text-left group cursor-pointer">
                    <p className="text-sm font-medium text-on-surface group-hover:text-primary-container">{item.q}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex flex-col gap-3 max-w-[85%] ${msg.role === 'user' ? 'self-end items-end' : 'self-start'}`}>
                  {msg.role === 'ai' && (
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-6 h-6 rounded-md bg-primary-container flex items-center justify-center">
                        <img alt="AI" className="w-4 h-4 rounded" src="https://upload.wikimedia.org/wikipedia/commons/2/2f/Blinkit-yellow-app-icon.svg" />
                      </div>
                      <span className="text-xs font-bold uppercase tracking-widest text-primary-fixed">Engine Analysis</span>
                    </div>
                  )}
                  
                  <div className={`${msg.role === 'user' ? 'bg-primary-container text-on-primary-container font-medium' : 'glass-card space-y-4'} p-4 rounded-2xl ${msg.role === 'user' ? 'rounded-tr-none shadow-xl' : 'rounded-tl-none shadow-2xl relative overflow-hidden'}`}>
                    {msg.role === 'ai' && <div className="shimmer absolute inset-0 opacity-10 pointer-events-none"></div>}
                    {msg.role === 'ai' ? (
                      <div className="prose prose-invert prose-sm max-w-none text-on-surface">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="relative whitespace-pre-wrap">{msg.content}</p>
                    )}
                    
                    {msg.citations && msg.citations.length > 0 && msg.content && (
                      <div className="flex flex-wrap gap-2 relative mt-3 pt-3 border-t border-white/10">
                        {msg.citations
                           .filter(c => msg.content.includes(`[${c.id}]`))
                           .map((c, cIdx) => (
                          <button key={cIdx} onClick={() => setSelectedCitation(c)} className="px-2 py-1 bg-surface-container-high border border-white/10 rounded text-[10px] text-on-surface-variant hover:border-primary-container cursor-pointer transition-colors active:scale-95">
                            [{c.id}] Source: <span className="uppercase font-bold">{c.source || 'Database'}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {isTyping && (
          <div className="absolute bottom-32 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-surface-container-high px-4 py-2 rounded-full border border-white/10 z-20">
            <div className="flex gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-primary-container typing-dot"></div>
              <div className="w-1.5 h-1.5 rounded-full bg-primary-container typing-dot" style={{animationDelay: '0.2s'}}></div>
              <div className="w-1.5 h-1.5 rounded-full bg-primary-container typing-dot" style={{animationDelay: '0.4s'}}></div>
            </div>
            <span className="text-xs text-on-surface-variant font-mono">Blinkit Engine is thinking...</span>
          </div>
        )}

        <div className="p-6 bg-gradient-to-t from-background via-background to-transparent z-20">
          <div className="max-w-4xl mx-auto relative group">
            
            {/* Pop Chat Suggestions */}
            {showSuggestions && (
              <div className="absolute bottom-full left-0 mb-4 bg-surface-container-high border border-white/10 rounded-xl p-2 w-80 shadow-2xl animate-in slide-in-from-bottom-2 fade-in duration-200 z-50">
                <div className="flex justify-between items-center px-2 py-1 mb-2 border-b border-white/5">
                  <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">More Questions</span>
                  <button onClick={() => setShowSuggestions(false)} className="text-on-surface-variant hover:text-white">
                    <span className="material-symbols-outlined text-[16px]">close</span>
                  </button>
                </div>
                <div className="flex flex-col gap-1 max-h-[400px] overflow-y-auto scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent pr-1">
                  {extraQuestions.map((q, idx) => (
                    <button key={idx} onClick={() => handleSuggestionClick(q)} className="text-left px-3 py-2 text-sm text-on-surface hover:bg-white/5 hover:text-primary-container rounded-lg transition-colors cursor-pointer">
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-4 mb-3 relative z-10">
              <button onClick={() => setShowSuggestions(!showSuggestions)} className="bg-surface border border-white/10 rounded-lg px-3 py-1.5 text-xs text-on-surface-variant hover:border-primary-container hover:text-primary-container transition-colors flex items-center gap-1 cursor-pointer">
                <span className="material-symbols-outlined text-[14px]">lightbulb</span>
                More Questions
              </button>
            </div>
            
            <div className="absolute -inset-0.5 bg-gradient-to-r from-primary-container/20 to-tertiary-container/20 rounded-2xl blur opacity-30 group-focus-within:opacity-100 transition duration-500 pointer-events-none"></div>
            <div className="relative glass-card rounded-2xl flex items-center p-2 pr-3 shadow-2xl bg-surface">
              <div className="pl-4 flex items-center gap-3 text-on-surface-variant">
                <span className="material-symbols-outlined text-[20px]">attach_file</span>
              </div>
              <input 
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-on-surface py-4 px-3 placeholder:text-on-surface-variant/50" 
                placeholder="Ask anything about user behavior..." 
                type="text"
              />
              <div className="flex items-center gap-2">
                <button className="p-2 rounded-lg hover:bg-white/5 text-on-surface-variant transition-colors cursor-pointer">
                  <span className="material-symbols-outlined">mic</span>
                </button>
                <button onClick={() => handleSubmit()} className="bg-primary-container text-on-primary-container p-3 rounded-xl shadow-lg shadow-primary-container/10 hover:shadow-primary-container/20 transition-all active:scale-95 flex items-center justify-center cursor-pointer">
                  <span className="material-symbols-outlined font-bold">arrow_forward</span>
                </button>
              </div>
            </div>
            <div className="flex justify-center mt-4 gap-6">
              <div className="flex items-center gap-2 text-[10px] text-on-surface-variant/60"><span className="material-symbols-outlined text-xs">verified</span>Citations included</div>
              <div className="flex items-center gap-2 text-[10px] text-on-surface-variant/60"><span className="material-symbols-outlined text-xs">bolt</span>Real-time RAG</div>
              <div className="flex items-center gap-2 text-[10px] text-on-surface-variant/60"><span className="material-symbols-outlined text-xs">shield</span>Privacy secure</div>
            </div>
          </div>
        </div>
      </main>

      {/* Citation Modal */}
      {selectedCitation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm" onClick={() => setSelectedCitation(null)}>
          <div className="glass-card max-w-2xl w-full p-8 rounded-3xl shadow-2xl relative animate-in fade-in zoom-in-95 duration-200" onClick={e => e.stopPropagation()}>
            <button onClick={() => setSelectedCitation(null)} className="absolute top-6 right-6 w-8 h-8 flex items-center justify-center rounded-full bg-surface-container-high hover:bg-white/10 transition-colors text-on-surface-variant">
              <span className="material-symbols-outlined text-sm">close</span>
            </button>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-primary-container/20 flex items-center justify-center border border-primary-container/30">
                <span className="material-symbols-outlined text-primary-container">data_object</span>
              </div>
              <div>
                <h3 className="text-lg font-bold text-on-surface">Source Evidence [{selectedCitation.id}]</h3>
                <p className="text-xs text-on-surface-variant uppercase tracking-widest font-bold">{selectedCitation.source || 'Database'}</p>
              </div>
            </div>
            
            <div className="bg-surface-container-low rounded-2xl p-6 border border-white/5 max-h-[60vh] overflow-y-auto">
              <p className="text-sm text-on-surface leading-relaxed whitespace-pre-wrap font-mono">{selectedCitation.text}</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
