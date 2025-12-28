#!/usr/bin/env python3
"""
PROTOXOL Endpoint Triage (defensive).
- host info
- processes + network
- persistence artifacts
- suspicious file discovery + hashes
- optional YARA + reputation checks
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
except ImportError:
    print("[-] Missing dependency: psutil. Install with: pip install psutil")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("[-] Missing dependency: requests. Install with: pip install requests")
    sys.exit(1)

try:
    import yara  # type: ignore
    YARA_AVAILABLE = True
except Exception:
    YARA_AVAILABLE = False

def utc_now_iso() -> str:
    return dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()

def local_now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def safe_run(cmd: List[str], timeout: int = 20) -> Dict[str, Any]:
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return {
            "cmd": cmd,
            "returncode": p.returncode,
            "stdout": p.stdout[:200000],
            "stderr": p.stderr[:200000],
        }
    except subprocess.TimeoutExpired:
        return {"cmd": cmd, "error": "timeout"}
    except Exception as e:
        return {"cmd": cmd, "error": str(e)}

def mkdirp(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def sha256_file(path: Path, max_mb: int = 200) -> Optional[str]:
    try:
        st = path.stat()
        if st.st_size > max_mb * 1024 * 1024:
            return None
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def is_probably_executable(p: Path) -> bool:
    ext = p.suffix.lower()
    high_exts = {
        ".exe",
        ".dll",
        ".sys",
        ".bat",
        ".cmd",
        ".ps1",
        ".vbs",
        ".js",
        ".jar",
        ".scr",
        ".msi",
        ".dmg",
        ".pkg",
        ".app",
        ".sh",
        ".bin",
        ".elf",
        ".so",
        ".py",
    }
    if ext in high_exts:
        return True
    try:
        if os.name != "nt":
            return os.access(str(p), os.X_OK)
    except Exception:
        pass
    return False

def looks_suspicious_name(name: str) -> bool:
    n = name.lower()
    patterns = [
        r"update\d{0,3}\.exe$",
        r"svchost\d+\.exe$",
        r"chrome_update\.exe$",
        r"winlogon\d+\.exe$",
        r"runtime(\d+)?\.exe$",
        r"\btemp\b",
        r"\btmp\b",
        r"\bappdata\b",
        r"\broaming\b",
        r"\blaunchagent\b",
        r"\blaunchdaemon\b",
    ]
    return any(re.search(pat, n) for pat in patterns)

def default_scan_paths() -> List[Path]:
    home = Path.home()
    paths: List[Path] = []
    system = platform.system().lower()
    if "windows" in system:
        for env in ["TEMP", "TMP", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA"]:
            v = os.environ.get(env)
            if v:
                paths.append(Path(v))
        paths += [
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Temp",
            Path(r"C:\Users\Public"),
        ]
    elif "darwin" in system or "mac" in system:
        paths += [
            Path("/tmp"),
            Path("/var/tmp"),
            home / "Downloads",
            home / "Library" / "LaunchAgents",
            Path("/Library/LaunchAgents"),
            Path("/Library/LaunchDaemons"),
        ]
    else:
        paths += [
            Path("/tmp"),
            Path("/var/tmp"),
            home / "Downloads",
            Path("/etc/cron.d"),
            Path("/etc/cron.daily"),
            Path("/etc/systemd/system"),
            home / ".config" / "autostart",
        ]
    uniq = []
    seen = set()
    for p in paths:
        try:
            rp = p.resolve()
        except Exception:
            rp = p
        key = str(rp)
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq

class VirusTotalClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base = "https://www.virustotal.com/api/v3"
        self.sess = requests.Session()
        self.sess.headers.update({"x-apikey": api_key, "User-Agent": "PROTOXOL-Triage/1.0"})

    def file_report(self, sha256: str) -> Dict[str, Any]:
        url = f"{self.base}/files/{sha256}"
        r = self.sess.get(url, timeout=20)
        return {"sha256": sha256, "status": r.status_code, "json": safe_json(r)}

    def ip_report(self, ip: str) -> Dict[str, Any]:
        url = f"{self.base}/ip_addresses/{ip}"
        r = self.sess.get(url, timeout=20)
        return {"ip": ip, "status": r.status_code, "json": safe_json(r)}

    def domain_report(self, domain: str) -> Dict[str, Any]:
        url = f"{self.base}/domains/{domain}"
        r = self.sess.get(url, timeout=20)
        return {"domain": domain, "status": r.status_code, "json": safe_json(r)}

class OTXClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base = "https://otx.alienvault.com/api/v1"
        self.sess = requests.Session()
        self.sess.headers.update({"X-OTX-API-KEY": api_key, "User-Agent": "PROTOXOL-Triage/1.0"})

    def ip_general(self, ip: str) -> Dict[str, Any]:
        url = f"{self.base}/indicators/IPv4/{ip}/general"
        r = self.sess.get(url, timeout=20)
        return {"ip": ip, "status": r.status_code, "json": safe_json(r)}

    def domain_general(self, domain: str) -> Dict[str, Any]:
        url = f"{self.base}/indicators/domain/{domain}/general"
        r = self.sess.get(url, timeout=20)
        return {"domain": domain, "status": r.status_code, "json": safe_json(r)}

    def file_general(self, sha256: str) -> Dict[str, Any]:
        url = f"{self.base}/indicators/file/{sha256}/general"
        r = self.sess.get(url, timeout=20)
        return {"sha256": sha256, "status": r.status_code, "json": safe_json(r)}

def safe_json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text[:200000]}

def collect_host_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "collected_utc": utc_now_iso(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": sys.version,
        },
        "hostname": socket.gethostname(),
    }
    try:
        boot = dt.datetime.fromtimestamp(psutil.boot_time())
        info["boot_time_local"] = boot.isoformat()
        info["uptime_seconds"] = int(time.time() - psutil.boot_time())
    except Exception:
        pass
    try:
        users = []
        for u in psutil.users():
            users.append({
                "name": getattr(u, "name", None),
                "terminal": getattr(u, "terminal", None),
                "host": getattr(u, "host", None),
                "started": getattr(u, "started", None),
            })
        info["logged_in_users"] = users
    except Exception:
        pass
    try:
        addrs = psutil.net_if_addrs()
        ip_map: Dict[str, Any] = {}
        for iface, lst in addrs.items():
            ip_map[iface] = []
            for a in lst:
                ip_map[iface].append({
                    "family": str(a.family),
                    "address": a.address,
                    "netmask": a.netmask,
                    "broadcast": a.broadcast,
                })
        info["network_interfaces"] = ip_map
    except Exception:
        pass
    return info

def collect_processes_and_connections() -> Dict[str, Any]:
    procs: List[Dict[str, Any]] = []
    suspicious: List[Dict[str, Any]] = []
    for p in psutil.process_iter(attrs=["pid", "name", "username", "create_time"]):
        entry: Dict[str, Any] = dict(p.info)
        pid = entry.get("pid")
        try:
            pp = psutil.Process(pid)
            entry["exe"] = pp.exe() if hasattr(pp, "exe") else None
            entry["cmdline"] = pp.cmdline()
            entry["ppid"] = pp.ppid()
            entry["cwd"] = pp.cwd() if hasattr(pp, "cwd") else None
        except Exception:
            pass
        try:
            conns = []
            for c in p.connections(kind="inet"):
                conns.append({
                    "fd": c.fd,
                    "family": str(c.family),
                    "type": str(c.type),
                    "laddr": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else None,
                    "raddr": f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else None,
                    "status": c.status,
                })
            entry["connections"] = conns[:2000]
        except Exception:
            pass
        procs.append(entry)
        name = (entry.get("name") or "").lower()
        exe = (entry.get("exe") or "")
        cmd = " ".join(entry.get("cmdline") or [])
        if looks_suspicious_name(name) or ("powershell" in name and "-enc" in cmd.lower()) or ("base64" in cmd.lower()):
            suspicious.append({
                "pid": pid,
                "name": entry.get("name"),
                "username": entry.get("username"),
                "exe": exe,
                "cmdline": cmd[:2000],
            })
    net: List[Dict[str, Any]] = []
    try:
        for c in psutil.net_connections(kind="inet"):
            net.append({
                "pid": c.pid,
                "family": str(c.family),
                "type": str(c.type),
                "laddr": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else None,
                "raddr": f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else None,
                "status": c.status,
            })
    except Exception:
        pass
    return {
        "processes": procs,
        "process_suspicious_heuristics": suspicious,
        "net_connections": net,
    }

def collect_persistence() -> Dict[str, Any]:
    system = platform.system().lower()
    out: Dict[str, Any] = {"os": system, "artifacts": {}, "commands": []}
    if "windows" in system:
        run_keys = [
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce",
            r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
            r"HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce",
        ]
        out["artifacts"]["registry_run_keys"] = run_keys
        out["commands"].append(safe_run(["schtasks", "/query", "/fo", "CSV", "/v"], timeout=30))
        out["commands"].append(safe_run(["sc", "query", "state=", "all"], timeout=30))
        startup_paths = []
        appdata = os.environ.get("APPDATA")
        programdata = os.environ.get("PROGRAMDATA")
        if appdata:
            startup_paths.append(str(Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"))
        if programdata:
            startup_paths.append(str(Path(programdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"))
        out["artifacts"]["startup_folders"] = startup_paths
    elif "darwin" in system or "mac" in system:
        home = Path.home()
        plist_dirs = [
            home / "Library" / "LaunchAgents",
            Path("/Library/LaunchAgents"),
            Path("/Library/LaunchDaemons"),
        ]
        out["artifacts"]["launchd_plist_dirs"] = [str(p) for p in plist_dirs]
        out["commands"].append(safe_run(["crontab", "-l"], timeout=10))
        out["commands"].append(safe_run(["sudo", "-n", "crontab", "-l"], timeout=10))
        out["commands"].append(safe_run(["launchctl", "list"], timeout=20))
    else:
        out["commands"].append(safe_run(["systemctl", "list-unit-files", "--type=service"], timeout=20))
        out["commands"].append(safe_run(["systemctl", "list-timers", "--all"], timeout=10))
        out["commands"].append(safe_run(["crontab", "-l"], timeout=10))
        out["commands"].append(safe_run(["sudo", "-n", "crontab", "-l"], timeout=10))
        cron_paths = [
            Path("/etc/crontab"),
            Path("/etc/cron.d"),
            Path("/etc/cron.daily"),
            Path("/etc/cron.hourly"),
            Path("/etc/cron.weekly"),
            Path("/etc/cron.monthly"),
        ]
        out["artifacts"]["cron_paths"] = [str(p) for p in cron_paths]
        out["artifacts"]["systemd_paths"] = ["/etc/systemd/system", "/lib/systemd/system", str(Path.home() / ".config/systemd/user")]
    return out

def discover_files(paths: List[Path], since_days: int, max_files: int) -> Dict[str, Any]:
    cutoff = time.time() - since_days * 24 * 3600
    found: List[Dict[str, Any]] = []
    errors: List[str] = []
    count = 0
    for base in paths:
        try:
            if not base.exists():
                continue
            for root, dirs, files in os.walk(base, followlinks=False):
                if count >= max_files:
                    break
                for fn in files:
                    if count >= max_files:
                        break
                    p = Path(root) / fn
                    try:
                        st = p.stat()
                        if st.st_mtime < cutoff:
                            continue
                        exeish = is_probably_executable(p)
                        susname = looks_suspicious_name(p.name)
                        if not exeish and not susname and st.st_mtime < (time.time() - 24 * 3600):
                            continue
                        entry = {
                            "path": str(p),
                            "size": st.st_size,
                            "mtime": dt.datetime.fromtimestamp(st.st_mtime).isoformat(),
                            "ctime": dt.datetime.fromtimestamp(st.st_ctime).isoformat(),
                            "executable_like": exeish,
                            "suspicious_name_heuristic": susname,
                        }
                        found.append(entry)
                        count += 1
                    except Exception:
                        continue
        except Exception as e:
            errors.append(f"{base}: {e}")
    return {"cutoff_days": since_days, "max_files": max_files, "files": found, "errors": errors}

def hash_files(file_entries: List[Dict[str, Any]], max_hash_mb: int = 200) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for fe in file_entries:
        p = Path(fe["path"])
        h = sha256_file(p, max_mb=max_hash_mb)
        out.append({
            "path": fe["path"],
            "sha256": h,
            "note": None if h else f"skipped_or_failed (maybe >{max_hash_mb}MB)",
        })
    return out

def yara_scan_files(file_paths: List[str], rules_path: Path) -> Dict[str, Any]:
    if not YARA_AVAILABLE:
        return {"error": "yara-python not installed. pip install yara-python"}
    try:
        rules = yara.compile(filepath=str(rules_path))
    except Exception as e:
        return {"error": f"failed_to_compile_rules: {e}"}
    matches: List[Dict[str, Any]] = []
    errors: List[str] = []
    for fp in file_paths:
        p = Path(fp)
        try:
            ms = rules.match(str(p))
            if ms:
                matches.append({"path": fp, "matches": [m.rule for m in ms]})
        except Exception as e:
            errors.append(f"{fp}: {e}")
    return {"rules": str(rules_path), "matches": matches, "errors": errors}

def extract_iocs_from_connections(net_connections: List[Dict[str, Any]]) -> Dict[str, Any]:
    ips = set()
    for c in net_connections:
        raddr = c.get("raddr")
        if raddr and ":" in raddr:
            ip = raddr.split(":", 1)[0]
            if ip not in {"127.0.0.1", "0.0.0.0", "::1"}:
                ips.add(ip)
    return {"remote_ips": sorted(list(ips))[:500]}

def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    keys = sorted({k for r in rows for k in r.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def compact_processes_for_csv(processes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for p in processes:
        out.append({
            "pid": p.get("pid"),
            "ppid": p.get("ppid"),
            "name": p.get("name"),
            "username": p.get("username"),
            "create_time": p.get("create_time"),
            "exe": p.get("exe"),
            "cmdline": " ".join(p.get("cmdline") or [])[:4000],
        })
    return out

def main() -> int:
    ap = argparse.ArgumentParser(description="PROTOXOL Endpoint Triage (defensive)")
    ap.add_argument("--out", default="triage_out", help="Output directory base")
    ap.add_argument("--paths", nargs="*", default=None, help="Custom scan paths")
    ap.add_argument("--since-days", type=int, default=14)
    ap.add_argument("--max-files", type=int, default=4000)
    ap.add_argument("--max-hash-mb", type=int, default=200)
    ap.add_argument("--yara", default=None, help="Path to YARA rules file")
    ap.add_argument("--vt", action="store_true", help="VirusTotal lookups (VT_API_KEY)")
    ap.add_argument("--otx", action="store_true", help="AlienVault OTX lookups (OTX_API_KEY)")
    ap.add_argument("--no-proc", action="store_true", help="Skip process/network")
    ap.add_argument("--zip", action="store_true", help="Create ZIP archive of outputs")
    args = ap.parse_args()
    host = socket.gethostname()
    base_out = Path(args.out) / f"{host}_{local_now_stamp()}"
    mkdirp(base_out)
    report: Dict[str, Any] = {
        "meta": {
            "tool": "PROTOXOL Endpoint Triage",
            "version": "1.0",
            "collected_local": dt.datetime.now().isoformat(),
            "collected_utc": utc_now_iso(),
            "output_dir": str(base_out),
        }
    }
    report["host"] = collect_host_info()
    if not args.no_proc:
        pn = collect_processes_and_connections()
        report["process_network"] = pn
        write_csv(base_out / "processes.csv", compact_processes_for_csv(pn.get("processes", [])))
        write_csv(base_out / "net_connections.csv", pn.get("net_connections", []))
    else:
        report["process_network"] = {"skipped": True}
    report["persistence"] = collect_persistence()
    scan_paths = [Path(p) for p in args.paths] if args.paths else default_scan_paths()
    report["file_discovery"] = {
        "scan_paths": [str(p) for p in scan_paths],
        "result": discover_files(scan_paths, args.since_days, args.max_files),
    }
    files = report["file_discovery"]["result"]["files"]
    hashes = hash_files(files, max_hash_mb=args.max_hash_mb)
    report["hashes"] = hashes
    write_csv(base_out / "hashes.csv", hashes)
    if args.yara:
        rules_path = Path(args.yara)
        candidate_paths = [f["path"] for f in files][:args.max_files]
        report["yara"] = yara_scan_files(candidate_paths, rules_path)
    else:
        report["yara"] = {"enabled": False}
    if not args.no_proc:
        iocs = extract_iocs_from_connections(report["process_network"].get("net_connections", []))
    else:
        iocs = {"remote_ips": []}
    report["iocs"] = iocs
    rep: Dict[str, Any] = {"enabled": bool(args.vt or args.otx), "vt": None, "otx": None}
    sha_list = [h["sha256"] for h in hashes if h.get("sha256")]
    sha_list = sha_list[:50]
    ip_list = (iocs.get("remote_ips") or [])[:30]
    if args.vt:
        vt_key = os.environ.get("VT_API_KEY", "").strip()
        if not vt_key:
            rep["vt"] = {"error": "VT_API_KEY env var not set"}
        else:
            vt = VirusTotalClient(vt_key)
            vt_out = {"files": [], "ips": []}
            for sha in sha_list:
                vt_out["files"].append(vt.file_report(sha))
            for ip in ip_list:
                vt_out["ips"].append(vt.ip_report(ip))
            rep["vt"] = vt_out
    if args.otx:
        otx_key = os.environ.get("OTX_API_KEY", "").strip()
        if not otx_key:
            rep["otx"] = {"error": "OTX_API_KEY env var not set"}
        else:
            otx = OTXClient(otx_key)
            otx_out = {"files": [], "ips": []}
            for sha in sha_list:
                otx_out["files"].append(otx.file_general(sha))
            for ip in ip_list:
                otx_out["ips"].append(otx.ip_general(ip))
            rep["otx"] = otx_out
    report["reputation"] = rep
    report_path = base_out / "report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[+] Output: {base_out}")
    print(f"[+] Report: {report_path}")
    print(f"[+] Files discovered: {len(files)}")
    print(f"[+] Hashes computed: {sum(1 for h in hashes if h.get('sha256'))}")
    if args.yara:
        matches = report.get("yara", {}).get("matches", [])
        print(f"[+] YARA matches: {len(matches)}")
    if args.vt or args.otx:
        print("[+] Reputation lookups done (bounded caps applied).")
    if args.zip:
        zip_path = shutil.make_archive(str(base_out), "zip", root_dir=str(base_out))
        print(f"[+] ZIP: {zip_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())


