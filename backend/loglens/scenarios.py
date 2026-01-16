from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .schemas import CauseClass, ScenarioSummary


@dataclass(frozen=True, slots=True)
class Scenario:
    summary: ScenarioSummary
    lines: tuple[str, ...]


def _timeline(
    incident: dict[int, tuple[tuple[str, str], ...]],
    *,
    minutes: int = 18,
) -> tuple[str, ...]:
    origin = datetime(2026, 4, 18, 9, 0, 0)
    lines: list[str] = []
    for minute in range(minutes):
        timestamp = (origin + timedelta(minutes=minute)).isoformat()
        lines.append(f"{timestamp} INFO gateway request batch completed status=200")
        for severity, message in incident.get(minute, ()):
            lines.append(f"{timestamp} {severity} {message}")
    return tuple(lines)


def _scenario(
    *,
    scenario_id: str,
    name: str,
    description: str,
    expected_cause: CauseClass,
    incident: dict[int, tuple[tuple[str, str], ...]],
) -> Scenario:
    lines = _timeline(incident)
    return Scenario(
        summary=ScenarioSummary(
            id=scenario_id,
            name=name,
            description=description,
            expected_cause=expected_cause,
            line_count=len(lines),
        ),
        lines=lines,
    )


SCENARIO_CATALOG = {
    scenario.summary.id: scenario
    for scenario in (
        _scenario(
            scenario_id="db-timeout-checkout",
            name="Checkout database timeout",
            description=(
                "A checkout service develops a burst of database timeouts after latency rises."
            ),
            expected_cause=CauseClass.DATABASE_TIMEOUT,
            incident={
                6: (("WARN", "subsystem=database dependency=db-primary latency elevated"),),
                7: (("ERROR", "checkout query timed out after 2500ms"),),
                8: (
                    ("WARN", "database round trip above threshold"),
                    ("ERROR", "DB-504 deadline exceeded reading orders"),
                ),
                9: (("ERROR", "transaction timed out awaiting db-primary"),),
            },
        ),
        _scenario(
            scenario_id="auth-token-expiry",
            name="Authentication token failure",
            description="Expired signing keys cause a cluster of rejected API requests.",
            expected_cause=CauseClass.AUTHENTICATION_FAILURE,
            incident={
                6: (("WARN", "subsystem=identity auth-gateway signing key expired"),),
                7: (("ERROR", "AUTH-401 invalid bearer token"),),
                8: (
                    ("WARN", "JWT audience mismatch"),
                    ("ERROR", "request rejected as unauthenticated"),
                ),
                9: (("ERROR", "credential validation denied"),),
            },
        ),
        _scenario(
            scenario_id="pool-exhaustion-orders",
            name="Connection pool exhaustion",
            description="Queued order requests consume every available database connection.",
            expected_cause=CauseClass.CONNECTION_POOL_EXHAUSTION,
            incident={
                6: (("WARN", "subsystem=database resource=connection-pool saturated"),),
                7: (("ERROR", "no connection available for order worker"),),
                8: (
                    ("WARN", "connection checkout waiters=68"),
                    ("ERROR", "pool acquisition timed out"),
                ),
                9: (("ERROR", "POOL-503 capacity exhausted"),),
            },
        ),
        _scenario(
            scenario_id="healthy-checkout",
            name="Healthy checkout traffic",
            description="A stable request stream with no detected anomalous window.",
            expected_cause=CauseClass.UNKNOWN,
            incident={
                7: (("INFO", "database latency within service objective"),),
                12: (("DEBUG", "connection pool has spare capacity"),),
            },
        ),
        _scenario(
            scenario_id="ambiguous-degradation",
            name="Ambiguous service degradation",
            description="An anomalous burst lacks enough evidence for a supported root cause.",
            expected_cause=CauseClass.UNKNOWN,
            incident={
                6: (("WARN", "dependency returned an unusual response"),),
                7: (("ERROR", "operation failed without a classified signature"),),
                8: (
                    ("WARN", "scheduler delay increased"),
                    ("ERROR", "human review required for unsupported failure"),
                ),
                9: (("ERROR", "generic service failure code UNKNOWN-520"),),
            },
        ),
    )
}


def list_scenario_summaries() -> list[ScenarioSummary]:
    return [scenario.summary for scenario in SCENARIO_CATALOG.values()]
