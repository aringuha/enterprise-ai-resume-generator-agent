from dataclasses import dataclass, asdict
from threading import Lock

@dataclass
class Metrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    crewai_enabled: bool = True
    ollama_enabled: bool = True

class MetricsService:
    def __init__(self):
        self._metrics = Metrics()
        self._lock = Lock()

    def record_success(self):
        with self._lock:
            self._metrics.total_requests += 1
            self._metrics.successful_requests += 1

    def record_failure(self):
        with self._lock:
            self._metrics.total_requests += 1
            self._metrics.failed_requests += 1

    def snapshot(self):
        with self._lock:
            return asdict(self._metrics)

    def prometheus_snapshot(self):
        with self._lock:
            metrics = asdict(self._metrics)
        lines = [
            "# HELP resume_generator_requests_total Total resume generation requests.",
            "# TYPE resume_generator_requests_total counter",
            f"resume_generator_requests_total {metrics['total_requests']}",
            "# HELP resume_generator_requests_success_total Successful resume generation requests.",
            "# TYPE resume_generator_requests_success_total counter",
            f"resume_generator_requests_success_total {metrics['successful_requests']}",
            "# HELP resume_generator_requests_failed_total Failed resume generation requests.",
            "# TYPE resume_generator_requests_failed_total counter",
            f"resume_generator_requests_failed_total {metrics['failed_requests']}",
            "# HELP resume_generator_crewai_enabled Whether CrewAI is enabled.",
            "# TYPE resume_generator_crewai_enabled gauge",
            f"resume_generator_crewai_enabled {int(metrics['crewai_enabled'])}",
            "# HELP resume_generator_ollama_enabled Whether Ollama usage is enabled.",
            "# TYPE resume_generator_ollama_enabled gauge",
            f"resume_generator_ollama_enabled {int(metrics['ollama_enabled'])}",
        ]
        return "\n".join(lines) + "\n"

metrics_service = MetricsService()
