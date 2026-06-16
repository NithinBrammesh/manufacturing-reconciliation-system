async function loadMetrics() {

    try {

        const response =
            await fetch(
                "http://localhost:5000/api/reconciliation"
            );

        const data =
            await response.json();

        document.getElementById(
            "total_aoi"
        ).innerText =
            data.total_aoi;

        document.getElementById(
            "total_spi"
        ).innerText =
            data.total_spi;

        document.getElementById(
            "matched"
        ).innerText =
            data.matched;

        document.getElementById(
            "missing_in_spi"
        ).innerText =
            data.missing_in_spi;

        document.getElementById(
            "missing_in_aoi"
        ).innerText =
            data.missing_in_aoi;

        document.getElementById(
            "aoi_match_percentage"
        ).innerText =
            data.aoi_match_percentage + "%";

        document.getElementById(
            "aoi_loss_percentage"
        ).innerText =
            data.aoi_loss_percentage + "%";

        document.getElementById(
            "spi_match_percentage"
        ).innerText =
            data.spi_match_percentage + "%";

        document.getElementById(
            "spi_loss_percentage"
        ).innerText =
            data.spi_loss_percentage + "%";

    }
    catch (error) {

        console.error(error);

    }

}

loadMetrics();

setInterval(
    loadMetrics,
    3000
);