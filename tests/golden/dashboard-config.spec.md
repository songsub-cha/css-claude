# Golden: dashboard config example

`config/dashboard-config.example.json` parses as JSON and contains keys:
- dashboard_enabled (bool)
- dashboard_url (string)
- database_url (string with asyncpg)
- claude_cli (string)
- queue_dir (string ending in /queue)
- default_palette (array of ≥5 hex strings)
