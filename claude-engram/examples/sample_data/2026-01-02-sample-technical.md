# Sample technical note (fictional)

Date: 2026-01-02
Topic: deployment

The main site is deployed from a GitLab CI pipeline to a small VPS. We use Docker Compose, Caddy as the reverse proxy, and automatic TLS. Database is Postgres with daily off-site backups.
