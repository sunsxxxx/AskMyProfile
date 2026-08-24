from __future__ import annotations

import ipaddress
from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class ClientIPResolver:
    trusted_proxies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        networks = tuple(ipaddress.ip_network(item, strict=False) for item in self.trusted_proxies)
        object.__setattr__(self, "_networks", networks)

    def resolve(self, request: Request) -> str:
        peer = request.client.host if request.client else "unknown"
        if not self._is_trusted(peer):
            return peer

        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            chain = [item.strip() for item in forwarded.split(",") if item.strip()]
            # Walk from the proxy-facing side and return the first untrusted address.
            for candidate in reversed(chain):
                if not self._is_trusted(candidate):
                    return candidate
            if chain:
                return chain[0]

        return request.headers.get("cf-connecting-ip") or request.headers.get("x-real-ip") or peer

    def _is_trusted(self, address: str) -> bool:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False
        return any(ip in network for network in self._networks)

