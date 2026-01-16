from .schemas import CauseClass, ModelCardSummary, ScenarioSummary

SCENARIOS = [
    ScenarioSummary(
        id="db-timeout-checkout",
        name="Checkout database timeout",
        description="A checkout service develops a burst of database timeouts after latency rises.",
        expected_cause=CauseClass.DATABASE_TIMEOUT,
        line_count=42,
    ),
    ScenarioSummary(
        id="auth-token-expiry",
        name="Authentication token failure",
        description="Expired signing keys cause a cluster of rejected API requests.",
        expected_cause=CauseClass.AUTHENTICATION_FAILURE,
        line_count=36,
    ),
    ScenarioSummary(
        id="pool-exhaustion-orders",
        name="Connection pool exhaustion",
        description="Queued order requests consume every available database connection.",
        expected_cause=CauseClass.CONNECTION_POOL_EXHAUSTION,
        line_count=48,
    ),
]


MODEL_CARD = ModelCardSummary(
    version="development-baseline",
    anomaly_dataset="LogHub HDFS_v1 (evaluation pending)",
    root_cause_dataset="LogLens synthetic incident corpus (evaluation pending)",
    anomaly_metrics={},
    root_cause_metrics={},
    limitations=[
        "HDFS_v1 provides binary anomaly labels, not root-cause labels.",
        "Root-cause evaluation is performed separately on disclosed synthetic incidents.",
        "The current manifest is replaced after the reproducible training run.",
    ],
)

