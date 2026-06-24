import React from "react";
import styles from "./ProductionLines.module.css";
import {
  HiOutlineBuildingOffice2,
  HiOutlineCheckCircle,
} from "react-icons/hi2";

const ProductionLines = ({ lines, selectedLine, onLineSelect, metrics }) => {

  const getActiveMachines = (line) => {
    const m = metrics[line];
    if (!m) return { count: 0, label: "No data" };

    const active = [];
    if (parseInt(m.total_aoi) > 0) active.push("AOI");
    if (parseInt(m.total_spi) > 0) active.push("SPI");
    if (parseInt(m.total_fcr) > 0) active.push("FCR");

    return {
      count: active.length,
      label: active.length > 0 ? active.join(" · ") : "No data",
    };
  };

  return (
    <section className={styles.container}>
      <div className={styles.sectionHeader}>
        <h2>Production Lines</h2>
        <p>Select a production line to view reconciliation metrics</p>
      </div>

      <div className={styles.grid}>
        {lines.map((line) => {
          const { count, label } = getActiveMachines(line);

          return (
            <div
              key={line}
              className={`${styles.card} ${selectedLine === line ? styles.active : ""}`}
              onClick={() => onLineSelect(line)}
            >
              <div className={styles.top}>
                <div className={styles.iconBox}>
                  <HiOutlineBuildingOffice2 />
                </div>
                <div className={styles.status}>
                  <HiOutlineCheckCircle />
                  <span>Running</span>
                </div>
              </div>

              <div className={styles.body}>
                <h3>{line}</h3>
                <p>Production Line</p>
              </div>

              <div className={styles.footer}>
                <div>
                  <span>Active Machines</span>
                  <h4>{count}</h4>
                </div>
                <div>
                  <span>Machines in Use</span>
                  <h4 className={styles.machineLabel}>{label}</h4>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default ProductionLines;