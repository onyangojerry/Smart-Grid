# Author: Jerry Onyango
# Contribution: Implements v1 tariff state modeling for flat and time-of-use pricing with export credit support.
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TariffState:
    import_price: float
    export_price: float
    is_peak: bool
    is_shoulder: bool
    tariff_name: str


@dataclass(frozen=True)
class TimeOfUseWindow:
    start_hour: int
    end_hour: int
    import_price: float
    export_price: float
    label: str


def build_tariff_state(ts: datetime, policy: dict[str, object], default_import: float, default_export: float) -> TariffState:
    tariff_model = str(policy.get("tariff_model", "flat"))

    if tariff_model == "flat":
        return TariffState(
            import_price=float(policy.get("flat_import_price", default_import)),
            export_price=float(policy.get("export_credit_price", default_export)),
            is_peak=False,
            is_shoulder=False,
            tariff_name="flat",
        )

    windows_raw = policy.get("tou_windows", [])
    windows: list[TimeOfUseWindow] = []
    if isinstance(windows_raw, list):
        for item in windows_raw:
            if not isinstance(item, dict):
                continue
            windows.append(
                TimeOfUseWindow(
                    start_hour=int(item.get("start_hour", 0)),
                    end_hour=int(item.get("end_hour", 24)),
                    import_price=float(item.get("import_price", default_import)),
                    export_price=float(item.get("export_price", default_export)),
                    label=str(item.get("label", "shoulder")),
                )
            )

    hour = ts.hour
    for window in windows:
        if window.start_hour <= hour < window.end_hour:
            label = window.label.lower()
            return TariffState(
                import_price=window.import_price,
                export_price=window.export_price,
                is_peak=label == "peak",
                is_shoulder=label == "shoulder",
                tariff_name=label,
            )

    return TariffState(
        import_price=default_import,
        export_price=float(policy.get("export_credit_price", default_export)),
        is_peak=False,
        is_shoulder=True,
        tariff_name="shoulder",
    )
