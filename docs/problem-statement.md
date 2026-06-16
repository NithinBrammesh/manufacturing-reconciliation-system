QR Code = Unique Board Identifier

Machines:
1. SPI
2. AOI
3. FCR

Flow:
SPI -> AOI -> FCR

Goal:
- Track every QR code
- Calculate stage-wise counts
- Detect missing QR codes
- Calculate loss percentages
- Generate reconciliation reports

1. Watchdog
   - Monitor SPI, AOI and FCR CSV files.
   - Trigger reconciliation automatically when files change.

2. Ripgrep
   - Search QR codes quickly in large CSV files.
   - Find missing records and trace QR history.
   - Debug production data issues.
