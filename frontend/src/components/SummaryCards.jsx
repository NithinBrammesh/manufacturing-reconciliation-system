import React from "react";
import styles from "./SummaryCards.module.css";
import {
  HiOutlineCircleStack,
  HiOutlineClipboardDocumentCheck,
  HiOutlineCpuChip,
  HiOutlineChartBar,
  HiOutlineCheckBadge,
} from "react-icons/hi2";

const ICON_MAP = {
  AOI: <HiOutlineCircleStack />,
  SPI: <HiOutlineClipboardDocumentCheck />,
  FCR: <HiOutlineCpuChip />,
};

const SummaryCards = ({ metrics }) => {

  if (!metrics) return null;

  const totalKeys = Object.keys(metrics).filter(
    k => k.startsWith("total_") && parseInt(metrics[k]) > 0
  );

  return (
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

      <div className={styles.card}>
        <div className={styles.icon}>
          <HiOutlineCheckBadge />
        </div>
        <h4>All Matched</h4>
        <h2>{metrics.all_matched}</h2>
      </div>

      <div className={`${styles.card} ${styles.highlight}`}>
        <div className={styles.icon}>
          <HiOutlineChartBar />
        </div>
        <h4>Overall Match</h4>
        <h2>{metrics.overall_percentage}%</h2>
      </div>

    </div>
  );
};

export default SummaryCards;