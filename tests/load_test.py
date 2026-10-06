"""Executa carga concorrente na API usando apenas a biblioteca padrao."""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Teste de carga HTTP concorrente")
    parser.add_argument("url", help="URL completa do endpoint submetido a carga")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--expected-statuses",
        default="200,429,504",
        help="Codigos HTTP aceitos, separados por virgula",
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()

    if arguments.requests < 1:
        parser.error("--requests deve ser maior que zero")
    if arguments.concurrency < 1:
        parser.error("--concurrency deve ser maior que zero")
    if arguments.timeout <= 0:
        parser.error("--timeout deve ser maior que zero")

    return arguments


# Usa a posição arredondada para cima na lista ordenada (nearest-rank).
# p95 é o tempo abaixo do qual ficaram pelo menos 95% das amostras.
def percentile(values: list[float], percentage: float) -> float | None:
    if not values:
        return None

    ordered = sorted(values)
    index = max(0, math.ceil((percentage / 100) * len(ordered)) - 1)
    return round(ordered[index], 2)


def latency_summary(values: list[float]) -> dict[str, float | None]:
    return {
        "minimum": round(min(values), 2) if values else None,
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
        "maximum": round(max(values), 2) if values else None,
    }


# Conta recusa HTTP, como 429, separada de falha de rede. As duas situações
# têm causas diferentes e não devem aparecer como o mesmo erro no relatório.
def request_once(url: str, timeout: float) -> dict[str, object]:
    started = time.perf_counter()
    request = Request(url, headers={"User-Agent": "spi-ii-load-test/1.0"})

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = response.status
            error = None
    except HTTPError as exception:
        body = exception.read().decode("utf-8", errors="replace")
        status = exception.code
        error = None
    except (URLError, TimeoutError, OSError) as exception:
        body = ""
        status = None
        error = f"{type(exception).__name__}: {exception}"

    return {
        "status": status,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "body": body,
        "error": error,
    }


def health_url_for(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}/health"


def main() -> int:
    arguments = parse_arguments()
    expected_statuses = {
        int(status.strip())
        for status in arguments.expected_statuses.split(",")
        if status.strip()
    }
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()

    # requests é o total enviado; concurrency limita quantas chamadas podem
    # rodar juntas. Não há garantia de que todas comecem no mesmo instante.
    with ThreadPoolExecutor(max_workers=arguments.concurrency) as executor:
        futures = [
            executor.submit(request_once, arguments.url, arguments.timeout)
            for _ in range(arguments.requests)
        ]
        responses = [future.result() for future in as_completed(futures)]

    duration_seconds = time.perf_counter() - started
    health = request_once(health_url_for(arguments.url), arguments.timeout)
    statuses = Counter(
        str(response["status"])
        for response in responses
        if response["status"] is not None
    )
    transport_errors = [
        str(response["error"])
        for response in responses
        if response["error"] is not None
    ]
    unexpected_statuses = sorted(
        int(status) for status in statuses if int(status) not in expected_statuses
    )
    latencies = [float(response["elapsed_ms"]) for response in responses]
    # Separa os tempos por status: uma recusa rápida não mede o tempo da busca.
    latencies_by_status = {
        status: [
            float(response["elapsed_ms"])
            for response in responses
            if str(response["status"]) == status
        ]
        for status in statuses
    }
    bodies_by_status: dict[str, str] = {}

    for response in responses:
        status = response["status"]
        if status is not None and str(status) not in bodies_by_status:
            bodies_by_status[str(status)] = str(response["body"])[:500]

    # Os status aceitos vêm da linha de comando. Para o ensaio de capacidade,
    # usar apenas 200; aceitar 429 aqui não significa que todas as buscas passaram.
    criterion_met = (
        len(responses) == arguments.requests
        and not transport_errors
        and not unexpected_statuses
        and health["status"] == 200
    )
    report = {
        "started_at_utc": started_at,
        "target": arguments.url,
        "health_check": health_url_for(arguments.url),
        "configuration": {
            "requests": arguments.requests,
            "concurrency": arguments.concurrency,
            "timeout_seconds": arguments.timeout,
            "expected_statuses": sorted(expected_statuses),
        },
        "results": {
            "completed_requests": len(responses),
            "duration_seconds": round(duration_seconds, 3),
            "throughput_requests_per_second": round(
                len(responses) / duration_seconds, 2
            ),
            "status_counts": dict(sorted(statuses.items())),
            "transport_error_count": len(transport_errors),
            "transport_error_samples": transport_errors[:5],
            "unexpected_statuses": unexpected_statuses,
            "latency_ms": latency_summary(latencies),
            "latency_ms_by_status": {
                status: latency_summary(values)
                for status, values in sorted(latencies_by_status.items())
            },
            "response_samples_by_status": bodies_by_status,
            "post_load_health_status": health["status"],
            "post_load_health_elapsed_ms": health["elapsed_ms"],
            "criterion_met": criterion_met,
        },
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)

    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered + "\n", encoding="utf-8")

    return 0 if criterion_met else 1


if __name__ == "__main__":
    raise SystemExit(main())
