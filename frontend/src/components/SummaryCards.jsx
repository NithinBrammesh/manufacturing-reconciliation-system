import React from "react";
import styles from "./SummaryCards.module.css";
import {
  HiOutlineCircleStack,
  HiOutlineClipboardDocumentCheck,
  HiOutlineCpuChip,
  HiOutlineChartBar,
  HiOutlineCheckBadge,
  HiOutlineAdjustmentsHorizontal,
} from "react-icons/hi2";

const ICON_MAP = {
  AOI: <HiOutlineCircleStack />,
  SPI: <HiOutlineClipboardDocumentCheck />,
  FCR: <HiOutlineCpuChip />,
};

const SummaryCards = ({ metrics }) => {

  if (!metrics) return null;

  // Machine totals — dynamic
  const totalKeys = Object.keys(metrics).filter(
    k => k.startsWith("total_")
      && !k.includes("unique")
      && parseInt(metrics[k]) > 0
  );

  // Partial matches — best pairwise match count across all pairs
  const comparisons = metrics.comparisons
    ? JSON.parse(metrics.comparisons)
    : [];

  // Build partial matching summary per pair
  const pairMatches = comparisons.map(pair => {
    const [S, T] = pair.split("_");
    const s = S.toLowerCase();
    const t = T.toLowerCase();
    return {
      label: `${S} ↔ ${T}`,
      matched: parseInt(metrics[`${s}_${t}_matched`] || 0),
    };
  });

  const overallMatched   = parseInt(metrics.all_matched || 0);
  const overallPct       = parseFloat(metrics.overall_percentage || 0);
  const totalUnique      = parseInt(metrics.total_unique_barcodes || 0);

  return (
    <div className={styles.wrapper}>

      {/* ── Machine totals ── */}
      <div className={styles.grid}>
        {totalKeys.map(key => {
          const type = key.replace("total_", "").toUpperCase();
          return (
            <div key={key} className={styles.card}>
              <div className={styles.icon}>
                {ICON_MAP[type] || <HiOutlineChartBar />}
              </div>
              <h4>Total {type}</h4>
              <h2>{metrics[key]}</h2>
            </div>
          );
        })}

        {totalUnique > 0 && (
          <div className={styles.card}>
            <div className={styles.icon}><HiOutlineAdjustmentsHorizontal /></div>
            <h4>Total Unique</h4>
            <h2>{totalUnique}</h2>
          </div>
        )}
      </div>

      {/* ── Matching summary ── */}
      <div className={styles.matchSection}>

        {/* Pairwise partial matches */}
        <div className={styles.matchGrid}>
          {pairMatches.map(({ label, matched }) => (
            <div key={label} className={styles.matchCard}>
              <h4>{label}</h4>
              <p>Partial Match</p>
              <h2>{matched}</h2>
              {totalUnique > 0 && (
                <span className={styles.matchPct}>
                  {round(matched / totalUnique * 100, 1)}% of total
                </span>
              )}
            </div>
          ))}
        </div>

        {/* Overall — seen by ALL machines */}
        <div className={styles.overallCard}>
          <div className={styles.icon}>
            <HiOutlineCheckBadge />
          </div>
          <div>
            <h4>Overall Match</h4>
            <p>Seen by ALL machines</p>
            <h2>{overallMatched} <span>({overallPct}%)</span></h2>
          </div>
        </div>

      </div>
    </div>
  );
};

// helper
const round = (v, d) => Math.round(v * Math.pow(10,d)) / Math.pow(10,d);

export default SummaryCards;