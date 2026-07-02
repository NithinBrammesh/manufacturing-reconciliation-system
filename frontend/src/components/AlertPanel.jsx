import React from "react";
import styles from "./AlertPanel.module.css";
import {
  HiOutlineExclamationTriangle,
  HiOutlineExclamationCircle,
  HiOutlineInformationCircle,
} from "react-icons/hi2";

const AlertPanel = ({ metrics }) => {

  if (!metrics) return null;

  const comparisons = metrics.comparisons
    ? JSON.parse(metrics.comparisons)
    : [];

  const alerts = [];

  // ── Pairwise alerts ──
  comparisons.forEach(pair => {
    const [SOURCE, TARGET] = pair.split("_");
    const s = SOURCE.toLowerCase();
    const t = TARGET.toLowerCase();

    const fLoss    = parseFloat(metrics[`${s}_${t}_loss_percentage`] || 0);
    const rLoss    = parseFloat(metrics[`${t}_${s}_loss_percentage`] || 0);
    const fMissing = parseInt(metrics[`${s}_missing_in_${t}`] || 0);
    const rMissing = parseInt(metrics[`${t}_missing_in_${s}`] || 0);

    if (fLoss >= 50) alerts.push({
      level: "critical", icon: <HiOutlineExclamationTriangle />,
      message: `${SOURCE} → ${TARGET}: ${fLoss}% pairwise loss — ${fMissing} barcodes missing in ${TARGET}`
    });
    else if (fLoss >= 20) alerts.push({
      level: "warning", icon: <HiOutlineExclamationCircle />,
      message: `${SOURCE} → ${TARGET}: ${fLoss}% pairwise loss — ${fMissing} barcodes missing in ${TARGET}`
    });

    if (rLoss >= 50) alerts.push({
      level: "critical", icon: <HiOutlineExclamationTriangle />,
      message: `${TARGET} → ${SOURCE}: ${rLoss}% pairwise loss — ${rMissing} barcodes missing in ${SOURCE}`
    });
    else if (rLoss >= 20) alerts.push({
      level: "warning", icon: <HiOutlineExclamationCircle />,
      message: `${TARGET} → ${SOURCE}: ${rLoss}% pairwise loss — ${rMissing} barcodes missing in ${SOURCE}`
    });
  });

  // ── Global loss alerts (new) ──
  const totalUnique = parseInt(metrics.total_unique_barcodes || 0);

  if (totalUnique > 0) {
    Object.keys(metrics)
      .filter(k => k.endsWith("_global_loss_pct"))
      .forEach(k => {
        const type      = k.replace("_global_loss_pct", "").toUpperCase();
        const lossPct   = parseFloat(metrics[k] || 0);
        const missing   = parseInt(metrics[`${type.toLowerCase()}_global_missing`] || 0);

        if (lossPct >= 50) alerts.push({
          level: "critical", icon: <HiOutlineExclamationTriangle />,
          message: `${type} globally: ${lossPct}% loss — ${missing} of ${totalUnique} total barcodes not seen by ${type}`
        });
        else if (lossPct >= 20) alerts.push({
          level: "warning", icon: <HiOutlineExclamationCircle />,
          message: `${type} globally: ${lossPct}% loss — ${missing} of ${totalUnique} total barcodes not seen by ${type}`
        });
      });
  }

  if (alerts.length === 0) {
    return (
      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <HiOutlineInformationCircle />
          <h3>Alerts</h3>
        </div>
        <div className={styles.healthy}>
          <HiOutlineInformationCircle />
          <span>All machine comparisons are within acceptable limits</span>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <HiOutlineExclamationTriangle />
        <h3>Alerts <span className={styles.count}>{alerts.length}</span></h3>
      </div>
      <div className={styles.list}>
        {alerts.map((alert, i) => (
          <div key={i} className={`${styles.alert} ${styles[alert.level]}`}>
            {alert.icon}
            <span>{alert.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertPanel;