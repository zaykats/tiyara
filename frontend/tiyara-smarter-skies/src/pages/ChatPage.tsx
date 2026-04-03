import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { apiFetch, sseStream } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useLang } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import { SkeletonCard } from "@/components/SkeletonCard";
import {
  Send, AlertTriangle, CheckCircle, Cog, Copy, Plane,
  FileDown, Loader2, ChevronDown, ChevronUp,
} from "lucide-react";

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  structured_content?: any;
  created_at?: string;
}

interface SessionData {
  id: string;
  engine_type: string;
  problem_description: string;
  status: string;
  created_at: string;
  messages: Message[];
  excel_pattern_summary?: {
    top_faults: string[];
    recurring_components: string[];
    unresolved_patterns: string[];
    time_between_recurrences: number;
    risk_summary: string;
  };
}

const DOCUMENTS = [
  { key: "report",        labelKey: "doc_report",        path: "report" },
  { key: "finding-input", labelKey: "doc_finding",       path: "report/finding-input" },
  { key: "ai-analysis",   labelKey: "doc_ai_analysis",   path: "report/ai-analysis" },
  { key: "capability",    labelKey: "doc_capability",    path: "report/capability" },
  { key: "service-order", labelKey: "doc_service_order", path: "report/service-order" },
  { key: "kcc",           labelKey: "doc_kcc",           path: "report/kcc" },
];

