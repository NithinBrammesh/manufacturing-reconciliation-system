import React, { useEffect, useState, useRef } from "react";
import Header from "../components/Header";
import ProductionLines from "../components/ProductionLines";
import DashboardContent from "../components/DashboardContent";

const API = "";

const Dashboard = () => {
  const [lines, setLines]             = useState([]);
  const [selectedLine, setSelectedLine] = useState(null);
  const [metrics, setMetrics]         = useState({});
  const [status, setStatus]           = useState({});
  const [loading, setLoading]         = useState(true);
  const eventSourceRef                = useRef(null);

  useEffect(() => {

    // Load initial snapshot via REST once
    fetch(`${API}/api/reconciliation`)
      .then(r => r.json())
      .then(data => {
        setMetrics(data);
        const availableLines = Object.keys(data).sort();
        setLines(availableLines);
        setSelectedLine(prev => prev ?? availableLines[0] ?? null);
        setLoading(false);
      })
      .catch(err => {
        console.error("Initial load failed:", err);
        setLoading(false);
      });

    // Open SSE connection — stays open, no polling
    const es = new EventSource(`${API}/events`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Update metrics
      if (data.metrics) {
        setMetrics(data.metrics);
        const availableLines = Object.keys(data.metrics).sort();
        setLines(availableLines);
        setSelectedLine(prev => prev ?? availableLines[0] ?? null);
      }

      // Update line status (ACTIVE / IDLE)
      if (data.status) {
        setStatus(data.status);
      }
    };

    es.onerror = (err) => {
      console.error("SSE connection error:", err);
      // Browser will auto-reconnect
    };

    return () => {
      es.close();
    };

  }, []);

  return (
    <div className="dashboard">
      <Header />

      {loading ? (
        <h2 style={{ textAlign: "center", marginTop: "50px", color: "#64748b" }}>
          Loading Dashboard...
        </h2>
      ) : (
        <>
          <ProductionLines
            lines={lines}
            selectedLine={selectedLine}
            onLineSelect={setSelectedLine}
            metrics={metrics}
            status={status}
          />
          <DashboardContent metrics={metrics[selectedLine]} />
        </>
      )}
    </div>
  );
};

export default Dashboard;