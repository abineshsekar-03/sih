import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Activity, Radio, AlertTriangle, ShieldCheck, Thermometer, Wind, Droplets } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const Overview = () => {
  const [stats, setStats] = useState({ total: 10, healthy: 10, activeAnomalies: 0, critical: 0, dataQuality: 98.4 });
  const [chartData, setChartData] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [stations, setStations] = useState<any[]>([]);
  const [latestReading, setLatestReading] = useState<{temp: number | string, hum: number | string, pres: number | string}>({temp: '--', hum: '--', pres: '--'});
  const [connectionStatus, setConnectionStatus] = useState('CONNECTING');

  const fetchInitialData = async () => {
    try {
      // 1. Fetch anomalies
      const resAnom = await axios.get('/api/anomalies');
      setAnomalies(resAnom.data.slice(0, 8));
      const criticalCount = resAnom.data.filter((a: any) => a.severity === 'CRITICAL').length;
      
      // 2. Fetch stations
      const resStat = await axios.get('/api/stations');
      setStations(resStat.data);
      const total = resStat.data.length;
      const healthy = resStat.data.filter((s: any) => s.status === 'healthy').length;
      
      setStats(prev => ({ 
        ...prev, 
        total, 
        healthy,
        activeAnomalies: resAnom.data.length, 
        critical: criticalCount 
      }));

      // 3. Fetch historical readings
      const resReadings = await axios.get('/api/readings?limit=300'); // 300 covers ~30 ticks across 10 stations
      
      // Filter for ST07 to avoid zigzag (or calculate averages)
      const st07_readings = resReadings.data.filter((r: any) => r.station_id === 'ST07').slice(-30);
      
      const formattedData = st07_readings.map((r: any) => ({
        time: new Date(r.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}),
        temp: r.temperature,
        pressure: r.pressure,
        hum: r.humidity,
        isAnomaly: r.temperature > 40 // simple historical logic
      }));
      setChartData(formattedData);

      if (st07_readings.length > 0) {
        const last = st07_readings[st07_readings.length - 1];
        setLatestReading({ temp: last.temperature, hum: last.humidity, pres: last.pressure });
      }

      // 4. Check simulator status
      const resSim = await axios.get('/api/simulation/status');
      setConnectionStatus(resSim.data.running ? 'CONNECTED' : 'PAUSED');

    } catch (err) {
      console.error("Error fetching initial data", err);
      setConnectionStatus('DISCONNECTED');
    }
  };

  useEffect(() => {
    fetchInitialData();
    // Poll for stations & anomalies periodically to stay in sync if missed SSE
    const interval = setInterval(fetchInitialData, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const eventSource = new EventSource('/api/live-feed');
    
    eventSource.onopen = () => {
      setConnectionStatus(prev => prev === 'PAUSED' ? 'PAUSED' : 'CONNECTED');
    };

    eventSource.addEventListener('reading', (e) => {
      const data = JSON.parse(e.data);
      const r = data.reading;
      
      // Update latest reading visually if it's ST07
      if (r.station_id === 'ST07') {
        setLatestReading({ temp: r.temperature, hum: r.humidity, pres: r.pressure });
        
        setChartData(prev => {
          const newD = [...prev, { 
            time: new Date(r.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}), 
            temp: r.temperature, 
            pressure: r.pressure,
            hum: r.humidity,
            isAnomaly: data.anomaly ? true : false,
            severity: data.anomaly?.severity
          }];
          if (newD.length > 30) newD.shift();
          return newD;
        });
      }

      // Realtime network/station update logic
      if (data.anomaly || data.station_status) {
        // Trigger a re-fetch of anomalies/stations to keep it simple and accurate
        fetchInitialData();
      }
    });

    eventSource.onerror = () => {
      setConnectionStatus('RECONNECTING');
    };

    return () => eventSource.close();
  }, []);

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Top Intelligence Strip */}
      <div className="bg-atmos-panel border border-atmos-border rounded flex items-center justify-between px-6 py-3 shadow-lg shrink-0">
        <div className="flex gap-8">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-atmos-accent" />
            <span className="text-atmos-muted text-xs font-semibold tracking-wider uppercase">Active Stations</span>
            <span className="text-atmos-text font-bold ml-1">{stats.total}</span>
          </div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-atmos-healthy" />
            <span className="text-atmos-muted text-xs font-semibold tracking-wider uppercase">Healthy</span>
            <span className="text-atmos-text font-bold ml-1">{stats.healthy}</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-atmos-warning" />
            <span className="text-atmos-muted text-xs font-semibold tracking-wider uppercase">Anomalies</span>
            <span className="text-atmos-text font-bold ml-1">{stats.activeAnomalies}</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-atmos-critical" />
            <span className="text-atmos-muted text-xs font-semibold tracking-wider uppercase">Critical</span>
            <span className="text-atmos-critical font-bold ml-1">{stats.critical}</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-atmos-accent" />
            <span className="text-atmos-muted text-xs font-semibold tracking-wider uppercase">Data Quality</span>
            <span className="text-atmos-text font-bold ml-1">{stats.dataQuality}%</span>
          </div>
        </div>
        <div className="flex flex-col items-end">
          <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${connectionStatus === 'CONNECTED' ? 'bg-atmos-critical animate-pulse' : (connectionStatus === 'PAUSED' ? 'bg-atmos-muted' : 'bg-atmos-warning')} `} />
            <span className={`text-xs tracking-widest font-bold ${connectionStatus === 'CONNECTED' ? 'text-atmos-critical' : 'text-atmos-muted'}`}>LIVE TELEMETRY</span>
          </div>
          <span className="text-[9px] text-atmos-muted uppercase font-bold tracking-widest mt-0.5">{connectionStatus}</span>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        
        {/* Main Visual: Atmospheric Signal */}
        <div className="col-span-9 flex flex-col gap-4 min-h-0">
          <div className="flex-1 bg-atmos-panel border border-atmos-border rounded p-4 flex flex-col shadow-lg relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-atmos-accent to-transparent opacity-50" />
            
            <div className="flex justify-between items-start mb-2">
              <div>
                <h2 className="text-atmos-text font-semibold tracking-wide flex items-center gap-2">
                  <Activity className="w-4 h-4 text-atmos-accent" />
                  ATMOSPHERIC SIGNAL MONITOR (ST07)
                </h2>
                <p className="text-xs text-atmos-muted">Real-time T/P/RH multivariate baseline tracking</p>
              </div>
              <div className="flex gap-4">
                <div className="flex flex-col items-end">
                   <div className="text-[10px] text-atmos-muted uppercase tracking-widest">Temperature</div>
                   <div className="text-lg font-bold text-atmos-text font-mono">{latestReading.temp} <span className="text-xs text-atmos-muted font-sans">°C</span></div>
                </div>
                <div className="w-px bg-atmos-border"></div>
                <div className="flex flex-col items-end">
                   <div className="text-[10px] text-atmos-muted uppercase tracking-widest">Pressure</div>
                   <div className="text-lg font-bold text-atmos-text font-mono">{latestReading.pres} <span className="text-xs text-atmos-muted font-sans">hPa</span></div>
                </div>
                <div className="w-px bg-atmos-border"></div>
                <div className="flex flex-col items-end">
                   <div className="text-[10px] text-atmos-muted uppercase tracking-widest">Humidity</div>
                   <div className="text-lg font-bold text-atmos-text font-mono">{latestReading.hum} <span className="text-xs text-atmos-muted font-sans">%</span></div>
                </div>
              </div>
            </div>

            {chartData.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-sm text-atmos-muted border border-dashed border-atmos-border/50 rounded mt-4">
                <div className="mb-2">NO TELEMETRY AVAILABLE</div>
                <div className="text-xs">Start the live simulation to begin receiving AWS observations.</div>
              </div>
            ) : (
              <div className="flex-1 min-h-0 mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="2 2" stroke="#203247" vertical={false} />
                    <XAxis dataKey="time" stroke="#8FA3B8" fontSize={10} tickMargin={8} minTickGap={20} />
                    <YAxis yAxisId="left" stroke="#39C6E8" fontSize={10} domain={['auto', 'auto']} />
                    <YAxis yAxisId="right" orientation="right" stroke="#8FA3B8" fontSize={10} domain={['auto', 'auto']} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#101D2E', borderColor: '#203247', fontSize: '12px' }} 
                      itemStyle={{ padding: 0 }}
                    />
                    <Line yAxisId="left" type="monotone" dataKey="temp" name="Temperature" stroke="#39C6E8" strokeWidth={2} dot={(props: any) => {
                      if (props.payload.isAnomaly) {
                        return <circle key={`dot-${props.index}`} cx={props.cx} cy={props.cy} r={5} fill="#EF5B61" stroke="#101D2E" strokeWidth={2} />;
                      }
                      return <span key={`dot-${props.index}`}/>;
                    }} isAnimationActive={false} />
                    <Line yAxisId="right" type="monotone" dataKey="hum" name="Humidity" stroke="#8FA3B8" strokeWidth={1} strokeDasharray="3 3" dot={false} isAnimationActive={false} />
                    <ReferenceLine yAxisId="left" y={31.8} stroke="#45D483" strokeDasharray="3 3" strokeOpacity={0.5} label={{ position: 'insideTopLeft', value: 'Expected Baseline', fill: '#45D483', fontSize: 10 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Bottom Row: Network & Critical Event */}
          <div className="h-48 grid grid-cols-2 gap-4 shrink-0">
            
            {/* Station Network Map (Abstract) */}
            <div className="bg-atmos-panel border border-atmos-border rounded p-4 flex flex-col relative overflow-hidden">
              <h3 className="text-xs font-semibold text-atmos-muted tracking-widest mb-3">STATION NETWORK</h3>
              <div className="flex-1 relative flex items-center justify-center">
                <svg className="absolute inset-0 w-full h-full opacity-30" viewBox="0 0 100 100" preserveAspectRatio="none">
                  <path d="M20,50 L50,20 L80,50 L50,80 Z" fill="none" stroke="#39C6E8" strokeWidth="0.5" />
                  <path d="M10,30 L90,30 M10,70 L90,70" fill="none" stroke="#203247" strokeWidth="0.5" strokeDasharray="2 2" />
                </svg>
                <div className="relative w-full h-full">
                  {stations.map((s, idx) => {
                    const positions = [
                      {top: '20%', left: '20%'}, {top: '50%', left: '10%'}, {top: '30%', left: '50%'},
                      {top: '80%', left: '40%'}, {top: '50%', left: '80%'}, {top: '70%', left: '70%'},
                      {top: '10%', left: '80%'}, {top: '90%', left: '10%'}, {top: '60%', left: '40%'},
                      {top: '40%', left: '90%'}
                    ];
                    const pos = positions[idx % positions.length];
                    const isCritical = s.status === 'critical';
                    const isWarning = s.status === 'warning';
                    
                    let bg = 'bg-atmos-healthy';
                    if (isCritical) bg = 'bg-atmos-critical shadow-[0_0_12px_#EF5B61] animate-pulse';
                    else if (isWarning) bg = 'bg-atmos-warning';

                    return (
                      <div key={s.id} className={`absolute w-2 h-2 rounded-full ${bg}`} style={{ top: pos.top, left: pos.left }} title={`${s.id} (${s.status})`} />
                    );
                  })}
                  {/* Dynamic critical lines could be added based on station status */}
                  <svg className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'none' }}>
                    {stations.map((s, idx) => {
                      if (s.status === 'critical') {
                        const positions = [
                          {top: '20%', left: '20%'}, {top: '50%', left: '10%'}, {top: '30%', left: '50%'},
                          {top: '80%', left: '40%'}, {top: '50%', left: '80%'}, {top: '70%', left: '70%'},
                          {top: '10%', left: '80%'}, {top: '90%', left: '10%'}, {top: '60%', left: '40%'},
                          {top: '40%', left: '90%'}
                        ];
                        const pos = positions[idx % positions.length];
                        return (
                           <React.Fragment key={`line-${s.id}`}>
                             <line x1="50%" y1="30%" x2={pos.left} y2={pos.top} stroke="#EF5B61" strokeWidth="1" strokeOpacity="0.4" strokeDasharray="2 2" />
                             <line x1="30%" y1="70%" x2={pos.left} y2={pos.top} stroke="#EF5B61" strokeWidth="1" strokeOpacity="0.4" strokeDasharray="2 2" />
                           </React.Fragment>
                        );
                      }
                      return null;
                    })}
                  </svg>
                </div>
              </div>
            </div>

            {/* Critical Incident Summary */}
            <div className="bg-atmos-panel border-l-4 border-atmos-critical rounded p-4 flex flex-col shadow-[inset_4px_0_0_0_#EF5B61] overflow-hidden">
               <h3 className="text-xs font-bold text-atmos-critical tracking-widest mb-1 flex items-center gap-2">
                 <AlertTriangle className="w-3 h-3" />
                 CRITICAL INCIDENT
               </h3>
               {anomalies.filter(a => a.severity === 'CRITICAL' && a.trust_state !== 'QUARANTINE').length > 0 ? (
                 <div className="mt-2 flex flex-col h-full justify-between">
                   <div>
                     <div className="text-lg font-bold text-white">{anomalies.find(a => a.severity === 'CRITICAL' && a.trust_state !== 'QUARANTINE')?.station_id}</div>
                     <div className="text-sm text-atmos-muted mt-1">{anomalies.find(a => a.severity === 'CRITICAL' && a.trust_state !== 'QUARANTINE')?.root_cause || anomalies.find(a => a.severity === 'CRITICAL' && a.trust_state !== 'QUARANTINE')?.attribution}</div>
                   </div>
                   
                   <div className="grid grid-cols-3 gap-2 mt-4">
                     <div className="bg-atmos-bg p-2 rounded border border-atmos-border">
                       <div className="text-[10px] text-atmos-muted uppercase">Observed</div>
                       <div className="text-sm font-bold text-atmos-critical">{anomalies.find(a => a.severity === 'CRITICAL' && a.trust_state !== 'QUARANTINE')?.observed_value}</div>
                     </div>
                     <div className="bg-atmos-bg p-2 rounded border border-atmos-border">
                       <div className="text-[10px] text-atmos-muted uppercase">Expected</div>
                       <div className="text-sm font-bold text-atmos-healthy">{anomalies.find(a => a.severity === 'CRITICAL' && a.trust_state !== 'QUARANTINE')?.expected_value?.toFixed(1) || '--'}</div>
                     </div>
                     <div className="bg-atmos-bg p-2 rounded border border-atmos-border">
                       <div className="text-[10px] text-atmos-muted uppercase">Evidence</div>
                       <div className="text-sm font-bold text-atmos-warning">{anomalies.find(a => a.severity === 'CRITICAL' && a.trust_state !== 'QUARANTINE')?.evidence_score}/100</div>
                     </div>
                   </div>
                 </div>
               ) : (
                 <div className="flex-1 flex flex-col items-center justify-center text-sm text-atmos-muted opacity-50">
                   <ShieldCheck className="w-8 h-8 mb-2" />
                   No active critical incidents.
                 </div>
               )}
            </div>

          </div>
        </div>

        {/* Right Column: Live Intelligence Stream */}
        <div className="col-span-3 bg-atmos-panel border border-atmos-border rounded p-4 flex flex-col shadow-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-atmos-accent opacity-5 blur-3xl rounded-full" />
          <h2 className="text-xs font-semibold text-atmos-muted tracking-widest mb-4 z-10">LIVE INTELLIGENCE EVENTS</h2>
          
          <div className="flex-1 overflow-y-auto pr-1 space-y-4 relative z-10">
            {/* Timeline line */}
            <div className="absolute left-2 top-2 bottom-0 w-px bg-atmos-border"></div>

            {anomalies.map((anom, i) => (
              <div key={i} className="relative pl-6 hover:bg-atmos-bg p-2 -ml-2 rounded transition-colors cursor-pointer border border-transparent hover:border-atmos-border/50">
                <div className={`absolute left-[13px] top-[14px] w-1.5 h-1.5 rounded-full ${anom.severity === 'CRITICAL' ? 'bg-atmos-critical shadow-[0_0_8px_#EF5B61]' : (anom.severity === 'HIGH' ? 'bg-atmos-warning' : 'bg-atmos-accent')}`} />
                <div className="text-[10px] font-mono text-atmos-muted mb-0.5">
                  {new Date(anom.timestamp).toLocaleTimeString()} • <span className="font-bold text-white">{anom.station_id}</span>
                </div>
                <div className={`text-xs font-semibold ${anom.severity === 'CRITICAL' ? 'text-atmos-critical' : 'text-atmos-text'}`}>
                  {anom.root_cause || anom.attribution || 'Deviation detected'}
                </div>
                <div className="flex justify-between items-center mt-1">
                  <div className="text-[9px] text-atmos-muted uppercase tracking-wider font-bold border border-atmos-border px-1.5 rounded bg-atmos-bg">
                    {anom.severity}
                  </div>
                  {anom.trust_state === 'QUARANTINE' && (
                    <div className="text-[9px] text-atmos-critical uppercase tracking-wider font-bold">QUARANTINED</div>
                  )}
                </div>
              </div>
            ))}
            
            {anomalies.length === 0 && (
              <div className="text-sm text-atmos-muted text-center mt-10">Waiting for intelligence events...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;
