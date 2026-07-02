import React, { useState } from "react";
import styles from "./MachineHealth.module.css";
import {
  HiOutlineCircleStack,
  HiOutlineClipboardDocumentCheck,
  HiOutlineCpuChip,
  HiOutlineChartBar,
  HiOutlineXMark,
  HiOutlineQrCode,
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
  return         { bar: "#ef4444", label: "Critical", text: "#991b1b", bg: "#fef2f2" };
};

// ── Modal Component ──────────────────────────────────────────────
const BarcodeModal = ({ data, onClose }) => {
  if (!data) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className={styles.modalHeader}>
          <div className={styles.modalTitle}>
            <HiOutlineQrCode />
            <div>
              <h3>{data.title}</h3>
              <p>{data.subtitle}</p>
            </div>
          </div>
          <button className={styles.closeBtn} onClick={onClose}>
            <HiOutlineXMark />
          </button>
        </div>

        {/* Count badge */}
        <div className={styles.modalCount}>
          <span className={styles.countBadge} style={{ background: data.badgeBg, color: data.badgeColor }}>
            {data.list.length} barcodes
          </span>
        </div>

        {/* Barcode list */}
        <div className={styles.barcodeGrid}>
          {data.list.map((barcode, i) => (
            <div key={i} className={styles.barcodeChip}>
              <HiOutlineQrCode />
              <span>{barcode}</span>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
};

// ── Main Component ───────────────────────────────────────────────
const MachineHealth = ({ metrics }) => {

  const [modalData, setModalData] = useState(null);

  if (!metrics) return null;

  const totalUnique = parseInt(metrics.total_unique_barcodes || 0);

  let globalUniqueMap = {};
  try {
    globalUniqueMap = metrics.global_unique_barcodes
      ? JSON.parse(metrics.global_unique_barcodes)
      : {};
  } catch (e) {
    globalUniqueMap = {};
  }

  const totalKeys = Object.keys(metrics).filter(
    k => k.startsWith("total_")
      && !k.includes("unique")
      && parseInt(metrics[k]) > 0
  );

  if (totalKeys.length === 0) return null;

  const machineStats = totalKeys.map(key => {
    const type = key.replace("total_", "").toUpperCase();
    const k = type.toLowerCase();

    // Parse missing barcode list from backend
    let missingList = [];

    try {
      missingList = metrics[`${k}_missing_barcodes`]
        ? JSON.parse(metrics[`${k}_missing_barcodes`])
        : [];
    } catch (e) {
      missingList = [];
    }

    return {
      type,
      seen: parseInt(metrics[`${k}_global_seen`] || metrics[key] || 0),
      missing: parseInt(metrics[`${k}_global_missing`] || 0),
      globalMatchPct: parseFloat(metrics[`${k}_global_match_pct`] || 0),
      globalLossPct: parseFloat(metrics[`${k}_global_loss_pct`] || 0),
      exclusive: parseInt(metrics[`${k}_exclusive_barcodes`] || 0),
      exclusiveList: globalUniqueMap[type] || [],
      missingList,
    };
  });

  const openModal = (title, subtitle, list, badgeBg, badgeColor) => {
    setModalData({ title, subtitle, list, badgeBg, badgeColor });
  };

  return (
    <>
      <div className={styles.panel}>
        <div className={styles.titleRow}>
          {/* <h3 className={styles.title}>Machine Health</h3> */}
          {totalUnique > 0 && (
            <span className={styles.uniqueTotal}>
              {totalUnique} unique barcodes in production
            </span>
          )}
        </div>

        <div className={styles.grid}>
          {machineStats.map(({
            type, seen, missing,
            globalMatchPct, globalLossPct,
            exclusive, exclusiveList,
            missingList,
          }) => {
            const health = getHealthColor(globalMatchPct);

            return (
              <div key={type} className={styles.card} style={{ background: health.bg }}>

                <div className={styles.top}>
                  <div className={styles.icon}>
                    {ICON_MAP[type] || <HiOutlineChartBar />}
                  </div>
                  <span className={styles.badge}
                    style={{ color: health.text, background: "white" }}>
                    {health.label}
                  </span>
                </div>

                <h4 className={styles.machineType}>{type}</h4>

                <div className={styles.statRow}>
                  <span>Barcodes seen</span>
                  <strong style={{ color: health.text }}>{seen}</strong>
                </div>

                <div className={styles.statRow}>
                  <span>Missing globally</span>
                  <strong style={{ color: "#dc2626" }}>{missing}</strong>
                </div>

                {/* Exclusive barcodes — clickable */}
                {exclusive > 0 && (
                  <div className={styles.exclusiveBox}>
                    <div className={styles.exclusiveTop}>
                      <div>
                        <span className={styles.exclusiveLabel}>
                          Unique to {type} only
                        </span>
                        <span className={styles.exclusiveCount}>{exclusive}</span>
                      </div>
                      <button
                        className={styles.viewBtn}
                        onClick={() => openModal(
                          `Unique to ${type} only`,
                          `These barcodes were seen ONLY by ${type} and no other machine`,
                          exclusiveList,
                          "#ede9fe",
                          "#7c3aed"
                        )}
                      >
                        View all
                      </button>
                    </div>
                    <div className={styles.exclusivePreview}>
                      {exclusiveList.slice(0, 2).join(", ")}
                      {exclusiveList.length > 2 && ` +${exclusiveList.length - 2} more`}
                    </div>
                  </div>
                )}

                {/* Missing globally — clickable if you store the list */}
                 {/* {missing > 0 && (
                  <button
                    className={styles.missingBtn}
                    style={{ borderColor: health.bar, color: health.text }}
                    onClick={() =>
                      openModal(
                        `${type} — Missing Globally`,
                        `${missing} barcodes from the global pool were NOT seen by ${type}`,
                        missingList,
                        "#fef2f2",
                        "#dc2626"
                      )
                    }
                  >
                    View {missing} missing barcodes ↗
                  </button>
                )}  */}

                <div className={styles.barTrack}>
                  <div
                    className={styles.barFill}
                    style={{
                      width: `${Math.min(globalMatchPct, 100)}%`,
                      background: health.bar
                    }}
                  />
                </div>

                <div className={styles.pctRow}>
                  <span style={{ color: health.text }}>
                    Coverage: {globalMatchPct.toFixed(1)}%
                  </span>
                  <span style={{ color: "#dc2626" }}>
                    Loss: {globalLossPct.toFixed(1)}%
                  </span>
                </div>

                {totalUnique > 0 && (
                  <p className={styles.outOf} style={{ color: health.text }}>
                    {seen} of {totalUnique} total barcodes
                  </p>
                )}

              </div>
            );
          })}
        </div>
      </div>

      {/* Modal */}
      <BarcodeModal data={modalData} onClose={() => setModalData(null)} />
    </>
  );
};

export default MachineHealth;