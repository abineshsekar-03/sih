import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { AlertTriangle, Database } from 'lucide-react';
import AnomalyDrawer from '../components/AnomalyDrawer';

const Anomalies = () => {
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        const res = await axios.get('/api/anomalies');
        setAnomalies(res.data);
      } catch (err) {}
    };
    fetchAnomalies();
    const int = setInterval(fetchAnomalies, 10000);
    return () => clearInterval(int);
  }, []);

  return (
    <div className="h-full flex flex-col relative">
      <div className="flex items-center gap-3 mb-6">
        <Database className="w-5 h-5 text-atmos-accent" />
        <h1 className="text-xl font-bold tracking-widest text-atmos-text uppercase">Anomaly History</h1>
      </div>
      
      <div className="flex-1 bg-atmos-panel border border-atmos-border rounded overflow-hidden flex flex-col relative">
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-atmos-border via-atmos-warning/50 to-atmos-border z-10"></div>
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-sm">
            <thead className="bg-atmos-surface/50 border-b border-atmos-border sticky top-0 z-0">
              <tr>
                <th className="p-4 text-[10px] font-bold uppercase tracking-widest text-atmos-muted">Time</th>
                <th className="p-4 text-[10px] font-bold uppercase tracking-widest text-atmos-muted">Station</th>
                <th className="p-4 text-[10px] font-bold uppercase tracking-widest text-atmos-muted">Parameter</th>
                <th className="p-4 text-[10px] font-bold uppercase tracking-widest text-atmos-muted">Severity</th>
                <th className="p-4 text-[10px] font-bold uppercase tracking-widest text-atmos-muted">Attribution</th>
                <th className="p-4 text-[10px] font-bold uppercase tracking-widest text-atmos-muted">Evidence</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((a, i) => (
                <tr key={i} onClick={() => setSelected(a)} className={`border-b border-atmos-border/30 hover:bg-atmos-accent/5 cursor-pointer transition-colors ${a.severity === 'CRITICAL' ? 'bg-atmos-critical/5' : ''}`}>
                  <td className="p-4 text-xs font-mono text-atmos-muted">{new Date(a.timestamp).toLocaleString()}</td>
                  <td className="p-4 font-mono font-bold text-atmos-text">{a.station_id}</td>
                  <td className="p-4 uppercase text-[10px] tracking-wider text-atmos-muted">{a.parameter}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 border rounded text-[9px] font-bold tracking-widest uppercase ${a.severity === 'CRITICAL' ? 'bg-atmos-critical/10 border-atmos-critical text-atmos-critical' : (a.severity === 'HIGH' ? 'bg-atmos-warning/10 border-atmos-warning text-atmos-warning' : 'bg-atmos-accent/10 border-atmos-accent text-atmos-accent')}`}>
                      {a.severity}
                    </span>
                  </td>
                  <td className="p-4 text-xs font-semibold text-atmos-text">{a.attribution}</td>
                  <td className="p-4 font-mono text-sm text-atmos-muted">{a.evidence_score} <span className="text-[10px]">/100</span></td>
                </tr>
              ))}
              {anomalies.length === 0 && (
                <tr>
                   <td colSpan={6} className="p-8 text-center text-atmos-muted text-sm">No historical anomalies recorded.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      <AnomalyDrawer anomaly={selected} onClose={() => setSelected(null)} />
    </div>
  );
};
export default Anomalies;
