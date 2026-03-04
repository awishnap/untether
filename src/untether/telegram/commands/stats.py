"""Command backend for per-engine session statistics."""

from __future__ import annotations

import time

from ...commands import CommandBackend, CommandContext, CommandResult
from ...session_stats import get_stats


def _format_duration(ms: int) -> str:
    """Format milliseconds as human-readable duration."""
    seconds = ms // 1000
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def _format_last_run(ts: float) -> str:
    """Format timestamp as relative time."""
    if ts <= 0:
        return "never"
    diff = time.time() - ts
    if diff < 60:
        return "just now"
    if diff < 3600:
        return f"{int(diff // 60)}m ago"
    if diff < 86400:
        return f"{int(diff // 3600)}h ago"
    return f"{int(diff // 86400)}d ago"


def _period_label(period: str) -> str:
    if period == "today":
        return "Today"
    if period == "week":
        return "This Week"
    return "All Time"


def format_stats_message(
    engine: str | None,
    period: str,
) -> str:
    """Format stats for display. Returns HTML string."""
    stats = get_stats(engine=engine, period=period)
    label = _period_label(period)

    if not stats:
        scope = f" ({engine})" if engine else ""
        return f"\U0001f4ca <b>Session Stats \u2014 {label}{scope}</b>\n\nNo sessions recorded."

    lines = [f"\U0001f4ca <b>Session Stats \u2014 {label}</b>\n"]
    total_runs = 0
    total_actions = 0
    total_duration = 0

    for s in sorted(stats, key=lambda x: x.run_count, reverse=True):
        lines.append(
            f"<b>{s.engine}</b>: {s.run_count} runs, "
            f"{s.action_count} actions, "
            f"{_format_duration(s.duration_ms)}, "
            f"last {_format_last_run(s.last_run_ts)}"
        )
        total_runs += s.run_count
        total_actions += s.action_count
        total_duration += s.duration_ms

    if len(stats) > 1:
        lines.append(
            f"\n<b>Total</b>: {total_runs} runs, "
            f"{total_actions} actions, "
            f"{_format_duration(total_duration)}"
        )

    return "\n".join(lines)


class StatsCommand:
    """Command backend for session statistics."""

    id = "stats"
    description = "Show per-engine session statistics"

    async def handle(self, ctx: CommandContext) -> CommandResult:
        # Parse args: /stats [engine] [period]
        engine: str | None = None
        period = "today"

        for arg in ctx.args:
            lower = arg.lower()
            if lower in ("today", "week", "all"):
                period = lower
            else:
                engine = lower

        text = format_stats_message(engine=engine, period=period)
        return CommandResult(text=text, notify=True, parse_mode="HTML")


BACKEND: CommandBackend = StatsCommand()
