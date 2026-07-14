import React from "react";
import styles from "./DashboardContent.module.css";
import ComparisonCard from "./ComparisonCard";
import SummaryCards from "./SummaryCards";
import MachineHealth from "./MachineHealth";
import AlertPanel from "./AlertPanel";
import ReworkPanel from "./ReworkPanel"; 

const DashboardContent = ({ metrics }) => {

  if (!metrics) {
    return (
      <div className={styles.noData}>
        Select a Production Line
      </div>
    );
  }

  const comparisons = metrics.comparisons
    ? JSON.parse(metrics.comparisons)
    : [];

  const totalKeys = Object.keys(metrics).filter(
    k => k.startsWith("total_") && parseInt(metrics[k]) > 0
  );
  const activeMachineCount = totalKeys.length;

  return (
    <div className={styles.container}>

      {/* ── Alerts ── */}
      <AlertPanel metrics={metrics} />

      {/* ── Summary ── */}
      <div className={styles.sectionTitle}>
        <h2>Production Summary</h2>
      </div>
      <SummaryCards metrics={metrics} />

      {/* ── Machine Health ── */}
      <div className={styles.sectionTitle} style={{ marginTop: 40 }}>
        <h2>Machine Health</h2>
      </div>
      <MachineHealth metrics={metrics} />


      <div className={styles.sectionTitle} style={{ marginTop: 40 }}>
       <h2>SPI Result & FCR Rework</h2>
      </div>
      <ReworkPanel metrics={metrics} />

      {/* ── Comparison Cards ── */}
      <div className={styles.sectionTitle}>
        <h2>Machine Comparison</h2>
        <p>{activeMachineCount} machine{activeMachineCount !== 1 ? "s" : ""} active on this line</p>
      </div>

      <div className={styles.comparisonGrid}>
        {comparisons.map(pair => {
          const [SOURCE, TARGET] = pair.split("_");
          const s = SOURCE.toLowerCase();
          const t = TARGET.toLowerCase();

          return (
            <ComparisonCard
              key={pair}
              title={`${SOURCE} ↔ ${TARGET}`}

              forwardLabel={`${SOURCE} → ${TARGET}`}
              forwardMatched={metrics[`${s}_${t}_matched`]}
              forwardMatch={metrics[`${s}_${t}_match_percentage`]}
              forwardLoss={metrics[`${s}_${t}_loss_percentage`]}
              forwardMissing={metrics[`${s}_missing_in_${t}`]}
              forwardMissingLabel={`${SOURCE} missing in ${TARGET}`}

              reverseLabel={`${TARGET} → ${SOURCE}`}
              reverseMatched={metrics[`${s}_${t}_matched`]}
              reverseMatch={metrics[`${t}_${s}_match_percentage`]}
              reverseLoss={metrics[`${t}_${s}_loss_percentage`]}
              reverseMissing={metrics[`${t}_missing_in_${s}`]}
              reverseMissingLabel={`${TARGET} missing in ${SOURCE}`}
            />
          );
        })}
      </div>

    </div>
  );
};

export default DashboardContent;