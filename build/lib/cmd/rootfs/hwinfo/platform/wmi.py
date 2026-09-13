from __future__ import annotations

from typing import Any

try:
    import wmi as _wmi
except ImportError:
    _wmi = None


class WMIClient:
    """
    Lightweight wrapper around the Python WMI package.

    This module is responsible only for creating and accessing
    WMI connections. Hardware-specific logic belongs in collection/.
    """

    def __init__(self, namespace: str | None = None):
        self.namespace = namespace
        self._client: Any | None = None
        self._failed = False

    @property
    def client(self) -> Any | None:
        if self._failed:
            return None

        if self._client is None:
            if _wmi is None:
                self._failed = True
                return None
            try:
                if self.namespace:
                    self._client = _wmi.WMI(namespace=self.namespace)
                else:
                    self._client = _wmi.WMI()
            except Exception:
                self._failed = True
                return None

        return self._client

    def query(self, class_name: str) -> list[Any]:
        client = self.client
        if client is None:
            return []

        query_method = getattr(client, class_name, None)
        if query_method is None:
            return []

        try:
            return list(query_method())
        except Exception:
            return []


_system_client: WMIClient | None = None
_monitor_client: WMIClient | None = None


def get_system_wmi() -> WMIClient:
    global _system_client

    if _system_client is None:
        _system_client = WMIClient()

    return _system_client


def get_monitor_wmi() -> WMIClient:
    global _monitor_client

    if _monitor_client is None:
        _monitor_client = WMIClient("root\\wmi")

    return _monitor_client
