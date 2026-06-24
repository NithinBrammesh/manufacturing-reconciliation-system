// src/components/Header.jsx

import React, { useEffect, useState } from "react";
import styles from "./Header.module.css";

import {
  HiOutlineCpuChip,
  HiOutlineSignal,
  HiOutlineClock,
} from "react-icons/hi2";

const Header = () => {
  const [currentTime, setCurrentTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();

      setCurrentTime(
        now.toLocaleString("en-IN", {
          weekday: "short",
          day: "2-digit",
          month: "short",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    };

    updateTime();

    const timer = setInterval(updateTime, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <header className={styles.header}>
      {/* Left */}

      <div className={styles.leftSection}>
        <div className={styles.logoContainer}>
          <HiOutlineCpuChip />
        </div>

        <div>
          <h1>Manufacturing Reconciliation Dashboard</h1>

          <p>
            Real-Time Production Monitoring & Reconciliation System
          </p>
        </div>
      </div>

      {/* Right */}

      <div className={styles.rightSection}>
        <div className={styles.statusCard}>
          <HiOutlineSignal />

          <div>
            <span>Status</span>

            <h4>LIVE</h4>
          </div>
        </div>

        <div className={styles.statusCard}>
          <HiOutlineClock />

          <div>
            <span>Last Updated</span>

            <h4>{currentTime}</h4>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;