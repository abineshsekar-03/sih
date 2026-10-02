import React from 'react';
import Sidebar from './Sidebar';

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex h-screen bg-atmos-bg overflow-hidden font-sans text-atmos-text">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="h-14 border-b border-atmos-border bg-atmos-panel/80 backdrop-blur-md flex items-center justify-between px-6 shrink-0 z-10 shadow-sm">
          <div className="flex items-center gap-3">
             <div className="w-1.5 h-6 bg-atmos-accent rounded-full"></div>
             <h2 className="text-sm font-bold tracking-widest text-atmos-muted uppercase">National Meteorological Command</h2>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-atmos-healthy animate-pulse shadow-[0_0_8px_#45D483]"></span>
              <span className="text-[10px] font-bold text-atmos-healthy tracking-widest">SYSTEM OPERATIONAL</span>
            </div>
            <div className="h-4 w-px bg-atmos-border"></div>
            <div className="w-7 h-7 rounded border border-atmos-accent/50 bg-atmos-accent/10 flex items-center justify-center font-bold text-xs text-atmos-accent">
              OP
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-4 md:p-6 bg-transparent relative">
          <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_top_right,_var(--color-atmos-panel),_transparent_50%)] opacity-30"></div>
          <div className="relative h-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
