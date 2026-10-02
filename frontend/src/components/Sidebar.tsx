import React from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, LayoutDashboard, Radio, AlertTriangle, ShieldAlert, BarChart2, Database, Network } from 'lucide-react';
import DemoController from './DemoController';

const Sidebar = () => {
  return (
    <aside className="w-64 bg-atmos-panel border-r border-atmos-border h-screen flex flex-col relative z-20">
      <div className="p-6 border-b border-atmos-border">
        <div className="flex items-center gap-3 mb-1">
          <Activity className="text-atmos-accent w-6 h-6" />
          <h1 className="font-bold text-2xl tracking-widest text-atmos-text">ATMOS-X</h1>
        </div>
        <p className="text-[9px] text-atmos-muted uppercase tracking-[0.2em] font-semibold">Automatic Weather Station Intelligence</p>
      </div>
      
      <div className="px-4 py-3 border-b border-atmos-border/50">
         <div className="text-[10px] text-atmos-muted tracking-widest font-semibold uppercase mb-2">Navigation</div>
         <nav className="space-y-1">
          <NavLink to="/" className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded transition-colors text-sm font-medium ${isActive ? 'bg-atmos-accent/10 text-atmos-accent border border-atmos-accent/20' : 'text-atmos-muted hover:text-atmos-text hover:bg-atmos-border/50 border border-transparent'}`}>
            <LayoutDashboard className="w-4 h-4" />
            Overview
          </NavLink>
          <NavLink to="/monitor" className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded transition-colors text-sm font-medium ${isActive ? 'bg-atmos-accent/10 text-atmos-accent border border-atmos-accent/20' : 'text-atmos-muted hover:text-atmos-text hover:bg-atmos-border/50 border border-transparent'}`}>
            <Radio className="w-4 h-4" />
            Live Monitor
          </NavLink>
          <NavLink to="/anomalies" className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded transition-colors text-sm font-medium ${isActive ? 'bg-atmos-accent/10 text-atmos-accent border border-atmos-accent/20' : 'text-atmos-muted hover:text-atmos-text hover:bg-atmos-border/50 border border-transparent'}`}>
            <AlertTriangle className="w-4 h-4" />
            Anomalies
          </NavLink>
          <NavLink to="/stations" className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded transition-colors text-sm font-medium ${isActive ? 'bg-atmos-accent/10 text-atmos-accent border border-atmos-accent/20' : 'text-atmos-muted hover:text-atmos-text hover:bg-atmos-border/50 border border-transparent'}`}>
            <Network className="w-4 h-4" />
            Stations
          </NavLink>
        </nav>
      </div>

      <div className="px-4 py-3 flex-1">
         <div className="text-[10px] text-atmos-muted tracking-widest font-semibold uppercase mb-2">Analysis</div>
         <nav className="space-y-1">
          <NavLink to="/health" className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded transition-colors text-sm font-medium ${isActive ? 'bg-atmos-accent/10 text-atmos-accent border border-atmos-accent/20' : 'text-atmos-muted hover:text-atmos-text hover:bg-atmos-border/50 border border-transparent'}`}>
            <Activity className="w-4 h-4" />
            Health
          </NavLink>
          <NavLink to="/analytics" className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded transition-colors text-sm font-medium ${isActive ? 'bg-atmos-accent/10 text-atmos-accent border border-atmos-accent/20' : 'text-atmos-muted hover:text-atmos-text hover:bg-atmos-border/50 border border-transparent'}`}>
            <BarChart2 className="w-4 h-4" />
            Analytics
          </NavLink>
          <NavLink to="/alerts" className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded transition-colors text-sm font-medium ${isActive ? 'bg-atmos-accent/10 text-atmos-accent border border-atmos-accent/20' : 'text-atmos-muted hover:text-atmos-text hover:bg-atmos-border/50 border border-transparent'}`}>
            <ShieldAlert className="w-4 h-4" />
            Alerts
          </NavLink>
          <NavLink to="/data-quality" className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded transition-colors text-sm font-medium ${isActive ? 'bg-atmos-accent/10 text-atmos-accent border border-atmos-accent/20' : 'text-atmos-muted hover:text-atmos-text hover:bg-atmos-border/50 border border-transparent'}`}>
            <Database className="w-4 h-4" />
            Data Quality
          </NavLink>
        </nav>
      </div>

      <div className="p-4 border-t border-atmos-border bg-atmos-surface">
        <DemoController />
      </div>
    </aside>
  );
};

export default Sidebar;
