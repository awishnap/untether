# Roadmap

This roadmap reflects the project's direction based on recent development and community feedback. It is not a commitment — priorities may shift as the ecosystem evolves.

## Near-term

- **Gemini CLI engine** — full integration with Google's Gemini CLI (runner stub exists, pending stable streaming JSON output)
- **Amp engine** — full integration with Sourcegraph's Amp coding agent (runner stub exists, pending stable CLI release)
- **Additional transport backends** — Discord and Slack transports via the plugin system
- **Improved onboarding diagnostics** — expand `untether doctor` with network, permission, and engine health checks

## Mid-term

- **Web dashboard** — browser-based UI for monitoring active runs and session history
- **Multi-user support** — per-user permissions and session isolation in group chats
- **Agent orchestration** — chain multiple engines in a single workflow (e.g., Claude for planning, Codex for execution)
- **Cost tracking enhancements** — per-project budgets, weekly summaries (historical reporting partially shipped via `/stats` in v0.30.0)

## Shipped

- **Webhook-driven workflows** — trigger agent runs from CI/CD events, GitHub webhooks, or external services (shipped in v0.28.0 as the triggers system with cron and webhook support)
- **Session statistics** — `/stats` command for per-engine run counts, actions, and duration across today/week/all-time (shipped in v0.30.0)
- **Device re-authentication** — `/auth` command for headless Codex re-auth via Telegram (shipped in v0.30.0)

## Future

- **Self-hosted relay mode** — run the Telegram bridge on a remote server with secure tunnelling to local agents
- **Additional transports** — Matrix, WhatsApp, or other messaging platforms via the plugin system

## Contributing

Have a feature idea? [Open an issue](https://github.com/littlebearapps/untether/issues) — we'd love to hear what you'd find useful.
