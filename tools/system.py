#!/usr/bin/env python3
"""
System Capability Inspector
WAT Framework — Tool Layer

Collects CPU, RAM, GPU, disk, and Python/ML library information relevant to
deciding whether a machine learning model can be trained and run locally.
Writes a structured report to system_info.txt in the project root.

Usage:
    python3 tools/system.py
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent.parent / "system_info.txt"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run(cmd: list) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""


def _safe_import(module: str):
    try:
        return __import__(module)
    except ImportError:
        return None


# ── CPU ───────────────────────────────────────────────────────────────────────

def get_cpu_info() -> dict:
    info = {
        "model":          platform.processor() or "unknown",
        "architecture":   platform.machine(),
        "physical_cores": None,
        "logical_cores":  None,
    }

    psutil = _safe_import("psutil")
    if psutil:
        info["physical_cores"] = psutil.cpu_count(logical=False)
        info["logical_cores"]  = psutil.cpu_count(logical=True)
    else:
        import multiprocessing
        info["logical_cores"] = multiprocessing.cpu_count()

    # Richer model name on Linux
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    info["model"] = line.split(":")[1].strip()
                    break
    except Exception:
        pass

    return info


# ── RAM ───────────────────────────────────────────────────────────────────────

def get_ram_info() -> dict:
    psutil = _safe_import("psutil")
    if psutil:
        vm = psutil.virtual_memory()
        return {
            "total_gb":     round(vm.total     / 1e9, 2),
            "available_gb": round(vm.available / 1e9, 2),
            "used_gb":      round(vm.used      / 1e9, 2),
            "percent_used": vm.percent,
        }
    # Fallback: /proc/meminfo on Linux
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                mem[k.strip()] = v.strip()
        total = int(mem.get("MemTotal",     "0 kB").split()[0]) * 1024
        avail = int(mem.get("MemAvailable", "0 kB").split()[0]) * 1024
        return {
            "total_gb":     round(total / 1e9, 2),
            "available_gb": round(avail / 1e9, 2),
            "used_gb":      round((total - avail) / 1e9, 2),
            "percent_used": round((total - avail) / total * 100, 1) if total else None,
        }
    except Exception:
        return {"error": "psutil not installed and /proc/meminfo unavailable"}


# ── GPU ───────────────────────────────────────────────────────────────────────

def get_gpu_info() -> list:
    gpus = []

    # NVIDIA via nvidia-smi
    smi = _run([
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.free,driver_version,compute_cap",
        "--format=csv,noheader,nounits",
    ])
    if smi:
        for line in smi.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            gpus.append({
                "vendor":         "NVIDIA",
                "model":          parts[0] if len(parts) > 0 else "unknown",
                "vram_total_mb":  int(parts[1]) if len(parts) > 1 else None,
                "vram_free_mb":   int(parts[2]) if len(parts) > 2 else None,
                "driver":         parts[3] if len(parts) > 3 else None,
                "compute_cap":    parts[4] if len(parts) > 4 else None,
                "cuda_available": None,
            })
        torch = _safe_import("torch")
        if torch:
            for g in gpus:
                g["cuda_available"] = torch.cuda.is_available()

    # AMD via rocm-smi
    if not gpus:
        rocm = _run(["rocm-smi", "--showproductname"])
        if rocm:
            gpus.append({"vendor": "AMD", "raw_rocm_output": rocm[:400]})

    # Apple Silicon MPS
    if not gpus:
        torch = _safe_import("torch")
        if torch and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            gpus.append({
                "vendor":        "Apple",
                "model":         "Metal Performance Shaders (MPS)",
                "cuda_available": False,
                "mps_available":  True,
            })

    if not gpus:
        gpus.append({"vendor": "none", "note": "No GPU detected or driver tools unavailable"})

    return gpus


# ── Disk ──────────────────────────────────────────────────────────────────────

def get_disk_info() -> dict:
    psutil = _safe_import("psutil")
    if psutil:
        d = psutil.disk_usage("/")
        return {
            "total_gb": round(d.total / 1e9, 2),
            "free_gb":  round(d.free  / 1e9, 2),
            "used_gb":  round(d.used  / 1e9, 2),
        }
    try:
        st = os.statvfs("/")
        total = st.f_blocks * st.f_frsize
        free  = st.f_bavail * st.f_frsize
        return {
            "total_gb": round(total / 1e9, 2),
            "free_gb":  round(free  / 1e9, 2),
            "used_gb":  round((total - free) / 1e9, 2),
        }
    except Exception:
        return {"error": "disk info unavailable"}


# ── ML Libraries ──────────────────────────────────────────────────────────────

def get_ml_libraries() -> dict:
    checks = [
        "torch",
        "tensorflow",
        "sklearn",
        "xgboost",
        "lightgbm",
        "catboost",
        "pandas",
        "numpy",
        "google.cloud.bigquery",
        "google.cloud.aiplatform",
    ]
    libs = {}
    for mod in checks:
        m = _safe_import(mod)
        if m:
            # Walk the dotted attribute path to find __version__
            ver_path = mod.split(".") + ["__version__"]
            obj = m
            for part in ver_path[1:]:
                obj = getattr(obj, part, None)
                if obj is None:
                    break
            libs[mod] = str(obj) if obj else "installed (version unknown)"
        else:
            libs[mod] = "not installed"
    return libs


# ── Platform recommendation ───────────────────────────────────────────────────

def recommend_platform(ram: dict, gpus: list, libs: dict) -> dict:
    has_gpu     = gpus[0].get("vendor", "none") != "none"
    vram_mb     = gpus[0].get("vram_total_mb") or 0
    ram_gb      = ram.get("available_gb") or 0
    has_torch   = libs.get("torch",      "not installed") != "not installed"
    has_tf      = libs.get("tensorflow", "not installed") != "not installed"
    has_sklearn = libs.get("sklearn",    "not installed") != "not installed"

    local_capable = (
        (has_gpu and vram_mb >= 4000)
        or (ram_gb >= 8 and (has_torch or has_tf or has_sklearn))
    )

    if local_capable:
        reason = (
            f"GPU available ({vram_mb} MB VRAM)" if has_gpu
            else f"{ram_gb:.1f} GB RAM available with ML libraries present"
        )
        return {
            "recommendation": "local",
            "reason":         reason,
            "note":           "Train and run locally. Save model artifact to tools/models/.",
        }
    return {
        "recommendation": "bigquery_ml",
        "reason":         "Insufficient local GPU/RAM or required ML libraries not installed",
        "note":           "Use BigQuery CREATE MODEL. Escalate to Vertex AI AutoML for complex/large tasks.",
    }


# ── Collect & write ───────────────────────────────────────────────────────────

def collect() -> dict:
    print("Collecting system information...")
    cpu  = get_cpu_info()
    ram  = get_ram_info()
    gpus = get_gpu_info()
    disk = get_disk_info()
    libs = get_ml_libraries()
    rec  = recommend_platform(ram, gpus, libs)

    return {
        "collected_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "os":           f"{platform.system()} {platform.release()} ({platform.version()})",
        "python":       sys.version,
        "cpu":          cpu,
        "ram":          ram,
        "gpu":          gpus,
        "disk":         disk,
        "ml_libraries": libs,
        "platform_recommendation": rec,
    }


def write_report(info: dict):
    rec  = info["platform_recommendation"]
    ram  = info["ram"]
    cpu  = info["cpu"]
    disk = info["disk"]

    lines = [
        "# System Information — Angel AI",
        f"# Generated       : {info['collected_at']}",
        f"# RECOMMENDATION  : {rec['recommendation'].upper()}",
        f"# Reason          : {rec['reason']}",
        "",
        "## OS & Python",
        f"OS      : {info['os']}",
        f"Python  : {info['python'].splitlines()[0]}",
        "",
        "## CPU",
        f"Model           : {cpu.get('model')}",
        f"Architecture    : {cpu.get('architecture')}",
        f"Physical cores  : {cpu.get('physical_cores')}",
        f"Logical cores   : {cpu.get('logical_cores')}",
        "",
        "## RAM",
    ]
    for k, v in ram.items():
        lines.append(f"{k:<20}: {v}")

    lines += ["", "## GPU(s)"]
    for i, g in enumerate(info["gpu"]):
        lines.append(f"GPU {i}: " + json.dumps(g))

    lines += ["", "## Disk (/)"]
    for k, v in disk.items():
        lines.append(f"{k:<20}: {v}")

    lines += ["", "## ML Libraries"]
    for lib, ver in info["ml_libraries"].items():
        lines.append(f"{lib:<35}: {ver}")

    lines += [
        "",
        "## Platform Recommendation",
        f"Recommendation  : {rec['recommendation'].upper()}",
        f"Reason          : {rec['reason']}",
        f"Note            : {rec['note']}",
        "",
    ]

    OUTPUT_PATH.write_text("\n".join(lines))
    print(f"Report written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    info = collect()
    write_report(info)
    rec = info["platform_recommendation"]
    print(f"\nRecommendation : {rec['recommendation'].upper()}")
    print(f"Reason         : {rec['reason']}")
    print(f"Note           : {rec['note']}")
