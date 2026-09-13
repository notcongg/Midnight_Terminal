from __future__ import annotations

import re
import socket
import subprocess

import psutil


def collect_network() -> list[dict]:
    networks: list[dict] = []
    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        wifi_name, wifi_type = "Unknown", "Unknown"

        try:
            wifi = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"],
                encoding="utf-8",
                errors="ignore",
            )
            ssid_match = re.search(r"^\s*SSID\s*:\s*(.+)$", wifi, re.MULTILINE)
            radio_match = re.search(r"^\s*Radio type\s*:\s*(.+)$", wifi, re.MULTILINE)
            if ssid_match:
                wifi_name = ssid_match.group(1).strip()
            if radio_match:
                wifi_type = radio_match.group(1).strip()
        except Exception:
            pass

        vpn_detected = False
        vpn_keywords = [
            "wireguard",
            "tailscale",
            "zerotier",
            "openvpn",
            "tap-",
            "tun",
            "sstp",
            "ike",
        ]

        for nic, stat in stats.items():
            if not stat.isup:
                continue

            lower_nic = nic.lower()
            ip, mac = "-", "-"

            if nic in addrs:
                for addr in addrs[nic]:
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                    elif addr.family == psutil.AF_LINK:
                        mac = addr.address.replace("-", ":").upper()

            if any(kw in lower_nic for kw in ["wi-fi", "wifi", "wireless"]):
                networks.append(
                    {
                        "adapter": nic,
                        "type": "Wireless (Wi-Fi)",
                        "name": wifi_name,
                        "standard": wifi_type,
                        "speed": f"{stat.speed} Mbps",
                        "ip": ip,
                        "mac": mac,
                        "vpn": "OFF",
                    }
                )
            elif any(kw in lower_nic for kw in vpn_keywords) and "teredo" not in lower_nic:
                vpn_detected = True
                networks.append(
                    {
                        "adapter": nic,
                        "type": "VPN Tunnel",
                        "name": nic,
                        "standard": "Secure Tunnel",
                        "speed": f"{stat.speed} Mbps",
                        "ip": ip,
                        "mac": mac,
                        "vpn": "ON",
                    }
                )
            elif "ethernet" in lower_nic:
                networks.append(
                    {
                        "adapter": nic,
                        "type": "Wired (Ethernet)",
                        "name": "LAN",
                        "standard": "Wired Connection",
                        "speed": f"{stat.speed} Mbps",
                        "ip": ip,
                        "mac": mac,
                        "vpn": "OFF",
                    }
                )

        for net in networks:
            if not net["type"].startswith("VPN"):
                net["vpn"] = "ON" if vpn_detected else "OFF"

        networks.append(
            {
                "adapter": "System Wide",
                "type": "Global Status",
                "name": "VPN Protection",
                "standard": "Active" if vpn_detected else "Inactive",
                "speed": "-",
                "ip": "-",
                "mac": "-",
                "vpn": "SYSTEM",
            }
        )
    except Exception:
        pass

    return networks if networks else [
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
