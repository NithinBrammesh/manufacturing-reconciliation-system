import React, { useState } from "react";
import styles from "./ReworkPanel.module.css";
import {
  HiOutlineExclamationTriangle,
  HiOutlineCheckCircle,
  HiOutlineQrCode,
  HiOutlineXMark,
  HiOutlineWrenchScrewdriver,
} from "react-icons/hi2";

const BarcodeModal = ({ data, onClose }) => {
  if (!data) return null;
  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
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
        <span className={styles.countBadge}
          style={{ background: data.badgeBg, color: data.badgeColor }}>
          {data.list.length} barcodes
        </span>
        <div className={styles.barcodeGrid}>
          {data.list.length === 0
            ? <p className={styles.emptyMsg}>No barcodes to show</p>
            : data.list.map((bc, i) => (
              <div key={i} className={styles.barcodeChip}>
                <HiOutlineQrCode />
                <span>{bc}</span>
              </div>
            ))
          }
        </div>
      </div>
    </div>
  );
};

const ReworkPanel = ({ metrics }) => {

  const [modalData, setModalData] = useState(null);

  const spiGoodCount = parseInt(metrics.spi_good_count || 0);
  const spiBadCount  = parseInt(metrics.spi_bad_count  || 0);
  const spiTotal     = parseInt(metrics.spi_total_barcodes || 0);
  const spiGoodPct   = parseFloat(metrics.spi_good_pct || 0);
  const spiBadPct    = parseFloat(metrics.spi_bad_pct  || 0);

  const fcrExpected    = parseInt(metrics.fcr_expected      || 0);
  const fcrReceived    = parseInt(metrics.fcr_received_bad  || 0);
  const fcrMissing     = parseInt(metrics.fcr_missing_bad   || 0);
  const coveragePct    = parseFloat(metrics.fcr_rework_coverage_pct || 0);
  const lossPct        = parseFloat(metrics.fcr_rework_loss_pct     || 0);

  let goodBarcodes = [];
  let badBarcodes  = [];
  let missingBarcodes = [];

  try { goodBarcodes    = JSON.parse(metrics.spi_good_barcodes      || "[]"); } catch(e) {}
  try { badBarcodes     = JSON.parse(metrics.spi_bad_barcodes       || "[]"); } catch(e) {}
  try { missingBarcodes = JSON.parse(metrics.fcr_missing_bad_barcodes || "[]"); } catch(e) {}

  // Don't render if no SPI result data yet
  if (spiTotal === 0) return null;

  const coverageColor = coveragePct >= 80
    ? "#22c55e" : coveragePct >= 50
    ? "#f59e0b" : "#ef4444";

  return (
    <>
      <div className={styles.panel}>

        {/* ── SPI Good / Bad split ── */}
        <div className={styles.splitSection}>
          <div className={styles.splitHeader}>
            <HiOutlineWrenchScrewdriver />
            <h4>SPI Inspection Result</h4>
            <span className={styles.totalBadge}>{spiTotal} total barcodes</span>
          </div>

          {/* Split bar */}
          <div className={styles.splitBar}>
            <div
              className={styles.goodBar}
              style={{ width: `${spiGoodPct}%` }}
              title={`Good: ${spiGoodCount}`}
            />
            <div
              className={styles.badBar}
              style={{ width: `${spiBadPct}%` }}
              title={`Bad: ${spiBadCount}`}
            />
          </div>

          {/* Labels + view buttons */}
          <div className={styles.splitLabels}>
            <div className={styles.splitLabelLeft}>
              <span className={styles.goodDot} />
              <span>Good: <strong>{spiGoodCount}</strong> ({spiGoodPct}%)</span>
              <button
                className={styles.viewBtnGood}
                onClick={() => setModalData({
                  title: "SPI Good Barcodes",
                  subtitle: "Barcodes that passed SPI inspection",
                  list: goodBarcodes,
                  badgeBg: "#dcfce7",
                  badgeColor: "#166534"
                })}
              >
                View all
              </button>
            </div>

            <div className={styles.splitLabelRight}>
              <span className={styles.badDot} />
              <span>Bad: <strong>{spiBadCount}</strong> ({spiBadPct}%)</span>
              <button
                className={styles.viewBtnBad}
                onClick={() => setModalData({
                  title: "SPI Bad Barcodes",
                  subtitle: "Barcodes that FAILED SPI — sent to FCR for rework",
                  list: badBarcodes,
                  badgeBg: "#fee2e2",
                  badgeColor: "#dc2626"
                })}
              >
                View all
              </button>
            </div>
          </div>
        </div>

        {/* ── FCR Rework reconciliation ── */}
        {fcrExpected > 0 && (
          <div className={styles.reworkSection}>

            <div className={styles.reworkHeader}>
              <HiOutlineExclamationTriangle style={{ color: lossPct >= 50 ? "#dc2626" : "#f59e0b" }} />
              <h4>FCR Rework Coverage</h4>
              <span className={styles.reworkSubtitle}>
                {fcrExpected} bad barcodes expected at FCR
              </span>
            </div>

            <div className={styles.reworkStats}>
              <div className={styles.stat}>
                <span>Expected at FCR</span>
                <strong>{fcrExpected}</strong>
              </div>
              <div className={styles.stat}>
                <span>FCR received</span>
                <strong style={{ color: "#16a34a" }}>{fcrReceived}</strong>
              </div>
              <div className={styles.stat}>
                <span>Missing at FCR</span>
                <strong style={{ color: "#dc2626" }}>{fcrMissing}</strong>
              </div>
              <div className={styles.stat}>
                <span>Coverage</span>
                <strong style={{ color: coverageColor }}>{coveragePct}%</strong>
              </div>
              <div className={styles.stat}>
                <span>Rework loss</span>
                <strong style={{ color: "#dc2626" }}>{lossPct}%</strong>
              </div>
            </div>

            {/* Coverage bar */}
            <div className={styles.barTrack}>
              <div
                className={styles.barFill}
                style={{ width: `${Math.min(coveragePct, 100)}%`, background: coverageColor }}
              />
            </div>

            {/* View missing button */}
            {fcrMissing > 0 && (
              <button
                className={styles.viewMissingBtn}
                onClick={() => setModalData({
                  title: "Bad Barcodes Missing at FCR",
                  subtitle: `${fcrMissing} barcodes marked Bad by SPI but never received by FCR`,
                  list: missingBarcodes,
                  badgeBg: "#fee2e2",
                  badgeColor: "#dc2626"
                })}
              >
                <HiOutlineExclamationTriangle />
                View {fcrMissing} missing rework barcodes
              </button>
            )}

            {fcrMissing === 0 && (
              <div className={styles.allReceived}>
                <HiOutlineCheckCircle />
                <span>All bad barcodes were received by FCR</span>
              </div>
            )}

          </div>
        )}

      </div>

      <BarcodeModal data={modalData} onClose={() => setModalData(null)} />
    </>
  );
};

export default ReworkPanel;