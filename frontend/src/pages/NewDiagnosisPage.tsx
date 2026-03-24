import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Upload, FileSpreadsheet, Loader2, ChevronRight, Sparkles } from "lucide-react";
import * as XLSX from "xlsx";

const ENGINE_TYPES = [
  "CFM56-7B", "CFM56-5B", "LEAP-1A", "LEAP-1B", "V2500",
  "PW1100G", "Trent 700", "Trent XWB", "CF6", "GE90", "GEnx",
];

export default function NewDiagnosisPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [engineType, setEngineType] = useState("");
  const [engineSearch, setEngineSearch] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const [problemDesc, setProblemDesc] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string[][]>([]);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const filtered = ENGINE_TYPES.filter((e) =>
    e.toLowerCase().includes(engineSearch.toLowerCase())
  );

  const handleFile = useCallback((f: File) => {
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (ext !== "xlsx" && ext !== "xls") {
      toast({ title: "Invalid file", description: "Only .xlsx and .xls files are accepted", variant: "destructive" });
      return;
    }
    setFile(f);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const wb = XLSX.read(e.target?.result, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const data: string[][] = XLSX.utils.sheet_to_json(ws, { header: 1 });
        setPreview(data.slice(0, 6));
      } catch {
        setPreview([]);
      }
    };
    reader.readAsArrayBuffer(f);
  }, [toast]);

  const isValid = engineType && problemDesc.trim() && file;

  const handleSubmit = async () => {
    if (!isValid || !file) return;
    setLoading(true);

    try {
      const res1 = await apiFetch("/sessions", {
        method: "POST",
        body: JSON.stringify({ engine_type: engineType, problem_description: problemDesc }),
      });

      if (res1.status !== 201) {
        toast({ title: "Error creating session", variant: "destructive" });
        return;
      }

      const session = await res1.json();
      const formData = new FormData();
      formData.append("file", file);

      const res2 = await apiFetch(`/sessions/${session.id}/upload-excel`, {
        method: "POST",
        body: formData,
      });

      if (res2.ok) {
        toast({ title: "Diagnosis session created" });
        navigate(`/chat/${session.id}`);
      } else {
        toast({ title: "Error uploading file", variant: "destructive" });
      }
    } catch {} finally {
      setLoading(false);
    }
  };

  // Step indicator
  const steps = [
    { label: "ENGINE", done: !!engineType },
    { label: "FAULT", done: !!problemDesc.trim() },
    { label: "HISTORY", done: !!file },
  ];

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 max-w-3xl animate-fade-in">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-foreground mb-1">New Diagnosis</h1>
            <p className="text-sm text-muted-foreground">Provide engine details and upload maintenance history for AI analysis.</p>
          </div>
          <Sparkles className="w-5 h-5 text-primary/40 mt-1" />
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          {steps.map((s, i) => (
            <div key={s.label} className="flex items-center gap-2">
              <div className={`flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-mono-tech tracking-[0.12em] border transition-colors ${
                s.done
                  ? 'border-success/30 text-success bg-success/5'
                  : 'border-border text-muted-foreground/50'
              }`}>
                <span className={`w-4 h-4 flex items-center justify-center text-[9px] font-bold ${
                  s.done ? 'bg-success/20 text-success' : 'bg-muted text-muted-foreground/40'
                }`}>{i + 1}</span>
                {s.label}
              </div>
              {i < steps.length - 1 && <ChevronRight className="w-3 h-3 text-muted-foreground/20" />}
            </div>
          ))}
        </div>

        <div className="space-y-6">
          {/* Engine type */}
          <div className="relative">
            <label className="label-tech">ENGINE / COMPONENT TYPE</label>
            <input
              className="input-field"
              value={engineSearch || engineType}
              onChange={(e) => {
                setEngineSearch(e.target.value);
                setEngineType(e.target.value);
                setShowDropdown(true);
              }}
              onFocus={() => setShowDropdown(true)}
              onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
              placeholder="Search or type engine type..."
            />
            {showDropdown && filtered.length > 0 && (
              <motion.div
                className="absolute z-20 w-full mt-1 bg-card border border-border overflow-hidden"
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.15 }}
              >
                {filtered.map((e) => (
                  <button
                    key={e}
                    className="w-full text-left px-4 py-3 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors min-h-[44px] flex items-center gap-2"
                    onMouseDown={() => {
                      setEngineType(e);
                      setEngineSearch(e);
                      setShowDropdown(false);
                    }}
                  >
                    <span className="font-mono-tech text-[10px] text-muted-foreground/40 w-4">{ENGINE_TYPES.indexOf(e) + 1}</span>
                    {e}
                  </button>
                ))}
              </motion.div>
            )}
          </div>

          {/* Problem description */}
          <div>
            <label className="label-tech">PROBLEM DESCRIPTION</label>
            <textarea
              className="input-field min-h-[140px] resize-y"
              value={problemDesc}
              onChange={(e) => setProblemDesc(e.target.value)}
              placeholder="Describe the fault, symptoms, error codes, and conditions when the fault occurred..."
            />
            <p className="font-mono-tech text-[10px] text-muted-foreground/40 mt-1.5 tracking-wider">
              {problemDesc.length} CHARACTERS
            </p>
          </div>

          {/* File upload */}
          <div>
            <label className="label-tech">MAINTENANCE HISTORY (EXCEL)</label>
            {!file ? (
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); e.dataTransfer.files[0] && handleFile(e.dataTransfer.files[0]); }}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed p-10 text-center cursor-pointer transition-all duration-200 ${
                  dragOver ? 'border-primary bg-primary/5' : 'border-border hover:border-secondary/50'
                }`}
              >
                <Upload className={`w-8 h-8 mx-auto mb-3 transition-colors ${dragOver ? 'text-primary' : 'text-muted-foreground/30'}`} />
                <p className="text-sm text-muted-foreground mb-1">Drag & drop your Excel file here</p>
                <p className="text-xs text-muted-foreground/50">.xlsx or .xls format</p>
                <input ref={fileInputRef} type="file" accept=".xlsx,.xls" className="hidden" onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
              </div>
            ) : (
              <motion.div
                className="surface-panel overflow-hidden"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
              >
                <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 bg-success/10 border border-success/20 flex items-center justify-center">
                      <FileSpreadsheet className="w-4 h-4 text-success" />
                    </div>
                    <div>
                      <span className="text-sm text-foreground block">{file.name}</span>
                      <span className="font-mono-tech text-[10px] text-muted-foreground/50">{(file.size / 1024).toFixed(1)} KB</span>
                    </div>
                  </div>
                  <button
                    onClick={() => { setFile(null); setPreview([]); }}
                    className="text-[11px] font-mono-tech text-muted-foreground hover:text-destructive transition-colors tracking-wider"
                  >
                    RE-UPLOAD
                  </button>
                </div>
                {preview.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr>
                          {preview[0]?.map((h, i) => (
                            <th key={i} className="px-3 py-2.5 text-left font-mono-tech text-[10px] text-secondary tracking-wider border-b border-border bg-muted/30">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {preview.slice(1).map((row, ri) => (
                          <tr key={ri} className={ri % 2 === 0 ? "" : "bg-muted/10"}>
                            {row.map((cell, ci) => (
                              <td key={ci} className="px-3 py-2 text-muted-foreground border-b border-border/50">{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </motion.div>
            )}
          </div>

          <motion.button
            onClick={handleSubmit}
            disabled={!isValid || loading}
            className="btn-aerospace w-full text-sm flex items-center justify-center gap-2"
            whileHover={isValid && !loading ? { scale: 1.01 } : {}}
            whileTap={isValid && !loading ? { scale: 0.99 } : {}}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>Start Diagnosis <ChevronRight className="w-4 h-4" /></>
            )}
          </motion.button>
        </div>
      </div>
    </DashboardLayout>
  );
}