function StepGuide({ data }: { data: any }) {
  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-foreground text-sm border-b border-border pb-2">{data.title}</h3>
      {data.steps?.map((step: any, i: number) => (
        <motion.div
          key={i}
          className="surface-elevated p-4 space-y-2"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
        >
          <div className="flex items-center gap-2.5">
            <span className="w-7 h-7 bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold shrink-0">
              {i + 1}
            </span>
            <span className="font-medium text-foreground text-sm">{step.title}</span>
          </div>
          <p className="text-sm text-muted-foreground pl-[38px] leading-relaxed">{step.instruction}</p>
          {step.warning && (
            <div className="ml-[38px] border border-destructive/20 bg-destructive/5 px-3 py-2.5 flex items-start gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-destructive shrink-0 mt-0.5" />
              <span className="text-xs text-destructive leading-relaxed">{step.warning}</span>
            </div>
          )}
          {step.amm_reference && (
            <span className="ml-[38px] inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono-tech text-secondary border border-secondary/20 bg-secondary/5 tracking-wider">
              AMM {step.amm_reference}
            </span>
          )}
        </motion.div>
      ))}
      {data.closing_note && (
        <div className="border-l-2 border-primary/30 pl-3 mt-2">
          <p className="text-sm text-muted-foreground italic leading-relaxed">{data.closing_note}</p>
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-4 py-3">
      {[0, 1, 2].map((i) => (
        <div key={i} className="w-1.5 h-1.5 bg-secondary rounded-full animate-pulse-dot" style={{ animationDelay: `${i * 0.2}s` }} />
      ))}
    </div>
  );
}

export default function ChatPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { toast } = useToast();
  const { lang, t } = useLang();
  const [session, setSession] = useState<SessionData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(true);
  const [docsExpanded, setDocsExpanded] = useState(false);
  const [downloading, setDownloading] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamingContentRef = useRef("");

  useEffect(() => {
    if (!sessionId) return;
    apiFetch(`/sessions/${sessionId}`).then(async (res) => {
      if (res.ok) {
        const data: SessionData = await res.json();
        setSession(data);
        setMessages(data.messages || []);
      }
    }).finally(() => setLoading(false));
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  const handleSend = () => {
    if (!input.trim() || streaming || session?.status === "resolved") return;
    const userMsg: Message = { role: "user", content: input.trim() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setStreaming(true);
    streamingContentRef.current = "";

    const assistantMsg: Message = { role: "assistant", content: "" };
    setMessages([...newMessages, assistantMsg]);

    const history = newMessages.map((m) => ({ role: m.role, content: m.content }));

    sseStream(
      "/chat",
      { session_id: sessionId, user_message: userMsg.content, conversation_history: history },
      (text) => {
        streamingContentRef.current += text;
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: "assistant", content: streamingContentRef.current };
          return updated;
        });
      },
      () => {
        setStreaming(false);
        const content = streamingContentRef.current;
        try {
          if (content.trim().startsWith('{"type":"step_guide"') || content.trim().startsWith('{ "type": "step_guide"')) {
            const parsed = JSON.parse(content);
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = { role: "assistant", content, structured_content: parsed };
              return updated;
            });
          }
        } catch {}
      }
    );
  };

  const handleResolve = async () => {
    if (!sessionId) return;
    const res = await apiFetch(`/sessions/${sessionId}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "resolved" }),
    });
    if (res.ok) {
      setSession((s) => s ? { ...s, status: "resolved" } : s);
      toast({ title: t("session_marked_resolved") });
    }
  };

  const handleDownload = async (docKey: string, docPath: string) => {
    if (!sessionId || downloading[docKey]) return;
    setDownloading((d) => ({ ...d, [docKey]: true }));
    try {
      const res = await apiFetch(`/sessions/${sessionId}/${docPath}?lang=${lang}`);
      if (!res.ok) {
        toast({ title: t("failed_to_generate"), variant: "destructive" });
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const ref = sessionId.slice(0, 8).toUpperCase();
      const langSuffix = lang === "fr" ? "_FR" : "";
      a.download = `Tiyara_${docKey.replace(/-/g, "_")}_${ref}${langSuffix}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast({ title: t("downloaded"), description: a.download });
    } catch {
      toast({ title: t("download_failed"), variant: "destructive" });
    } finally {
      setDownloading((d) => ({ ...d, [docKey]: false }));
    }
  };

  const isResolved = session?.status === "resolved";

  if (loading) {
    return (
      <DashboardLayout>
        <div className="p-6 space-y-4">
          <SkeletonCard /><SkeletonCard /><SkeletonCard />
        </div>
      </DashboardLayout>
    );
  }

  const hasMessages = messages.length > 0;

  return (
    <DashboardLayout>
      <div className="flex h-[calc(100vh-56px)]">
        {/* Left sidebar */}
        <aside className="w-72 border-r border-border overflow-y-auto hidden lg:block shrink-0">
          <div className="p-4 space-y-4">
            {/* Session info */}
            <div className="surface-panel p-3 space-y-3">
              <p className="font-mono-tech text-[10px] text-muted-foreground/40 tracking-[0.15em]">{t("session_info")}</p>
              <div className="space-y-2.5">
                <div>
                  <p className="text-[10px] font-mono-tech text-muted-foreground/50 tracking-wider mb-0.5">{t("engine_label")}</p>
                  <p className="text-sm font-medium text-foreground">{session?.engine_type}</p>
                </div>
                <div>
                  <p className="text-[10px] font-mono-tech text-muted-foreground/50 tracking-wider mb-0.5">ID</p>
                  <div className="flex items-center gap-1.5">
                    <p className="text-[11px] font-mono text-muted-foreground">{session?.id?.slice(0, 12)}...</p>
                    <button
                      onClick={() => { navigator.clipboard.writeText(session?.id || ""); toast({ title: t("copied") }); }}
                      className="text-muted-foreground/30 hover:text-foreground transition-colors"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                  </div>
                </div>
                <div>
                  <p className="text-[10px] font-mono-tech text-muted-foreground/50 tracking-wider mb-0.5">DATE</p>
                  <p className="text-xs text-muted-foreground">{session?.created_at ? new Date(session.created_at).toLocaleDateString() : "-"}</p>
                </div>
              </div>
            </div>

            {/* History patterns */}
            {session?.excel_pattern_summary && (
              <div className="surface-panel p-3 space-y-3">
                <p className="font-mono-tech text-[10px] text-muted-foreground/40 tracking-[0.15em]">{t("history_patterns")}</p>
                <div className="flex flex-wrap gap-1">
                  {session.excel_pattern_summary.top_faults.map((f) => (
                    <span key={f} className="px-2 py-0.5 text-[10px] font-mono-tech bg-secondary/10 text-secondary border border-secondary/20 tracking-wider">{f}</span>
                  ))}
                </div>
                {session.excel_pattern_summary.risk_summary && (
                  <p className="text-xs text-muted-foreground leading-relaxed">{session.excel_pattern_summary.risk_summary}</p>
                )}
              </div>
            )}

            {/* Resolve button */}
            {!isResolved ? (
              <button
                onClick={handleResolve}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm border border-success/20 text-success hover:bg-success/5 transition-all min-h-[48px]"
              >
                <CheckCircle className="w-4 h-4" /> {t("mark_resolved")}
              </button>
            ) : (
              <div className="flex items-center justify-center gap-2 px-4 py-3 text-sm text-success bg-success/5 border border-success/20">
                <CheckCircle className="w-4 h-4" /> {t("session_resolved")}
              </div>
            )}

            {/* Document downloads */}
            {hasMessages && (
              <div className="surface-panel overflow-hidden">
                <button
                  onClick={() => setDocsExpanded(!docsExpanded)}
                  className="w-full flex items-center justify-between px-3 py-2.5 text-xs text-primary hover:bg-primary/5 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <FileDown className="w-3.5 h-3.5" />
                    <span className="font-mono-tech tracking-wider text-[10px]">{t("documents")} ({DOCUMENTS.length})</span>
                  </span>
                  {docsExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>

                {docsExpanded && (
                  <div className="border-t border-border">
                    {DOCUMENTS.map((doc) => {
                      const isLoading = downloading[doc.key];
                      return (
                        <button
                          key={doc.key}
                          onClick={() => handleDownload(doc.key, doc.path)}
                          disabled={isLoading}
                          className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-xs hover:bg-muted/30 transition-colors disabled:opacity-40 disabled:cursor-not-allowed border-b border-border/30 last:border-0"
                        >
                          {isLoading ? (
                            <Loader2 className="w-3 h-3 animate-spin text-primary shrink-0" />
                          ) : (
                            <FileDown className="w-3 h-3 text-muted-foreground/50 shrink-0" />
                          )}
                          <span className="text-foreground/80 leading-tight">{t(doc.labelKey)}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </aside>

        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center py-20">
                <div className="w-12 h-12 bg-muted flex items-center justify-center mb-4">
                  <Plane className="w-6 h-6 text-muted-foreground/20" />
                </div>
                <p className="text-sm text-muted-foreground mb-1">{t("start_diag_conv")}</p>
                <p className="text-xs text-muted-foreground/50">{t("describe_fault")}</p>
              </div>
            )}
            <AnimatePresence mode="popLayout">
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                  layout
                >
                  {msg.role === "assistant" && (
                    <div className="w-8 h-8 bg-card border border-border flex items-center justify-center mr-2.5 shrink-0 mt-1">
                      <Cog className="w-3.5 h-3.5 text-secondary" />
                    </div>
                  )}
                  <div className={`max-w-[78%] ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground px-4 py-3"
                      : "surface-panel px-4 py-3"
                  }`}>
                    {msg.role === "assistant" && msg.structured_content?.type === "step_guide" ? (
                      <StepGuide data={msg.structured_content} />
                    ) : (
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    )}
                    {msg.role === "assistant" && !streaming && msg.content && (
                      <div className="flex items-center gap-2 mt-2 pt-2 border-t border-border/30">
                        <button
                          onClick={() => { navigator.clipboard.writeText(msg.content); toast({ title: t("copied") }); }}
                          className="text-muted-foreground/30 hover:text-foreground transition-colors"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            {streaming && messages[messages.length - 1]?.content === "" && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>

          {/* Input bar */}
          <div className="border-t border-border p-4">
            {isResolved && (
              <div className="flex items-center justify-center gap-2 px-4 py-2 mb-3 text-xs font-mono-tech text-success/60 tracking-wider bg-success/5 border border-success/10">
                <CheckCircle className="w-3 h-3" /> {t("session_resolved_notice")}
              </div>
            )}
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                placeholder={isResolved ? t("session_resolved_ph") : t("chat_placeholder")}
                disabled={streaming || isResolved}
                className="input-field flex-1"
              />
              <motion.button
                onClick={handleSend}
                disabled={!input.trim() || streaming || isResolved}
                className="btn-aerospace px-5 disabled:opacity-30 disabled:cursor-not-allowed"
                whileHover={input.trim() && !streaming ? { scale: 1.03 } : {}}
                whileTap={input.trim() && !streaming ? { scale: 0.97 } : {}}
              >
                <Send className="w-4 h-4" />
              </motion.button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
