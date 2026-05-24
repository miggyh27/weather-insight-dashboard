from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class WeatherRecord:
    city: str | None
    country: str | None
    temperature_raw: str | None
    condition: str | None
    humidity_raw: str | None
    wind_raw: str | None
    pressure_raw: str | None
    local_time_raw: str | None
    scraped_at: str
    source_url: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
