import React, { useEffect, useState } from "react";
import Header from "../components/Header";
import ProductionLines from "../components/ProductionLines";
import DashboardContent from "../components/DashboardContent";
import { getAllMetrics } from "../services/api";

const Dashboard = () => {
  const [lines, setLines] = useState([]);
  const [selectedLine, setSelectedLine] = useState(null);
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const data = await getAllMetrics();
      setMetrics(data);
      const availableLines = Object.keys(data).sort();
      setLines(availableLines);
      // Only auto-select on first load
      setSelectedLine(prev => prev ?? availableLines[0] ?? null);
      setLoading(false);
    } catch (error) {
      console.error("Failed to load metrics:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
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
            />
          <DashboardContent metrics={metrics[selectedLine]} />
        </>
      )}
    </div>
  );
};

export default Dashboard;