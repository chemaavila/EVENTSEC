from __future__ import annotations

import hashlib
import ipaddress
import logging
from dataclasses import dataclass
from functools import lru_cache

from .config import ThreatMapConfig
from .schema import Asn, Geo

logger = logging.getLogger("eventsec.threatmap")


@dataclass(frozen=True)
class GeoAsn:
    geo: Geo | None
    asn: Asn | None


def _is_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_global
    except Exception:
        return False


def _fallback_coordinates(ip: str) -> Geo:
    digest = hashlib.sha256(ip.encode("utf-8")).digest()
    lat_seed = int.from_bytes(digest[:4], "big") / 2**32
    lon_seed = int.from_bytes(digest[4:8], "big") / 2**32
    lat = (lat_seed * 140) - 70
    lon = (lon_seed * 360) - 180
    return Geo(lat=round(lat, 6), lon=round(lon, 6), approx=True)


class GeoIpEnricher:
    def __init__(self, cfg: ThreatMapConfig):
        self._cfg = cfg
        self._reader_city = None
        self._reader_asn = None
        self._warned = False
        self._init_readers()

    def _init_readers(self) -> None:
        if not self._cfg.maxmind_db_path:
            if not self._warned:
                logger.warning(
                    "MAXMIND_DB_PATH is not set. Geo enrichment will be unavailable."
                )
                self._warned = True
            return
        try:
            import geoip2.database  # type: ignore

            # Single DB path may be City DB; ASN may not exist. We'll try both readers on same path.
            self._reader_city = geoip2.database.Reader(self._cfg.maxmind_db_path)
            self._reader_asn = geoip2.database.Reader(self._cfg.maxmind_db_path)
        except Exception as exc:
            if not self._warned:
                logger.warning(
                    "GeoIP DB not usable (%s). Geo enrichment disabled (no random coords).",
                    exc,
                )
                self._warned = True
            self._reader_city = None
            self._reader_asn = None

    @lru_cache(maxsize=50_000)
    def lookup(self, ip: str) -> GeoAsn:
        # Deterministic: never randomize. If unknown, return None fields.
        if not ip:
            return GeoAsn(geo=None, asn=None)
        if not _is_public_ip(ip) and not self._cfg.fallback_coords:
            return GeoAsn(geo=None, asn=None)
        if self._reader_city is None and self._reader_asn is None:
            if self._cfg.fallback_coords:
                return GeoAsn(geo=_fallback_coordinates(ip), asn=None)
            return GeoAsn(geo=None, asn=None)

        geo: Geo | None = None
        asn: Asn | None = None

        # City lookup
        if self._reader_city is not None:
            try:
                resp = self._reader_city.city(ip)
                lat = resp.location.latitude
                lon = resp.location.longitude
                if lat is not None and lon is not None:
                    geo = Geo(
                        lat=float(lat),
                        lon=float(lon),
                        country=(resp.country.iso_code or resp.country.name),
                        city=(resp.city.name),
                    )
            except Exception:
                pass

        # ASN lookup (will work if DB supports it)
        if self._reader_asn is not None:
            try:
                resp = self._reader_asn.asn(ip)
                asn = Asn(
                    asn=(
                        f"AS{resp.autonomous_system_number}"
                        if resp.autonomous_system_number
                        else None
                    ),
                    org=(resp.autonomous_system_organization),
                )
            except Exception:
                pass

        if geo is None and self._cfg.fallback_coords:
            geo = _fallback_coordinates(ip)

        return GeoAsn(geo=geo, asn=asn)
