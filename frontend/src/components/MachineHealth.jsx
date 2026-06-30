import React from "react";
import styles from "./MachineHealth.module.css";
import {
  HiOutlineCircleStack,
  HiOutlineClipboardDocumentCheck,
  HiOutlineCpuChip,
  HiOutlineChartBar,
} from "react-icons/hi2";

const ICON_MAP = {
  AOI: <HiOutlineCircleStack />,
  SPI: <HiOutlineClipboardDocumentCheck />,
  FCR: <HiOutlineCpuChip />,
};

const getHealthColor = (matchPct) => {
  const v = parseFloat(matchPct);
  if (v >= 80) return { bar: "#22c55e", label: "Healthy",  text: "#166534", bg: "#f0fdf4" };
  if (v >= 50) return { bar: "#f59e0b", label: "Warning",  text: "#92400e", bg: "#fffbeb" };
  return       { bar: "#ef4444", label: "Critical", text: "#991b1b", bg: "#fef2f2" };
};

const MachineHealth = ({ metrics }) => {

  if (!metrics) return null;

  const totalKeys = Object.keys(metrics).filter(
    k => k.startsWith("total_") && parseInt(metrics[k]) > 0
  );

  if (totalKeys.length === 0) return null;

  // For each machine type, find its best match % across all comparisons
  const machineStats = totalKeys.map(key => {
    const type = key.replace("total_", "").toUpperCase();
    const total = parseInt(metrics[key]);

    // Find all comparison percentages involving this type
    const matchKeys = Object.keys(metrics).filter(
      k => k.startsWith(`${type.toLowerCase()}_`) && k.endsWith("_match_percentage")
    );

    const bestMatch = matchKeys.length > 0
      ? Math.max(...matchKeys.map(k => parseFloat(metrics[k] || 0)))
      : 0;

    return { type, total, bestMatch };
  });

  return (
    <div className={styles.panel}>
      <h3 className={styles.title}>Machine Health</h3>
      <div className={styles.grid}>
        {machineStats.map(({ type, total, bestMatch }) => {
          const health = getHealthColor(bestMatch);
          return (
            <div key={type} className={styles.card} style={{ background: health.bg }}>
              <div className={styles.top}>
                <div className={styles.icon}>
                  {ICON_MAP[type] || <HiOutlineChartBar />}
                </div>
                <span className={styles.badge} style={{ color: health.text, background: "white" }}>
                  {health.label}
                </span>
              </div>
              <h4 className={styles.machineType}>{type}</h4>
              <p className={styles.total}>{total} barcodes</p>
              <div className={styles.barTrack}>
                <div
                  className={styles.barFill}
                  style={{ width: `${Math.min(bestMatch, 100)}%`, background: health.bar }}
                />
              </div>
              <p className={styles.matchPct} style={{ color: health.text }}>
                Best match: {bestMatch.toFixed(1)}%
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MachineHealth;