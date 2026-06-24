import React from "react";
import styles from "./DashboardContent.module.css";
import {
  HiOutlineCircleStack,
  HiOutlineClipboardDocumentCheck,
  HiOutlineCpuChip,
  HiOutlineChartBar,
  HiOutlineArrowTrendingUp,
} from "react-icons/hi2";

const DashboardContent = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className={styles.noData}>
        Select a Production Line
      </div>
    );
  }

  const hasAOI = parseInt(metrics.total_aoi) > 0;
  const hasSPI = parseInt(metrics.total_spi) > 0;
  const hasFCR = parseInt(metrics.total_fcr) > 0;

  const activeMachineCount = [hasAOI, hasSPI, hasFCR].filter(Boolean).length;

  return (
    <div className={styles.container}>

      {/* ========================= */}
      {/* Production Summary */}
      {/* ========================= */}

      <div className={styles.sectionTitle}>
        <h2>Production Summary</h2>
      </div>

      <div className={styles.summaryGrid}>
        {hasAOI && (
          <div className={styles.summaryCard}>
            <HiOutlineCircleStack />
            <h4>Total AOI</h4>
            <h2>{metrics.total_aoi}</h2>
          </div>
        )}

        {hasSPI && (
          <div className={styles.summaryCard}>
            <HiOutlineClipboardDocumentCheck />
            <h4>Total SPI</h4>
            <h2>{metrics.total_spi}</h2>
          </div>
        )}

        {hasFCR && (
          <div className={styles.summaryCard}>
            <HiOutlineCpuChip />
            <h4>Total FCR</h4>
            <h2>{metrics.total_fcr}</h2>
          </div>
        )}

        <div className={styles.summaryCard}>
          <HiOutlineChartBar />
          <h4>Overall Match</h4>
          <h2>{metrics.overall_percentage}%</h2>
        </div>
      </div>

      {/* ========================= */}
      {/* Active Machines Info */}
      {/* ========================= */}

      <div className={styles.sectionTitle}>
        <h2>Machine Comparison</h2>
        <p>{activeMachineCount} machine{activeMachineCount !== 1 ? "s" : ""} active on this line</p>
      </div>

      <div className={styles.comparisonGrid}>

        {/* AOI ↔ SPI — only if both have data */}
        {hasAOI && hasSPI && (
          <div className={styles.compareCard}>
            <div className={styles.compareHeader}>
              <HiOutlineArrowTrendingUp />
              <h3>AOI ↔ SPI</h3>
            </div>
            <div className={styles.compareBody}>
              <p>Matched <span>{metrics.aoi_spi_matched}</span></p>
              <p>Match % <span>{metrics.aoi_spi_match_percentage}%</span></p>
              <p>Loss % <span>{metrics.aoi_spi_loss_percentage}%</span></p>
              <p>AOI missing in SPI <span>{metrics.aoi_missing_in_spi}</span></p>
              <p>SPI missing in AOI <span>{metrics.spi_missing_in_aoi}</span></p>
            </div>
          </div>
        )}

        {/* AOI ↔ FCR — only if both have data */}
        {hasAOI && hasFCR && (
          <div className={styles.compareCard}>
            <div className={styles.compareHeader}>
              <HiOutlineArrowTrendingUp />
              <h3>AOI ↔ FCR</h3>
            </div>
            <div className={styles.compareBody}>
              <p>Matched <span>{metrics.aoi_fcr_matched}</span></p>
              <p>Match % <span>{metrics.aoi_fcr_match_percentage}%</span></p>
              <p>Loss % <span>{metrics.aoi_fcr_loss_percentage}%</span></p>
              <p>AOI missing in FCR <span>{metrics.aoi_missing_in_fcr}</span></p>
              <p>FCR missing in AOI <span>{metrics.fcr_missing_in_aoi}</span></p>
            </div>
          </div>
        )}

        {/* SPI ↔ FCR — only if both have data */}
        {hasSPI && hasFCR && (
          <div className={styles.compareCard}>
            <div className={styles.compareHeader}>
              <HiOutlineArrowTrendingUp />
              <h3>SPI ↔ FCR</h3>
            </div>
            <div className={styles.compareBody}>
              <p>Matched <span>{metrics.spi_fcr_matched}</span></p>
              <p>Match % <span>{metrics.spi_fcr_match_percentage}%</span></p>
              <p>Loss % <span>{metrics.spi_fcr_loss_percentage}%</span></p>
              <p>SPI missing in FCR <span>{metrics.spi_missing_in_fcr}</span></p>
              <p>FCR missing in SPI <span>{metrics.fcr_missing_in_spi}</span></p>
            </div>
          </div>
        )}

      </div>

      {/* ========================= */}
      {/* Three-Way — only if all three have data */}
      {/* ========================= */}

      {hasAOI && hasSPI && hasFCR && (
        <>
          {/* <div className={styles.sectionTitle}>
            <h2>Three-Way Reconciliation</h2>
          </div>
          <div className={styles.summaryGrid}>
            <div className={styles.summaryCard}>
              <HiOutlineChartBar />
              <h4>All Three Matched</h4>
              <h2>{metrics.all_matched}</h2>
            </div>
            <div className={styles.summaryCard}>
              <HiOutlineChartBar />
              <h4>Overall Total</h4>
              <h2>{metrics.overall_total}</h2>
            </div>
            <div className={styles.summaryCard}>
              <HiOutlineChartBar />
              <h4>Overall Match %</h4>
              <h2>{metrics.overall_percentage}%</h2>
            </div>
          </div> */}
        </>
      )}

    </div>
  );
};

export default DashboardContent;