import React, { useState } from 'react';
import axios from 'axios';
import { Play, Square, RotateCcw, AlertTriangle, Settings } from 'lucide-react';

const API_URL = '/api';

const DemoController = () => {
  const [status, setStatus] = useState('Stopped');
  const [scenario, setScenario] = useState('NORMAL');

  const handleStart = async () => {
    await axios.post(`${API_URL}/simulation/start`);
    setStatus('Running');
  };

  const handlePause = async () => {
    await axios.post(`${API_URL}/simulation/pause`);
    setStatus('Paused');
  };

  const handleReset = async () => {
    await axios.post(`${API_URL}/simulation/reset`);
    setStatus('Stopped');
  };

  const handleInject = async () => {
    if (scenario !== 'NORMAL') {
      await axios.post(`${API_URL}/simulation/inject`, { scenario });
    }
  };

  return (
    <div className="bg-atmos-panel rounded border border-atmos-border p-4 relative overflow-hidden">
      {/* Top tech lines */}
      <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-atmos-border via-atmos-accent/50 to-atmos-border"></div>
      
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[10px] font-bold text-atmos-muted uppercase tracking-widest flex items-center gap-1.5">
          <Settings className="w-3 h-3" />
          Live Demo Control
        </h3>
        <div className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${status === 'Running' ? 'bg-atmos-healthy animate-pulse' : 'bg-atmos-muted'}`}></span>
          <span className="text-[9px] font-bold text-atmos-text uppercase tracking-widest">{status}</span>
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        <button onClick={handleStart} className="flex-1 bg-atmos-bg border border-atmos-border hover:border-atmos-healthy hover:text-atmos-healthy text-atmos-text rounded py-1.5 flex justify-center transition-colors">
          <Play className="w-3.5 h-3.5" />
        </button>
        <button onClick={handlePause} className="flex-1 bg-atmos-bg border border-atmos-border hover:border-atmos-warning hover:text-atmos-warning text-atmos-text rounded py-1.5 flex justify-center transition-colors">
          <Square className="w-3.5 h-3.5" />
        </button>
        <button onClick={handleReset} className="flex-1 bg-atmos-bg border border-atmos-border hover:border-atmos-accent hover:text-atmos-accent text-atmos-text rounded py-1.5 flex justify-center transition-colors">
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="space-y-2">
        <select 
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
          className="w-full bg-atmos-bg border border-atmos-border rounded p-2 text-xs text-atmos-text focus:outline-none focus:border-atmos-accent tracking-wide"
        >
          <option value="NORMAL">Normal Operation</option>
          <option value="TEMPERATURE_SPIKE">Temperature Spike (ST07)</option>
          <option value="HUMIDITY_FAULT">Humidity Fault (ST05)</option>
          <option value="PRESSURE_DRIFT">Pressure Drift (ST09)</option>
          <option value="FLATLINE">Flatline Sensor (ST02)</option>
          <option value="SPATIAL_OUTLIER">Spatial Outlier (ST04)</option>
        </select>
        <button 
          onClick={handleInject}
          disabled={scenario === 'NORMAL'}
          className="w-full bg-atmos-critical/10 hover:bg-atmos-critical/20 text-atmos-critical border border-atmos-critical/50 rounded py-2 text-[10px] font-bold tracking-widest uppercase flex items-center justify-center gap-2 transition-colors disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-atmos-critical/10"
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          Inject Anomaly
        </button>
      </div>
    </div>
  );
};

export default DemoController;
