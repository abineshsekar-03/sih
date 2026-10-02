import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import LiveMonitor from './pages/LiveMonitor';
import Anomalies from './pages/Anomalies';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/monitor" element={<LiveMonitor />} />
          <Route path="/anomalies" element={<Anomalies />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
