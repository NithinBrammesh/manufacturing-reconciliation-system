import React from "react";
import styles from "./ComparisonCard.module.css";
import {
  HiOutlineArrowTrendingUp,
  HiOutlineExclamationTriangle,
  HiOutlineCheckCircle,
  HiOutlineExclamationCircle,
} from "react-icons/hi2";

const ComparisonCard = ({
  title,

  forwardLabel,
  reverseLabel,

  forwardMatched,
  forwardMatch,
  forwardLoss,
  forwardMissing,

  reverseMatched,
  reverseMatch,
  reverseLoss,
  reverseMissing,

  forwardMissingLabel,
  reverseMissingLabel,
}) => {

  const getStatus = (loss) => {
    const value = parseFloat(loss);

    if (value >= 50) {
      return {
        label: "Critical",
        color: styles.critical,
        icon: <HiOutlineExclamationTriangle />
      };
    }

    if (value >= 20) {
      return {
        label: "Warning",
        color: styles.warning,
        icon: <HiOutlineExclamationCircle />
      };
    }

    return {
      label: "Healthy",
      color: styles.healthy,
      icon: <HiOutlineCheckCircle />
    };
  };

  const status = getStatus(forwardLoss);

  return (
    <div className={styles.card}>

      {/* Header */}

      <div className={styles.header}>

        <div className={styles.title}>
          <HiOutlineArrowTrendingUp />
          <h3>{title}</h3>
        </div>

        <div className={`${styles.badge} ${status.color}`}>
          {status.icon}
          {status.label}
        </div>

      </div>

      {/* Forward */}

      <div className={styles.direction}>

        <h4>{forwardLabel}</h4>

        <div className={styles.row}>
          <span>Matched</span>
          <strong>{forwardMatched}</strong>
        </div>

        <div className={styles.row}>
          <span>Match %</span>
          <strong>{forwardMatch}%</strong>
        </div>

        <div className={styles.row}>
          <span>Loss %</span>
          <strong>{forwardLoss}%</strong>
        </div>

        <div className={styles.row}>
          <span>{forwardMissingLabel}</span>
          <strong>{forwardMissing}</strong>
        </div>

      </div>

      <hr className={styles.divider}/>

      {/* Reverse */}

      <div className={styles.direction}>

        <h4>{reverseLabel}</h4>

        <div className={styles.row}>
          <span>Matched</span>
          <strong>{reverseMatched}</strong>
        </div>

        <div className={styles.row}>
          <span>Match %</span>
          <strong>{reverseMatch}%</strong>
        </div>

        <div className={styles.row}>
          <span>Loss %</span>
          <strong>{reverseLoss}%</strong>
        </div>

        <div className={styles.row}>
          <span>{reverseMissingLabel}</span>
          <strong>{reverseMissing}</strong>
        </div>

      </div>

    </div>
  );
};

export default ComparisonCard;