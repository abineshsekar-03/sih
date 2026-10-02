import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { MapPin, Activity, Radio, SignalHigh, AlertTriangle } from 'lucide-react';
import AnomalyDrawer from '../components/AnomalyDrawer';

const LiveMonitor = () => {
  const [stations, setStations] = useState<any[]>([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState<any>(null);

  useEffect(() => {
    const fetchStations = async () => {
      try {
        const res = await axios.get('/api/stations');
        setStations(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchStations();

    const eventSource = new EventSource('/api/live-feed');
    eventSource.addEventListener('reading', async (e) => {
      const data = JSON.parse(e.data);
      const r = data.reading;
      setStations(prev => prev.map(s => {
        if (s.id === r.station_id) {
          return {
            ...s,
            temp: r.temperature,
            hum: r.humidity,
            pres: r.pressure,
            status: data.station_status,
            health_score: data.station_health
          };
        }
        return s;
      }));

      // Auto-open drawer for demo purposes if critical
      if (data.anomaly && data.anomaly.severity === 'CRITICAL') {
        try {
          const res = await axios.get('/api/anomalies');
          const anom = res.data.find((a: any) => a.id === data.anomaly.id);
          if (anom) setSelectedAnomaly(anom);
        } catch (err) {}
      }
    });

    return () => eventSource.close();
  }, []);

  return (
    <div className="h-full flex flex-col relative">
      <div className="flex items-center gap-3 mb-6">
        <Radio className="w-5 h-5 text-atmos-accent" />
        <h1 className="text-xl font-bold tracking-widest text-atmos-text uppercase">Live Network Monitor</h1>
      </div>
      
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 auto-rows-max overflow-y-auto pb-6 pr-2">
        {stations.map(station => (
          <div key={station.id} className={`bg-atmos-panel border transition-all duration-300 relative overflow-hidden ${
            station.status === 'critical' ? 'border-atmos-critical shadow-[0_0_15px_rgba(239,91,97,0.15)]' : 
            station.status === 'warning' ? 'border-atmos-warning' : 
            'border-atmos-border hover:border-atmos-accent/50'
          }`}>
            {/* Status Top Bar */}
            <div className={`h-1 w-full ${
              station.status === 'critical' ? 'bg-atmos-critical' : 
              station.status === 'warning' ? 'bg-atmos-warning' : 
              'bg-atmos-healthy'
            }`} />

            <div className="p-4">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    station.status === 'critical' ? 'bg-atmos-critical animate-pulse' : 
                    station.status === 'warning' ? 'bg-atmos-warning' : 
                    'bg-atmos-healthy'
                  }`} />
                  <h3 className="font-mono font-bold text-lg text-atmos-text tracking-wide">{station.id}</h3>
                </div>
                <div className="flex items-center gap-3">
                   <div className="text-right">
                     <div className="text-[9px] uppercase tracking-widest text-atmos-muted">Health</div>
                     <div className={`text-sm font-bold ${station.health_score < 70 ? 'text-atmos-critical' : 'text-atmos-healthy'}`}>
                       {station.health_score} <span className="text-[10px] font-normal text-atmos-muted">/100</span>
                     </div>
                   </div>
                </div>
              </div>
              
              <div className="flex justify-between items-center mb-5 pb-3 border-b border-atmos-border/50">
                <div className="flex items-center gap-1.5 text-xs text-atmos-muted">
                  <MapPin className="w-3 h-3" />
                  {station.name}
                </div>
                <div className="flex items-center gap-1 text-[10px] text-atmos-muted uppercase tracking-wider">
                  <SignalHigh className="w-3 h-3 text-atmos-healthy" />
                  COMMS OK
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="flex flex-col">
                  <span className="text-[10px] text-atmos-muted uppercase tracking-wider mb-1">Temp</span>
                  <span className={`font-mono text-lg font-semibold ${station.status === 'critical' && station.temp > 40 ? 'text-atmos-critical' : 'text-atmos-text'}`}>
                    {station.temp !== undefined ? `${station.temp}°C` : '--'}
                  </span>
                </div>
                <div className="flex flex-col border-l border-r border-atmos-border/50 px-3">
                  <span className="text-[10px] text-atmos-muted uppercase tracking-wider mb-1">Pressure</span>
                  <span className="font-mono text-lg font-semibold text-atmos-text">
                    {station.pres !== undefined ? station.pres : '--'}
                  </span>
                </div>
                <div className="flex flex-col pl-3">
                  <span className="text-[10px] text-atmos-muted uppercase tracking-wider mb-1">RH</span>
                  <span className="font-mono text-lg font-semibold text-atmos-text">
                    {station.hum !== undefined ? `${station.hum}%` : '--'}
                  </span>
                </div>
              </div>

              {station.status === 'critical' && (
                <div className="mt-4 pt-3 border-t border-atmos-critical/20 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-atmos-critical text-xs font-bold tracking-widest uppercase">
                    <AlertTriangle className="w-4 h-4" />
                    Anomaly Detected
                  </div>
                  <button className="text-[10px] border border-atmos-critical text-atmos-critical px-2 py-1 uppercase font-bold hover:bg-atmos-critical hover:text-white transition-colors" onClick={() => setSelectedAnomaly(station)}>
                    Investigate
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <AnomalyDrawer anomaly={selectedAnomaly} onClose={() => setSelectedAnomaly(null)} />
    </div>
  );
};

export default LiveMonitor;
