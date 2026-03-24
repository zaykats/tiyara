import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [show, setShow] = useState(true);

  useEffect(() => {
    const t1 = setTimeout(() => setShow(false), 2400);
    const t2 = setTimeout(onComplete, 2800);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [onComplete]);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          className="fixed inset-0 z-[9999] bg-background flex flex-col items-center justify-center overflow-hidden gap-6"
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4, ease: [0.2, 0, 0, 1] }}
        >
          {/* Ambient glow */}
          <div className="absolute inset-0 pointer-events-none" style={{
            background: 'radial-gradient(ellipse at 50% 60%, hsl(338 100% 18% / 0.07) 0%, transparent 60%)',
          }} />

          {/* Ticket card */}
          <motion.div
            className="container-cards-ticket"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.2, 0, 0, 1] }}
          >
            <div className="card-ticket">
              {/* Barcode */}
              <svg xmlns="http://www.w3.org/2000/svg" width="64" height="150" viewBox="0 0 64 150" fill="black">
                <path d="M44 138V136.967H20V138H44Z" />
                <path d="M44 13.0328V12H20V13.0328H44Z" />
                <path d="M44 14.0656V13.5492H20V14.0656H44Z" />
                <path d="M44 15.6148V15.0984H20V15.6148H44Z" />
                <path d="M44 18.1967V17.6803H20V18.1967H44Z" />
                <path d="M44 20.2623V19.2295H20V20.2623H44Z" />
                <path d="M44 22.8443V22.3279H20V22.8443H44Z" />
                <path d="M44 23.877V23.3607H20V23.877H44Z" />
                <path d="M44 26.9754V24.9098H20V26.9754H44Z" />
                <path d="M44 28.0082V27.4918H20V28.0082H44Z" />
                <path d="M44 29.5574V29.041H20V29.5574H44Z" />
                <path d="M44 32.6557V30.5902H20V32.6557H44Z" />
                <path d="M44 33.6885V33.1721H20V33.6885H44Z" />
                <path d="M44 35.2376V34.7213H20V35.2376H44Z" />
                <path d="M44 36.2705V35.7541H20V36.2705H44Z" />
                <path d="M44 39.3689V37.3033H20V39.3689H44Z" />
                <path d="M44 40.918V40.4015H20V40.918H44Z" />
                <path d="M44 43.5001V41.4345H20V43.5001H44Z" />
                <path d="M44 45.0492V44.5327H20V45.0492H44Z" />
                <path d="M44 47.631V46.0819H20V47.631H44Z" />
                <path d="M44 49.1804V48.664H20V49.1804H44Z" />
                <path d="M44 51.2458V50.2131H20V51.2458H44Z" />
                <path d="M44 52.2787V51.7622H20V52.2787H44Z" />
                <path d="M44 54.3443V52.7952H20V54.3443H44Z" />
                <path d="M44 56.4099V55.377H20V56.4099H44Z" />
                <path d="M44 57.959V57.4426H20V57.959H44Z" />
                <path d="M44 60.0247V58.4753H20V60.0247H44Z" />
                <path d="M44 62.09V61.0573H20V62.09H44Z" />
                <path d="M44 63.6394V63.123H20V63.6394H44Z" />
                <path d="M44 66.7377V64.6721H20V66.7377H44Z" />
                <path d="M44 68.2868V67.7704H20V68.2868H44Z" />
                <path d="M44 69.3198V68.8033H20V69.3198H44Z" />
                <path d="M44 72.4181V71.3851H20V72.4181H44Z" />
                <path d="M44 73.4508V72.9345H20V73.4508H44Z" />
                <path d="M44 76.5493V74.4837H20V76.5493H44Z" />
                <path d="M44 77.5819V77.0655H20V77.5819H44Z" />
                <path d="M44 79.1311V78.6146H20V79.1311H44Z" />
                <path d="M44 80.6802V80.164H20V80.6802H44Z" />
                <path d="M44 82.2294V81.1967H20V82.2294H44Z" />
                <path d="M44 83.7788V83.2623H20V83.7788H44Z" />
                <path d="M44 86.3606V85.8441H20V86.3606H44Z" />
                <path d="M44 87.9097V87.3935H20V87.9097H44Z" />
                <path d="M44 91.0083V88.9427H20V91.0083H44Z" />
                <path d="M44 92.041V91.5245H20V92.041H44Z" />
                <path d="M44 94.623V92.5574H20V94.623H44Z" />
                <path d="M44 96.1722V95.6557H20V96.1722H44Z" />
                <path d="M44 97.7213V97.2048H20V97.7213H44Z" />
                <path d="M44 99.2704V98.2378H20V99.2704H44Z" />
                <path d="M44 100.82V100.303H20V100.82H44Z" />
                <path d="M44 103.402V102.885H20V103.402H44Z" />
                <path d="M44 105.467V104.434H20V105.467H44Z" />
                <path d="M44 108.049V106.5H20V108.049H44Z" />
                <path d="M44 109.082V108.566H20V109.082H44Z" />
                <path d="M44 112.18V111.148H20V112.18H44Z" />
                <path d="M44 113.213V112.697H20V113.213H44Z" />
                <path d="M44 114.762V114.246H20V114.762H44Z" />
                <path d="M44 118.377V116.311H20V118.377H44Z" />
                <path d="M44 119.41V118.893H20V119.41H44Z" />
                <path d="M44 120.442V119.926H20V120.442H44Z" />
                <path d="M44 122.508V120.959H20V122.508H44Z" />
                <path d="M44 124.574V123.541H20V124.574H44Z" />
                <path d="M44 127.672V125.607H20V127.672H44Z" />
                <path d="M44 128.705V128.188H20V128.705H44Z" />
                <path d="M44 130.254V129.738H20V130.254H44Z" />
                <path d="M44 132.32V131.287H20V132.32H44Z" />
                <path d="M44 135.418V133.869H20V135.418H44Z" />
                <path d="M44 136.451V135.934H20V136.451H44Z" />
              </svg>

              {/* Dashed separator */}
              <div className="separator">
                <span className="span-lines" />
              </div>

              {/* Content */}
              <div className="content-ticket">
                <div className="content-data">
                  {/* Route */}
                  <div className="destination">
                    <div className="dest start">
                      <p className="country">Fault</p>
                      <p className="acronym">FLT</p>
                      <p className="hour">
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 1024 1024">
                          <path fill="currentColor" d="M768 256H353.6a32 32 0 1 1 0-64H800a32 32 0 0 1 32 32v448a32 32 0 0 1-64 0z" />
                          <path fill="currentColor" d="M777.344 201.344a32 32 0 0 1 45.312 45.312l-544 544a32 32 0 0 1-45.312-45.312z" />
                        </svg>
                        08:00
                      </p>
                    </div>
                    <svg style={{ flexShrink: 0 }} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                      <path fill="none" stroke="#aeaeae" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="m18 8l4 4l-4 4M2 12h20" />
                    </svg>
                    <div className="dest end">
                      <p className="country">Cleared</p>
                      <p className="acronym">CLR</p>
                      <p className="hour">
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 1024 1024">
                          <path fill="currentColor" d="M352 768a32 32 0 1 0 0 64h448a32 32 0 0 0 32-32V352a32 32 0 0 0-64 0v416z" />
                          <path fill="currentColor" d="M777.344 822.656a32 32 0 0 0 45.312-45.312l-544-544a32 32 0 0 0-45.312 45.312z" />
                        </svg>
                        --:--
                      </p>
                    </div>
                  </div>

                  <div style={{ borderBottom: "2px solid #e8e8e8" }} />

                  <div className="data-flex-col">
                    <div className="data-flex">
                      <div className="data">
                        <p className="title">ID</p>
                        <p className="subtitle">TY-2025</p>
                      </div>
                      <div className="data passenger">
                        <p className="title">System</p>
                        <p className="subtitle">TIYARA</p>
                      </div>
                    </div>
                    <div className="data-flex">
                      <div className="data">
                        <p className="title">Flight</p>
                        <p className="subtitle">TY-AI</p>
                      </div>
                      <div className="data">
                        <p className="title">Ref</p>
                        <p className="subtitle">AMM</p>
                      </div>
                      <div className="data">
                        <p className="title">Mode</p>
                        <p className="subtitle">RAG</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right color panel */}
                <div className="container-icons">
                  <div className="icon plane">
                    <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24">
                      <path fill="currentColor" d="M20.56 3.91c.59.59.59 1.54 0 2.12l-3.89 3.89l2.12 9.19l-1.41 1.42l-3.88-7.43L9.6 17l.36 2.47l-1.07 1.06l-1.76-3.18l-3.19-1.77L5 14.5l2.5.37L11.37 11L3.94 7.09l1.42-1.41l9.19 2.12l3.89-3.89c.56-.58 1.56-.58 2.12 0" />
                    </svg>
                  </div>
                  <div className="icon" style={{ fontWeight: 700, fontSize: 11, letterSpacing: "0.1em" }}>
                    AI
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Brand label */}
          <motion.div
            className="relative z-10 text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <p className="font-mono-tech text-[10px] text-muted-foreground/50 tracking-[0.25em]">
              AEROSPACE MAINTENANCE PLATFORM
            </p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
