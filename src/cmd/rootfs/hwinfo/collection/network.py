from __future__ import annotations

import os
import re
import socket
import subprocess

import psutil


VPN_KEYWORDS = (
    "wireguard",
    "tailscale",
    "zerotier",
    "openvpn",
    "tap-",
    "tun",
    "sstp",
    "ike",
)


def _read_file(path: str, default: str = "") -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            value = file.read().strip()

        return value if value else default
    except (OSError, UnicodeError):
        return default


def _get_ipv4_and_mac(
    nic: str,
    addrs: dict,
) -> tuple[str, str]:
    ip = "-"
    mac = "-"

    for addr in addrs.get(nic, []):
        if addr.family == socket.AF_INET:
            ip = addr.address

        elif addr.family == psutil.AF_LINK:
            mac = addr.address.replace(
                "-",
                ":",
            ).upper()

    return ip, mac


# ============================================================================
# Windows Wi-Fi
# ============================================================================

def _windows_wifi_info() -> tuple[str, str]:
    """
    Return:
        (SSID, Wi-Fi standard)
    """
    try:
        output = subprocess.check_output(
            [
                "netsh",
                "wlan",
                "show",
                "interfaces",
            ],
            encoding="utf-8",
            errors="ignore",
            timeout=3,
        )
    except (
        OSError,
        subprocess.SubprocessError,
    ):
        return "Unknown", "Unknown"

    ssid_match = re.search(
        r"^\s*SSID\s*:\s*(.+)$",
        output,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    radio_match = re.search(
        r"^\s*Radio type\s*:\s*(.+)$",
        output,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    ssid = (
        ssid_match.group(1).strip()
        if ssid_match
        else "Unknown"
    )

    wifi_type = (
        radio_match.group(1).strip()
        if radio_match
        else "Unknown"
    )

    return ssid, wifi_type


# ============================================================================
# Linux Wi-Fi
# ============================================================================

def _linux_wifi_info(nic: str) -> tuple[str, str]:
    """
    Return:
        (SSID, Wi-Fi standard)

    Uses `iw` when available.
    No root is required for normal `iw dev <iface> link`.
    """
    iw = _which("iw")

    if iw is None:
        return "Unknown", "Unknown"

    try:
        output = subprocess.check_output(
            [
                iw,
                "dev",
                nic,
                "link",
            ],
            encoding="utf-8",
            errors="ignore",
            timeout=3,
        )
    except (
        OSError,
        subprocess.SubprocessError,
    ):
        return "Unknown", "Unknown"

    if "Not connected" in output:
        return "Not Connected", "Unknown"

    ssid_match = re.search(
        r"SSID:\s*(.+)$",
        output,
        flags=re.MULTILINE,
    )

    ssid = (
        ssid_match.group(1).strip()
        if ssid_match
        else "Unknown"
    )

    # `iw dev <iface> link` does not directly expose a friendly
    # Wi-Fi generation such as Wi-Fi 5 / Wi-Fi 6.
    # Leave this as Unknown rather than guessing.
    return ssid, "Unknown"


def _which(command: str) -> str | None:
    """
    Small local equivalent of shutil.which.
    """
    import shutil

    return shutil.which(command)


def _is_linux_wireless(nic: str) -> bool:
    return os.path.isdir(
        f"/sys/class/net/{nic}/wireless"
    )


# ============================================================================
# Interface helpers
# ============================================================================

def _interface_speed(nic: str, stat) -> str:
    """
    Get interface speed in Mbps.
    """
    speed = getattr(stat, "speed", 0)

    if isinstance(speed, (int, float)) and speed > 0:
        return f"{int(speed)} Mbps"

    # Linux fallback.
    if os.name != "nt":
        raw = _read_file(
            f"/sys/class/net/{nic}/speed",
            "0",
        )

        try:
            linux_speed = int(raw)

            if linux_speed > 0:
                return f"{linux_speed} Mbps"
        except ValueError:
            pass

    return "-"


def _is_vpn_interface(nic: str) -> bool:
    lower = nic.lower()

    return any(
        keyword in lower
        for keyword in VPN_KEYWORDS
    )


def _is_linux_loopback(nic: str) -> bool:
    return nic == "lo"


# ============================================================================
# Public collector
# ============================================================================

def collect_network() -> list[dict]:
    networks: list[dict] = []

    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        vpn_detected = False

        # ---------------------------------------------------------------
        # Platform-specific Wi-Fi information
        # ---------------------------------------------------------------
        windows_wifi_name = "Unknown"
        windows_wifi_type = "Unknown"

        if os.name == "nt":
            (
                windows_wifi_name,
                windows_wifi_type,
            ) = _windows_wifi_info()

        # ---------------------------------------------------------------
        # Interfaces
        # ---------------------------------------------------------------
        for nic, stat in stats.items():
            if not stat.isup:
                continue

            if _is_linux_loopback(nic):
                continue

            lower_nic = nic.lower()

            ip, mac = _get_ipv4_and_mac(
                nic,
                addrs,
            )

            speed = _interface_speed(
                nic,
                stat,
            )

            # -----------------------------------------------------------
            # VPN
            # -----------------------------------------------------------
            if (
                _is_vpn_interface(nic)
                and "teredo" not in lower_nic
            ):
                vpn_detected = True

                networks.append(
                    {
                        "adapter": nic,
                        "type": "VPN Tunnel",
                        "name": nic,
                        "standard": "Secure Tunnel",
                        "speed": speed,
                        "ip": ip,
                        "mac": mac,
                        "vpn": "ON",
                    }
                )

                continue

            # -----------------------------------------------------------
            # Wi-Fi
            # -----------------------------------------------------------
            if os.name == "nt":
                is_wifi = any(
                    keyword in lower_nic
                    for keyword in (
                        "wi-fi",
                        "wifi",
                        "wireless",
                    )
                )

                if is_wifi:
                    wifi_name = windows_wifi_name
                    wifi_type = windows_wifi_type

                    networks.append(
                        {
                            "adapter": nic,
                            "type": "Wireless (Wi-Fi)",
                            "name": wifi_name,
                            "standard": wifi_type,
                            "speed": speed,
                            "ip": ip,
                            "mac": mac,
                            "vpn": "OFF",
                        }
                    )

                    continue

            else:
                # Linux: wireless interface is exposed through sysfs.
                if _is_linux_wireless(nic):
                    wifi_name, wifi_type = _linux_wifi_info(
                        nic
                    )

                    networks.append(
                        {
                            "adapter": nic,
                            "type": "Wireless (Wi-Fi)",
                            "name": wifi_name,
                            "standard": wifi_type,
                            "speed": speed,
                            "ip": ip,
                            "mac": mac,
                            "vpn": "OFF",
                        }
                    )

                    continue

            # -----------------------------------------------------------
            # Ethernet
            # -----------------------------------------------------------
            if (
                "ethernet" in lower_nic
                or lower_nic.startswith(("en", "eth"))
            ):
                networks.append(
                    {
                        "adapter": nic,
                        "type": "Wired (Ethernet)",
                        "name": "LAN",
                        "standard": "Wired Connection",
                        "speed": speed,
                        "ip": ip,
                        "mac": mac,
                        "vpn": "OFF",
                    }
                )

                continue

            # -----------------------------------------------------------
            # Other active interfaces
            # -----------------------------------------------------------
            networks.append(
                {
                    "adapter": nic,
                    "type": "Network Interface",
                    "name": nic,
                    "standard": "Unknown",
                    "speed": speed,
                    "ip": ip,
                    "mac": mac,
                    "vpn": "OFF",
                }
            )

        # ---------------------------------------------------------------
        # Apply system-wide VPN status.
        # ---------------------------------------------------------------
        for network in networks:
            if not network["type"].startswith("VPN"):
                network["vpn"] = (
                    "ON"
                    if vpn_detected
                    else "OFF"
                )

        networks.append(
            {
                "adapter": "System Wide",
                "type": "Global Status",
                "name": "VPN Protection",
                "standard": (
                    "Active"
                    if vpn_detected
                    else "Inactive"
                ),
                "speed": "-",
                "ip": "-",
                "mac": "-",
                "vpn": "SYSTEM",
            }
        )

    except Exception:
        pass

    return (
        networks
        if networks
        else [
            {
                "adapter": "None",
                "type": "Unknown",
                "name": "No Connection",
                "standard": "-",
                "speed": "-",
                "ip": "-",
                "mac": "-",
                "vpn": "-",
            }
        ]
    )