// =====================================================
// Manufacturing Reconciliation Dashboard
// app.js
// =====================================================

const API_URL = "http://localhost:5000/api/reconciliation";

// =====================================================
// Update HTML Element
// =====================================================

function updateValue(id, value) {

    const element = document.getElementById(id);

    if (element) {
        element.innerText = value;
    }

}

// =====================================================
// Load Metrics
// =====================================================

async function loadMetrics() {

    try {

        const response = await fetch(API_URL);

        if (!response.ok) {

            throw new Error("Unable to connect to Flask API");

        }

        const data = await response.json();

        // ============================================
        // Production Summary
        // ============================================

        updateValue("total_aoi", data.total_aoi);
        updateValue("total_spi", data.total_spi);
        updateValue("total_fcr", data.total_fcr);

        updateValue(
            "overall_percentage",
            data.overall_percentage + "%"
        );

        updateValue(
            "overall_percentage_bottom",
            data.overall_percentage + "%"
        );

        // ============================================
        // AOI ↔ SPI
        // ============================================

        updateValue(
            "aoi_spi_matched",
            data.aoi_spi_matched
        );

        updateValue(
            "aoi_missing_in_spi",
            data.aoi_missing_in_spi
        );

        updateValue(
            "spi_missing_in_aoi",
            data.spi_missing_in_aoi
        );

        updateValue(
            "aoi_spi_match_percentage",
            data.aoi_spi_match_percentage + "%"
        );

        updateValue(
            "aoi_spi_loss_percentage",
            data.aoi_spi_loss_percentage + "%"
        );

        updateValue(
            "spi_aoi_match_percentage",
            data.spi_aoi_match_percentage + "%"
        );

        updateValue(
            "spi_aoi_loss_percentage",
            data.spi_aoi_loss_percentage + "%"
        );

        // ============================================
        // AOI ↔ FCR
        // ============================================

        updateValue(
            "aoi_fcr_matched",
            data.aoi_fcr_matched
        );

        updateValue(
            "aoi_missing_in_fcr",
            data.aoi_missing_in_fcr
        );

        updateValue(
            "fcr_missing_in_aoi",
            data.fcr_missing_in_aoi
        );

        updateValue(
            "aoi_fcr_match_percentage",
            data.aoi_fcr_match_percentage + "%"
        );

        updateValue(
            "aoi_fcr_loss_percentage",
            data.aoi_fcr_loss_percentage + "%"
        );

        updateValue(
            "fcr_aoi_match_percentage",
            data.fcr_aoi_match_percentage + "%"
        );

        updateValue(
            "fcr_aoi_loss_percentage",
            data.fcr_aoi_loss_percentage + "%"
        );

        // ============================================
        // SPI ↔ FCR
        // ============================================

        updateValue(
            "spi_fcr_matched",
            data.spi_fcr_matched
        );

        updateValue(
            "spi_missing_in_fcr",
            data.spi_missing_in_fcr
        );

        updateValue(
            "fcr_missing_in_spi",
            data.fcr_missing_in_spi
        );

        updateValue(
            "spi_fcr_match_percentage",
            data.spi_fcr_match_percentage + "%"
        );

        updateValue(
            "spi_fcr_loss_percentage",
            data.spi_fcr_loss_percentage + "%"
        );

        updateValue(
            "fcr_spi_match_percentage",
            data.fcr_spi_match_percentage + "%"
        );

        updateValue(
            "fcr_spi_loss_percentage",
            data.fcr_spi_loss_percentage + "%"
        );

        // ============================================
        // Overall Health
        // ============================================

        updateValue(
            "overall_total",
            data.overall_total
        );

        updateValue(
            "all_matched",
            data.all_matched
        );

        // ============================================
        // Last Updated
        // ============================================

        const now = new Date();

        document.getElementById(
            "last_updated"
        ).innerText =
            now.toLocaleString();

    }

    catch (error) {

        console.error(error);

        document.getElementById(
            "last_updated"
        ).innerText =
            "API Connection Failed";

    }

}

// =====================================================
// Initial Load
// =====================================================

loadMetrics();

// =====================================================
// Refresh Every 3 Seconds
// =====================================================

setInterval(

    loadMetrics,

    3000

);