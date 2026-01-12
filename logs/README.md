# Logs Directory

This directory contains application logs for debugging and monitoring.

## Contents

- **Application logs**: Runtime logs from the automation script
- **Error logs**: Detailed error traces
- **API logs**: Spotify API request/response logs (future)

## Log Rotation

Logs should be rotated regularly to prevent excessive disk usage:
- Daily logs are kept for 30 days
- Weekly summaries are kept for 1 year

## Notes

- This directory is gitignored
- Logs can be sent to cloud monitoring services in production
