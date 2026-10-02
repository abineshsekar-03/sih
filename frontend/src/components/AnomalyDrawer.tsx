import React from 'react';
import { X, CheckCircle, ShieldAlert, AlertOctagon, Info, ArrowRight, Activity, Cpu, Radio, Network } from 'lucide-react';
import axios from 'axios';

const AnomalyDrawer = ({ anomaly, onClose }: { anomaly: any, onClose: () => void }) => {
  if (!anomaly) return null;

  const handleQuarantine = async () => {
    // In a full implementation, this would call an API to update trust state
    try {
      // await axios.post(`/api/anomalies/${anomaly.id}/quarantine`);
      onClose();
    } catch (e) {
      console.error(e);
      onClose(); // close anyway for demo
    }
  };

  const getDeviation = () => {
    if (anomaly.observed_value !== null && anomaly.expected_value !== null) {
      const diff = anomaly.observed_value - anomaly.expected_value;
      return diff > 0 ? `+${diff.toFixed(1)}` : diff.toFixed(1);
    }
    return 'N/A';
  };

  const explanations = anomaly.explanation ? anomaly.explanation.split('\n') : [];
  
  const hasEvidence = (engine: string) => {
    return explanations.some((e: string) => e.toLowerCase().includes(engine.toLowerCase()));
  };

  const evidenceChain = [
    { name: 'RULE ENGINE', icon: <CheckCircle className="w-3 h-3" />, detected: hasEvidence('rule') },
    { name: 'PHYSICS', icon: <Activity className="w-3 h-3" />, detected: hasEvidence('physics') },
    { name: 'TEMPORAL', icon: <Radio className="w-3 h-3" />, detected: hasEvidence('temporal') },
    { name: 'SPATIAL', icon: <Network className="w-3 h-3" />, detected: hasEvidence('spatial') },
    { name: 'MACHINE LEARNING', icon: <Cpu className="w-3 h-3" />, detected: hasEvidence('ml') }
  ];

  return (
    <div className="absolute top-0 right-0 h-full w-[450px] bg-atmos-surface border-l border-atmos-border shadow-[-10px_0_30px_rgba(0,0,0,0.5)] z-50 flex flex-col transform transition-transform duration-300 font-sans">
      
      {/* Header */}
      <div className={`p-5 flex justify-between items-start border-b ${
        anomaly.severity === 'CRITICAL' ? 'border-atmos-critical/30 bg-atmos-critical/10' : 
        anomaly.severity === 'HIGH' ? 'border-atmos-warning/30 bg-atmos-warning/10' : 
        'border-atmos-border bg-atmos-panel'
      }`}>
        <div>
          <h2 className="text-[10px] tracking-widest text-atmos-muted font-bold mb-1">ANOMALY INVESTIGATION</h2>
          <div className="flex items-center gap-3">
             <div className="text-2xl font-bold text-atmos-text">{anomaly.station_id}</div>
             <div className="px-2 py-0.5 border border-atmos-border text-xs rounded text-atmos-muted uppercase tracking-wider bg-atmos-bg">
               {anomaly.parameter || 'TEMPERATURE SENSOR'}
             </div>
          </div>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-white/10 rounded text-atmos-muted hover:text-atmos-text transition-colors">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 bg-atmos-bg">
        
        {/* Value Analysis */}
        <div className="grid grid-cols-3 gap-4">
          <div className="flex flex-col border-l-2 border-atmos-critical pl-3">
            <span className="text-[10px] text-atmos-muted uppercase tracking-widest mb-1">Observed</span>
            <span className="font-mono text-2xl font-semibold text-atmos-critical">{anomaly.observed_value !== null ? anomaly.observed_value : '--'}</span>
          </div>
          <div className="flex flex-col border-l-2 border-atmos-healthy pl-3">
            <span className="text-[10px] text-atmos-muted uppercase tracking-widest mb-1">Expected</span>
            <span className="font-mono text-2xl font-semibold text-atmos-healthy">{anomaly.expected_value !== null ? anomaly.expected_value.toFixed(1) : '--'}</span>
          </div>
          <div className="flex flex-col border-l-2 border-atmos-warning pl-3">
            <span className="text-[10px] text-atmos-muted uppercase tracking-widest mb-1">Deviation</span>
            <span className="font-mono text-2xl font-semibold text-atmos-warning">{getDeviation()}</span>
          </div>
        </div>

        {/* Evidence Chain */}
        <div>
          <h3 className="text-[10px] font-bold tracking-widest text-atmos-muted uppercase mb-3 flex items-center gap-2">
            Evidence Chain
            <div className="h-px flex-1 bg-atmos-border"></div>
          </h3>
          <div className="bg-atmos-panel border border-atmos-border rounded p-4 relative overflow-hidden">
             {/* Vertical line connector */}
             <div className="absolute left-6 top-6 bottom-6 w-px bg-atmos-border z-0"></div>
             
             <div className="space-y-4 relative z-10">
               {evidenceChain.map((layer, idx) => (
                 <div key={idx} className="flex items-center gap-4">
                   <div className={`w-5 h-5 rounded-full flex items-center justify-center border bg-atmos-panel ${layer.detected ? 'border-atmos-critical text-atmos-critical shadow-[0_0_8px_rgba(239,91,97,0.3)]' : 'border-atmos-border text-atmos-muted'}`}>
                     {layer.icon}
                   </div>
                   <div className="flex-1 flex justify-between items-center text-xs">
                     <span className={`font-mono ${layer.detected ? 'text-atmos-text' : 'text-atmos-muted'}`}>{layer.name}</span>
                     <span className={`font-bold uppercase tracking-wider ${layer.detected ? 'text-atmos-critical' : 'text-atmos-muted'}`}>
                       {layer.detected ? '✓ DETECTED' : '— NORMAL'}
                     </span>
                   </div>
                 </div>
               ))}
               <div className="flex items-center gap-4 pt-2">
                  <div className="w-5 h-5 flex items-center justify-center">
                    <ArrowRight className="w-4 h-4 text-atmos-accent" />
                  </div>
                  <div className="flex-1 border-t border-atmos-border pt-3 flex justify-between items-center">
                    <span className="text-xs font-mono text-atmos-accent">EVIDENCE FUSION</span>
                  </div>
               </div>
             </div>
          </div>
        </div>

        {/* Evidence Score */}
        <div className="flex gap-4">
          <div className="flex-1 bg-atmos-panel border border-atmos-border rounded p-4 flex flex-col justify-center items-center">
             <div className="text-4xl font-bold text-atmos-text mb-1">
               {anomaly.evidence_score} <span className="text-lg text-atmos-muted font-normal">/ 100</span>
             </div>
             <div className="text-[10px] text-atmos-muted tracking-widest uppercase text-center">Evidence Agreement Score</div>
          </div>
          <div className="flex-1 bg-atmos-panel border border-atmos-border rounded p-4 flex flex-col justify-center items-center">
             <div className={`text-xl font-bold mb-1 uppercase tracking-wider ${anomaly.trust_state === 'QUARANTINE' || anomaly.trust_state === 'REJECT' ? 'text-atmos-critical' : 'text-atmos-warning'}`}>
               {anomaly.trust_state}
             </div>
             <div className="text-[10px] text-atmos-muted tracking-widest uppercase text-center">Trust State</div>
          </div>
        </div>

        {/* Why Flagged */}
        <div>
          <h3 className="text-[10px] font-bold tracking-widest text-atmos-muted uppercase mb-3 flex items-center gap-2">
            Why was this flagged?
            <div className="h-px flex-1 bg-atmos-border"></div>
          </h3>
          <div className="text-sm text-atmos-text space-y-2">
            {explanations.map((exp: string, idx: number) => (
              <p key={idx} className="flex gap-2">
                <span className="text-atmos-critical">•</span>
                <span>{exp.replace('• ', '')}</span>
              </p>
            ))}
          </div>
        </div>

        {/* Root Cause & Action */}
        <div className="bg-atmos-surface border border-atmos-border rounded p-4 space-y-4">
          <div>
            <div className="text-[10px] text-atmos-muted uppercase tracking-widest mb-1">Likely Cause</div>
            <div className="text-sm font-semibold text-atmos-text">{anomaly.root_cause || anomaly.attribution}</div>
          </div>
          <div>
            <div className="text-[10px] text-atmos-muted uppercase tracking-widest mb-1">Recommended Action</div>
            <div className="text-sm text-atmos-text">
              {anomaly.trust_state === 'QUARANTINE' || anomaly.trust_state === 'REJECT' ? 
                'Quarantine observation. Inspect temperature sensor. Compare calibration. Continue monitoring station.' : 
                'Monitor station for further deviations. Acknowledge alert.'}
            </div>
          </div>
        </div>

      </div>

      {/* Footer Actions */}
      <div className="p-5 border-t border-atmos-border bg-atmos-panel flex flex-col gap-3 shrink-0">
        <button onClick={handleQuarantine} className="w-full bg-atmos-critical/10 border border-atmos-critical hover:bg-atmos-critical text-atmos-critical hover:text-white font-bold tracking-widest uppercase py-3 text-xs transition-colors">
          [ Quarantine ]
        </button>
        <button onClick={onClose} className="w-full bg-transparent border border-atmos-border text-atmos-muted hover:text-atmos-text hover:border-atmos-muted font-bold tracking-widest uppercase py-3 text-xs transition-colors">
          [ Acknowledge ]
        </button>
      </div>
    </div>
  );
};

export default AnomalyDrawer;
