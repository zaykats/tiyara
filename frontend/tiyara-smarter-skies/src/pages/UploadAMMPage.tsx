import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useLang } from "@/contexts/LanguageContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Upload, FileText, Loader2, Search } from "lucide-react";

interface Doc {
  id: string;
  filename: string;
  engine_type_tag: string;
  created_at: string;
}

export default function UploadAMMPage() {
  const { toast } = useToast();
  const { t } = useLang();
  const fileRef = useRef<HTMLInputElement>(null);
  const [engineTag, setEngineTag] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [filter, setFilter] = useState("");
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [dragOver, setDragOver] = useState(false);

  const fetchDocs = (tag?: string) => {
    const q = tag ? `?engine_type_tag=${encodeURIComponent(tag)}` : "";
    apiFetch(`/documents${q}`).then(async (res) => {
      if (res.ok) setDocs(await res.json());
    }).finally(() => setLoadingDocs(false));
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleUpload = async () => {
    if (!file || !engineTag.trim()) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("engine_type_tag", engineTag);
    fd.append("file", file);
    try {
      const res = await apiFetch("/documents/ingest", { method: "POST", body: fd });
      if (res.status === 201) {
        const data = await res.json();
        toast({ title: t("doc_uploaded"), description: `${data.filename} — ${data.chunks_created} chunks created` });
        setFile(null);
        setEngineTag("");
        fetchDocs();
      } else if (res.status === 403) {
        toast({ title: t("permission_denied"), description: t("no_permission"), variant: "destructive" });
      }
    } catch {} finally {
      setUploading(false);
    }
  };

  const handleFilter = () => { setLoadingDocs(true); fetchDocs(filter); };

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 max-w-4xl animate-fade-in">
        <h1 className="text-2xl font-bold text-foreground mb-1">{t("upload_amm")}</h1>
        <p className="text-sm text-muted-foreground mb-8">{t("upload_amm_sub")}</p>

        <div className="surface-panel p-6 space-y-5 mb-10">
          <div>
            <label className="label-tech">{t("engine_type_tag")}</label>
            <input className="input-field" value={engineTag} onChange={(e) => setEngineTag(e.target.value)} placeholder="e.g. CFM56-7B" />
          </div>
          <div>
            <label className="label-tech">{t("pdf_file")}</label>
            {!file ? (
              <div
                onClick={() => fileRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); e.dataTransfer.files[0] && setFile(e.dataTransfer.files[0]); }}
                className={`border-2 border-dashed p-8 text-center cursor-pointer transition-all duration-200 ${
                  dragOver ? 'border-primary bg-primary/5' : 'border-border hover:border-secondary/50'
                }`}
              >
                <Upload className={`w-7 h-7 mx-auto mb-2 transition-colors ${dragOver ? 'text-primary' : 'text-muted-foreground/25'}`} />
                <p className="text-sm text-muted-foreground">{t("drop_pdf")}</p>
                <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])} />
              </div>
            ) : (
              <motion.div className="flex items-center gap-3 px-4 py-3 surface-elevated" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }}>
                <div className="w-8 h-8 bg-success/10 border border-success/20 flex items-center justify-center">
                  <FileText className="w-4 h-4 text-success" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-sm text-foreground block truncate">{file.name}</span>
                  <span className="font-mono-tech text-[10px] text-muted-foreground/50">{(file.size / 1024).toFixed(1)} KB</span>
                </div>
                <button onClick={() => setFile(null)} className="text-[11px] font-mono-tech text-muted-foreground hover:text-destructive transition-colors tracking-wider">
                  {t("remove")}
                </button>
              </motion.div>
            )}
          </div>
          <button
            onClick={handleUpload}
            disabled={!file || !engineTag.trim() || uploading}
            className="btn-aerospace text-sm flex items-center gap-2"
          >
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            {uploading ? t("uploading") : t("upload_doc")}
          </button>
        </div>

        {/* Document list */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-mono-tech text-[10px] text-muted-foreground/60 tracking-[0.15em]">{t("existing_docs")}</h2>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground/30" />
                <input
                  className="input-field pl-9 py-2 text-xs w-48"
                  style={{ minHeight: 'auto' }}
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  placeholder={t("filter_engine")}
                  onKeyDown={(e) => e.key === "Enter" && handleFilter()}
                />
              </div>
              <button onClick={handleFilter} className="text-[11px] font-mono-tech text-secondary hover:text-foreground transition-colors tracking-wider">
                {t("filter")}
              </button>
            </div>
          </div>
          <div className="space-y-1.5">
            {docs.map((d, i) => (
              <motion.div key={d.id} className="surface-panel px-4 py-3 flex items-center gap-4" initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
                <div className="w-8 h-8 bg-muted flex items-center justify-center shrink-0">
                  <FileText className="w-4 h-4 text-secondary/60" />
                </div>
                <span className="text-sm text-foreground flex-1 truncate">{d.filename}</span>
                <span className="font-mono-tech text-[10px] text-secondary tracking-wider hidden sm:inline">{d.engine_type_tag}</span>
                <span className="font-mono-tech text-[10px] text-muted-foreground/40">{new Date(d.created_at).toLocaleDateString()}</span>
              </motion.div>
            ))}
            {!loadingDocs && docs.length === 0 && (
              <div className="text-center py-12">
                <FileText className="w-8 h-8 text-muted-foreground/15 mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">{t("no_docs")}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
