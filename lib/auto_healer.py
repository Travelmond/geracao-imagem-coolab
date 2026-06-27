"""
auto_healer.py — EnvironmentDoctor: Diagnóstico e Cura Automática
==================================================================

Sistema de "vacinas" que verifica, corrige e valida cada dependência
do ambiente Python no Google Colab antes de iniciar o Forge.

Cada vacina implementa 4 etapas:
    check()    → Verifica se a dependência está saudável.
    fix()      → Tenta corrigir automaticamente.
    verify()   → Confirma que a correção funcionou.
    fallback() → Estratégia alternativa de último recurso.

O EnvironmentDoctor orquestra todas as vacinas e gera um HealReport
detalhado com emojis para o terminal e HTML para o Gradio.

Autor: Fabiano
Última atualização: 2026-06-27
"""

from __future__ import annotations

import importlib
import logging
import os
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

# ══════════════════════════════════════════════════════════════
# Importar version_pins com fallback robusto
# ══════════════════════════════════════════════════════════════
_LIB_DIR = Path(__file__).resolve().parent

try:
    from lib import version_pins as vp  # type: ignore[import]
except ImportError:
    try:
        # Fallback: importar diretamente quando executado como script
        sys.path.insert(0, str(_LIB_DIR))
        import version_pins as vp  # type: ignore[import, no-redef]
    except ImportError:
        # Último recurso: se o arquivo existir, importar manualmente
        _vp_path = _LIB_DIR / "version_pins.py"
        if _vp_path.exists():
            import importlib.util

            _spec = importlib.util.spec_from_file_location("version_pins", _vp_path)
            vp = importlib.util.module_from_spec(_spec)  # type: ignore[assignment]
            _spec.loader.exec_module(vp)  # type: ignore[union-attr]
        else:
            raise FileNotFoundError(
                f"Não foi possível encontrar version_pins.py em {_vp_path}"
            )

# ══════════════════════════════════════════════════════════════
# Logging
# ══════════════════════════════════════════════════════════════
logger = logging.getLogger("EnvironmentDoctor")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(_handler)


# ══════════════════════════════════════════════════════════════
# Utilitários
# ══════════════════════════════════════════════════════════════

def is_colab() -> bool:
    """Detect if running inside Google Colab."""
    try:
        import google.colab  # type: ignore[import]  # noqa: F401
        return True
    except ImportError:
        return False


def _run_cmd(
    cmd: str,
    timeout: int = 120,
    shell: bool = True,
    env: Optional[dict[str, str]] = None,
) -> tuple[bool, str, str]:
    """
    Run a shell command with timeout.

    Returns:
        (success: bool, stdout: str, stderr: str)
    """
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    logger.debug("Executando comando: %s", cmd)
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=merged_env,
        )
        success = result.returncode == 0
        if not success:
            logger.debug(
                "Comando falhou (rc=%d): stderr=%s",
                result.returncode,
                result.stderr[:500],
            )
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.warning("Comando excedeu timeout de %ds: %s", timeout, cmd)
        return False, "", f"Timeout após {timeout}s"
    except Exception as exc:
        logger.error("Erro ao executar comando: %s — %s", cmd, exc)
        return False, "", str(exc)


# ══════════════════════════════════════════════════════════════
# Data Classes
# ══════════════════════════════════════════════════════════════

class VaccineStatus(str, Enum):
    """Possible outcomes of a vaccine application."""

    HEALTHY = "healthy"
    FIXED = "fixed"
    WARNING = "warning"
    FAILED = "failed"


@dataclass
class VaccineResult:
    """Result of applying a single vaccine."""

    vaccine_name: str
    status: VaccineStatus
    message: str
    details: str = ""
    duration_seconds: float = 0.0

    @property
    def emoji(self) -> str:
        """Return an emoji representing the status."""
        return {
            VaccineStatus.HEALTHY: "✅",
            VaccineStatus.FIXED: "🔧",
            VaccineStatus.WARNING: "⚠️",
            VaccineStatus.FAILED: "❌",
        }.get(self.status, "❓")


@dataclass
class HealReport:
    """Collector of VaccineResult objects with reporting capabilities."""

    results: list[VaccineResult] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0

    # ── Properties ──────────────────────────────────────────

    @property
    def all_healthy(self) -> bool:
        """True if there are no failures and no warnings."""
        return all(
            r.status in (VaccineStatus.HEALTHY, VaccineStatus.FIXED)
            for r in self.results
        )

    @property
    def critical_failures(self) -> list[VaccineResult]:
        """Return list of results with FAILED status."""
        return [r for r in self.results if r.status == VaccineStatus.FAILED]

    @property
    def warnings(self) -> list[VaccineResult]:
        """Return list of results with WARNING status."""
        return [r for r in self.results if r.status == VaccineStatus.WARNING]

    @property
    def fixed_count(self) -> int:
        """Count of vaccines that were fixed."""
        return sum(1 for r in self.results if r.status == VaccineStatus.FIXED)

    @property
    def progress(self) -> float:
        """Progress as percentage (0-100) based on non-failed results."""
        if not self.results:
            return 0.0
        non_failed = sum(
            1
            for r in self.results
            if r.status != VaccineStatus.FAILED
        )
        return (non_failed / len(self.results)) * 100.0

    @property
    def total_duration(self) -> float:
        """Total elapsed time for the healing process."""
        if self.end_time > 0:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    # ── Methods ─────────────────────────────────────────────

    def add(self, result: VaccineResult) -> None:
        """Add a VaccineResult to the report."""
        self.results.append(result)

    def finalize(self) -> None:
        """Mark the report as complete."""
        self.end_time = time.time()

    def to_text(self) -> str:
        """
        Generate a human-readable text report with emojis.

        Suitable for terminal/notebook output.
        """
        lines: list[str] = []
        lines.append("")
        lines.append("╔══════════════════════════════════════════════════╗")
        lines.append("║       🏥 Relatório do EnvironmentDoctor 🏥       ║")
        lines.append("╚══════════════════════════════════════════════════╝")
        lines.append("")

        for r in self.results:
            status_label = r.status.value.upper()
            lines.append(f"  {r.emoji} {r.vaccine_name:<30s} [{status_label}]")
            lines.append(f"     └─ {r.message}")
            if r.details:
                for detail_line in r.details.strip().split("\n"):
                    lines.append(f"        {detail_line}")
            lines.append(f"        ⏱ {r.duration_seconds:.1f}s")
            lines.append("")

        # Summary
        lines.append("─" * 52)
        total = len(self.results)
        healthy = sum(1 for r in self.results if r.status == VaccineStatus.HEALTHY)
        fixed = self.fixed_count
        warns = len(self.warnings)
        fails = len(self.critical_failures)

        lines.append(f"  📊 Total: {total} vacinas")
        lines.append(f"  ✅ Saudáveis: {healthy}")
        lines.append(f"  🔧 Corrigidas: {fixed}")
        lines.append(f"  ⚠️  Avisos: {warns}")
        lines.append(f"  ❌ Falhas críticas: {fails}")
        lines.append(f"  ⏱  Tempo total: {self.total_duration:.1f}s")
        lines.append(f"  📈 Progresso: {self.progress:.0f}%")
        lines.append("")

        if self.all_healthy:
            lines.append("  🎉 Ambiente 100% saudável! Pronto para usar.")
        elif fails > 0:
            lines.append(
                f"  🚨 {fails} falha(s) crítica(s) detectada(s). "
                "Verifique os detalhes acima."
            )
        else:
            lines.append("  ⚡ Ambiente funcional com avisos.")

        lines.append("")
        return "\n".join(lines)

    def to_html(self) -> str:
        """
        Generate an HTML report suitable for Gradio display.

        Returns styled HTML with status indicators.
        """
        status_colors = {
            VaccineStatus.HEALTHY: "#2ecc71",
            VaccineStatus.FIXED: "#3498db",
            VaccineStatus.WARNING: "#f39c12",
            VaccineStatus.FAILED: "#e74c3c",
        }

        rows = []
        for r in self.results:
            color = status_colors.get(r.status, "#95a5a6")
            badge = (
                f'<span style="background:{color};color:#fff;'
                f'padding:2px 8px;border-radius:4px;font-size:0.85em;">'
                f"{r.status.value.upper()}</span>"
            )
            detail_html = ""
            if r.details:
                escaped = (
                    r.details.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                detail_html = (
                    f'<br><small style="color:#888;">{escaped}</small>'
                )

            rows.append(
                f"<tr>"
                f'<td style="padding:6px 10px;">{r.emoji}</td>'
                f'<td style="padding:6px 10px;font-weight:600;">'
                f"{r.vaccine_name}</td>"
                f'<td style="padding:6px 10px;">{badge}</td>'
                f'<td style="padding:6px 10px;">{r.message}{detail_html}</td>'
                f'<td style="padding:6px 10px;text-align:right;">'
                f"{r.duration_seconds:.1f}s</td>"
                f"</tr>"
            )

        table_rows = "\n".join(rows)

        summary_color = "#2ecc71" if self.all_healthy else (
            "#e74c3c" if self.critical_failures else "#f39c12"
        )
        summary_text = (
            "🎉 Ambiente saudável!"
            if self.all_healthy
            else (
                f"🚨 {len(self.critical_failures)} falha(s) crítica(s)"
                if self.critical_failures
                else "⚡ Funcional com avisos"
            )
        )

        html = f"""
        <div style="font-family:'Segoe UI',system-ui,sans-serif;max-width:800px;">
          <h3 style="margin-bottom:4px;">🏥 Relatório do EnvironmentDoctor</h3>
          <p style="color:{summary_color};font-weight:600;font-size:1.1em;">
            {summary_text}
          </p>
          <table style="width:100%;border-collapse:collapse;margin-top:10px;">
            <thead>
              <tr style="background:#f8f9fa;border-bottom:2px solid #dee2e6;">
                <th style="padding:8px 10px;text-align:left;width:30px;"></th>
                <th style="padding:8px 10px;text-align:left;">Vacina</th>
                <th style="padding:8px 10px;text-align:left;">Status</th>
                <th style="padding:8px 10px;text-align:left;">Mensagem</th>
                <th style="padding:8px 10px;text-align:right;">Tempo</th>
              </tr>
            </thead>
            <tbody>
              {table_rows}
            </tbody>
          </table>
          <p style="margin-top:12px;color:#888;font-size:0.85em;">
            Progresso: {self.progress:.0f}% &nbsp;|&nbsp;
            Corrigidas: {self.fixed_count} &nbsp;|&nbsp;
            Tempo total: {self.total_duration:.1f}s
          </p>
        </div>
        """
        return html

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report to a dictionary."""
        return {
            "results": [
                {
                    "vaccine_name": r.vaccine_name,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details,
                    "duration_seconds": r.duration_seconds,
                }
                for r in self.results
            ],
            "summary": {
                "all_healthy": self.all_healthy,
                "critical_failures": len(self.critical_failures),
                "warnings": len(self.warnings),
                "fixed_count": self.fixed_count,
                "progress": self.progress,
                "total_duration": self.total_duration,
            },
        }


# ══════════════════════════════════════════════════════════════
# Abstract Base: Vaccine
# ══════════════════════════════════════════════════════════════

class Vaccine(ABC):
    """
    Abstract base class for all environment vaccines.

    Each vaccine follows a 4-step protocol:
        1. check()    — Is the dependency healthy?
        2. fix()      — Attempt to repair it.
        3. verify()   — Did the fix work?
        4. fallback() — Last-resort alternative strategy.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the vaccine."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of what this vaccine checks/fixes."""

    @abstractmethod
    def check(self) -> bool:
        """Return True if the dependency is healthy."""

    @abstractmethod
    def fix(self) -> bool:
        """Attempt to fix the dependency. Return True on success."""

    @abstractmethod
    def verify(self) -> bool:
        """Verify the fix was successful. Return True if healthy."""

    @abstractmethod
    def fallback(self) -> bool:
        """Last-resort fix. Return True on success."""

    @abstractmethod
    def describe_problem(self) -> str:
        """Describe the detected problem in Portuguese."""

    def _invalidate_import_cache(self, module_name: str) -> None:
        """Remove a module from sys.modules to force re-import."""
        keys_to_remove = [
            k for k in sys.modules if k == module_name or k.startswith(f"{module_name}.")
        ]
        for key in keys_to_remove:
            del sys.modules[key]
        importlib.invalidate_caches()


# ══════════════════════════════════════════════════════════════
# Vaccine 1: PythonVersionVaccine
# ══════════════════════════════════════════════════════════════

class PythonVersionVaccine(Vaccine):
    """Ensure Python 3.10 is available for Forge."""

    @property
    def name(self) -> str:
        return "Python 3.10"

    @property
    def description(self) -> str:
        return "Verificar instalação do Python 3.10 para o Forge"

    def check(self) -> bool:
        """Check if python3.10 binary exists and runs."""
        # Check basic execution
        ok, stdout, _ = _run_cmd(f"{vp.PYTHON_CMD} --version", timeout=15)
        if not (ok and vp.PYTHON_TARGET in stdout):
            return False
            
        # Check distutils
        ok_distutils, _, _ = _run_cmd(f"{vp.PYTHON_CMD} -c 'import distutils.core'", timeout=15)
        if not ok_distutils:
            logger.info("distutils ausente para Python %s", vp.PYTHON_TARGET)
            return False
            
        # Check dev headers (Python.h)
        ok_dev, _, _ = _run_cmd(f"test -f /usr/include/python{vp.PYTHON_TARGET}/Python.h", timeout=15)
        if not ok_dev:
            logger.info("python%s-dev headers ausentes", vp.PYTHON_TARGET)
            return False
            
        logger.info("Python %s completo (com dev e distutils) encontrado.", vp.PYTHON_TARGET)
        return True

    def fix(self) -> bool:
        """Install Python 3.10 via apt."""
        logger.info("Instalando Python %s via apt...", vp.PYTHON_TARGET)
        ok, _, stderr = _run_cmd(
            f"apt-get update -qq && apt-get install -y -qq "
            f"python{vp.PYTHON_TARGET} python{vp.PYTHON_TARGET}-venv "
            f"python{vp.PYTHON_TARGET}-dev python{vp.PYTHON_TARGET}-distutils",
            timeout=180,
        )
        if not ok:
            logger.warning("apt install falhou: %s", stderr[:300])
        return ok

    def verify(self) -> bool:
        """Verify Python 3.10 is now available."""
        return self.check()

    def fallback(self) -> bool:
        """Add deadsnakes PPA and retry."""
        logger.info("Tentando PPA deadsnakes como fallback...")
        _run_cmd(
            "apt-get install -y -qq software-properties-common && "
            "add-apt-repository -y ppa:deadsnakes/ppa && "
            "apt-get update -qq",
            timeout=120,
        )
        return self.fix()

    def describe_problem(self) -> str:
        return (
            f"Python {vp.PYTHON_TARGET} não encontrado. "
            f"O Forge requer esta versão específica."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 2: PIPVaccine
# ══════════════════════════════════════════════════════════════

class PIPVaccine(Vaccine):
    """Ensure pip is available for the target Python."""

    @property
    def name(self) -> str:
        return "PIP"

    @property
    def description(self) -> str:
        return "Verificar se pip está instalado para Python 3.10"

    def check(self) -> bool:
        """Check if pip works for the target Python."""
        ok, _, _ = _run_cmd(f"{vp.PYTHON_CMD} -m pip --version", timeout=15)
        return ok

    def fix(self) -> bool:
        """Install pip using get-pip.py, and then setuptools and wheel."""
        logger.info("Instalando pip via get-pip.py...")
        ok, _, stderr = _run_cmd(
            f"curl -sS https://bootstrap.pypa.io/get-pip.py | {vp.PYTHON_CMD} && "
            f"{vp.PYTHON_CMD} -m pip install setuptools wheel --quiet",
            timeout=120,
        )
        if not ok:
            logger.warning("get-pip.py falhou: %s", stderr[:300])
        return ok

    def verify(self) -> bool:
        """Verify pip is now working."""
        return self.check()

    def fallback(self) -> bool:
        """Try ensurepip as fallback."""
        logger.info("Tentando ensurepip como fallback...")
        ok, _, _ = _run_cmd(f"{vp.PYTHON_CMD} -m ensurepip --upgrade", timeout=60)
        return ok

    def describe_problem(self) -> str:
        return f"pip não disponível para {vp.PYTHON_CMD}."


# ══════════════════════════════════════════════════════════════
# Vaccine 3: PIPConstraintVaccine
# ══════════════════════════════════════════════════════════════

class PIPConstraintVaccine(Vaccine):
    """Ensure PIP_CONSTRAINT environment variable is set and the file exists."""

    _constraint_path: str = ""

    @property
    def name(self) -> str:
        return "PIP Constraint"

    @property
    def description(self) -> str:
        return "Configurar blindagem global de versões via PIP_CONSTRAINT"

    def check(self) -> bool:
        """Check if PIP_CONSTRAINT env var is set and file exists."""
        path = os.environ.get("PIP_CONSTRAINT", "")
        if path and os.path.isfile(path):
            logger.info("PIP_CONSTRAINT ativo: %s", path)
            self._constraint_path = path
            return True
        return False

    def _write_constraint_file(self, base_path: str) -> str:
        """Write the constraint file and return its path."""
        constraint_path = os.path.join(base_path, "pip_constraints_sd.txt")
        os.makedirs(base_path, exist_ok=True)
        with open(constraint_path, "w") as f:
            f.write(vp.PIP_CONSTRAINT_CONTENT)
        logger.info("Arquivo de constraint escrito em: %s", constraint_path)
        return constraint_path

    def fix(self) -> bool:
        """Write constraint file to /content and set env var."""
        try:
            base = "/content" if is_colab() else "/tmp"
            self._constraint_path = self._write_constraint_file(base)
            os.environ["PIP_CONSTRAINT"] = self._constraint_path
            logger.info("PIP_CONSTRAINT definido: %s", self._constraint_path)
            return True
        except Exception as exc:
            logger.error("Falha ao criar arquivo de constraint: %s", exc)
            return False

    def verify(self) -> bool:
        """Verify the constraint file exists and env var is set."""
        return self.check()

    def fallback(self) -> bool:
        """Write to /tmp as fallback location."""
        try:
            self._constraint_path = self._write_constraint_file("/tmp")
            os.environ["PIP_CONSTRAINT"] = self._constraint_path
            logger.info(
                "Fallback: PIP_CONSTRAINT definido em /tmp: %s",
                self._constraint_path,
            )
            return True
        except Exception as exc:
            logger.error("Fallback de constraint falhou: %s", exc)
            return False

    def describe_problem(self) -> str:
        return (
            "PIP_CONSTRAINT não configurado. Sem a blindagem, "
            "pip install pode atualizar numpy/scipy para versões incompatíveis."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 4: NumPyVaccine
# ══════════════════════════════════════════════════════════════

class NumPyVaccine(Vaccine):
    """Ensure NumPy is installed with a compatible version (<2.1)."""

    @property
    def name(self) -> str:
        return "NumPy"

    @property
    def description(self) -> str:
        return f"Verificar NumPy com versão {vp.NUMPY_PIN}"

    def _get_numpy_version(self) -> Optional[str]:
        """Get the installed numpy version, or None."""
        try:
            self._invalidate_import_cache("numpy")
            import numpy  # noqa: F811
            return numpy.__version__
        except ImportError:
            return None

    def _version_ok(self, version: str) -> bool:
        """Check if version satisfies <2.1.0."""
        try:
            parts = [int(x) for x in version.split(".")[:2]]
            major, minor = parts[0], parts[1]
            # Must be < 2.1
            return major < 2 or (major == 2 and minor < 1)
        except (ValueError, IndexError):
            return False

    def check(self) -> bool:
        """Check numpy is importable and version is compatible."""
        ver = self._get_numpy_version()
        if ver is None:
            logger.warning("NumPy não está instalado.")
            return False
        if self._version_ok(ver):
            logger.info("NumPy %s — compatível.", ver)
            return True
        logger.warning("NumPy %s — INCOMPATÍVEL (requer %s).", ver, vp.NUMPY_PIN)
        return False

    def fix(self) -> bool:
        """Force install numpy with version constraint."""
        logger.info("Instalando NumPy %s...", vp.NUMPY_PIN)
        ok, _, stderr = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install --force-reinstall "
            f"'numpy{vp.NUMPY_PIN}' --quiet",
            timeout=120,
        )
        if not ok:
            logger.warning("Instalação do NumPy falhou: %s", stderr[:300])
        return ok

    def verify(self) -> bool:
        """Verify numpy is now at a compatible version."""
        self._invalidate_import_cache("numpy")
        return self.check()

    def fallback(self) -> bool:
        """Pin to exact known-good version as fallback."""
        logger.info("Fallback: instalando NumPy==1.26.4...")
        ok, _, _ = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install numpy==1.26.4 "
            f"--force-reinstall --quiet",
            timeout=120,
        )
        return ok

    def describe_problem(self) -> str:
        ver = self._get_numpy_version() or "não instalado"
        return (
            f"NumPy {ver} — incompatível. Requer {vp.NUMPY_PIN}. "
            "Versões ≥2.1 quebram scikit-image, scipy e insightface."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 5: ScikitImageVaccine
# ══════════════════════════════════════════════════════════════

class ScikitImageVaccine(Vaccine):
    """Ensure scikit-image is importable."""

    @property
    def name(self) -> str:
        return "scikit-image"

    @property
    def description(self) -> str:
        return "Verificar se scikit-image importa corretamente"

    def check(self) -> bool:
        """Check if skimage can be imported."""
        try:
            self._invalidate_import_cache("skimage")
            import skimage  # type: ignore[import]  # noqa: F401, F811
            logger.info("scikit-image %s — OK.", getattr(skimage, "__version__", "?"))
            return True
        except ImportError:
            return False
        except Exception as exc:
            logger.warning("scikit-image import error: %s", exc)
            return False

    def fix(self) -> bool:
        """Install scikit-image with version pin."""
        logger.info("Instalando scikit-image %s...", vp.SCIKIT_IMAGE_PIN)
        ok, _, stderr = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install "
            f"'scikit-image{vp.SCIKIT_IMAGE_PIN}' --quiet",
            timeout=120,
        )
        if not ok:
            logger.warning("Instalação do scikit-image falhou: %s", stderr[:300])
        return ok

    def verify(self) -> bool:
        """Verify scikit-image imports."""
        self._invalidate_import_cache("skimage")
        return self.check()

    def fallback(self) -> bool:
        """Reinstall the trio: numpy, scipy, scikit-image."""
        logger.info("Fallback: reinstalando trio numpy+scipy+scikit-image...")
        ok, _, _ = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install --force-reinstall "
            f"'numpy{vp.NUMPY_PIN}' 'scipy{vp.SCIPY_PIN}' "
            f"'scikit-image{vp.SCIKIT_IMAGE_PIN}' --quiet",
            timeout=180,
        )
        return ok

    def describe_problem(self) -> str:
        return (
            "scikit-image não pode ser importado. Geralmente causado por "
            "incompatibilidade de ABI com NumPy."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 6: CLIPVaccine
# ══════════════════════════════════════════════════════════════

class CLIPVaccine(Vaccine):
    """Ensure OpenAI CLIP is installed and importable."""

    @property
    def name(self) -> str:
        return "CLIP (OpenAI)"

    @property
    def description(self) -> str:
        return "Verificar instalação do CLIP para embeddings"

    def check(self) -> bool:
        """Check if clip can be imported."""
        try:
            self._invalidate_import_cache("clip")
            import clip  # type: ignore[import]  # noqa: F401, F811
            logger.info("CLIP importado com sucesso.")
            return True
        except ImportError:
            return False
        except Exception as exc:
            logger.warning("CLIP import error: %s", exc)
            return False

    def fix(self) -> bool:
        """Install CLIP from GitHub."""
        logger.info("Instalando CLIP do GitHub (commit fixo)...")
        # Install dependencies first
        deps = " ".join(vp.CLIP_DEPS)
        _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install {deps} --quiet",
            timeout=60,
        )
        ok, _, stderr = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install "
            f"'{vp.CLIP_GITHUB_URL}' --quiet --no-deps",
            timeout=180,
        )
        if not ok:
            logger.warning("Instalação do CLIP falhou: %s", stderr[:300])
        return ok

    def verify(self) -> bool:
        """Verify CLIP imports correctly."""
        self._invalidate_import_cache("clip")
        return self.check()

    def fallback(self) -> bool:
        """Pin setuptools<70 first, then retry CLIP install."""
        logger.info(
            "Fallback: instalando setuptools%s e retentando CLIP...",
            vp.SETUPTOOLS_PIN,
        )
        _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install "
            f"'setuptools{vp.SETUPTOOLS_PIN}' --quiet",
            timeout=60,
        )
        # Retry with build isolation disabled
        deps = " ".join(vp.CLIP_DEPS)
        _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install {deps} --quiet",
            timeout=60,
        )
        ok, _, _ = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install "
            f"'{vp.CLIP_GITHUB_URL}' --no-build-isolation --quiet",
            timeout=180,
        )
        return ok

    def describe_problem(self) -> str:
        return (
            "CLIP (OpenAI) não instalado. Necessário para embeddings de texto/imagem. "
            "Frequentemente falha se setuptools ≥70 está presente."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 7: TorchCUDAVaccine
# ══════════════════════════════════════════════════════════════

class TorchCUDAVaccine(Vaccine):
    """Check if PyTorch is importable and GPU is available."""

    @property
    def name(self) -> str:
        return "PyTorch / CUDA"

    @property
    def description(self) -> str:
        return "Verificar PyTorch e disponibilidade de GPU"

    def check(self) -> bool:
        """
        Check if torch imports. GPU availability is a WARNING, not a failure.

        Returns True if torch imports successfully (even without GPU).
        """
        try:
            self._invalidate_import_cache("torch")
            import torch  # noqa: F811

            logger.info("PyTorch %s — importado.", torch.__version__)
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                logger.info("GPU disponível: %s", gpu_name)
            else:
                logger.warning(
                    "CUDA não disponível — execução em CPU (lento)."
                )
            return True
        except ImportError:
            return False
        except Exception as exc:
            logger.error("Erro ao importar torch: %s", exc)
            return False

    def fix(self) -> bool:
        """
        No auto-fix for PyTorch — Colab provides it.

        Attempting to install torch ourselves would likely break CUDA.
        Return True to skip (not our responsibility).
        """
        logger.info(
            "PyTorch é fornecido pelo Colab. Não será reinstalado automaticamente."
        )
        return True

    def verify(self) -> bool:
        """Verify torch imports."""
        return self.check()

    def fallback(self) -> bool:
        """No fallback — PyTorch must come from Colab."""
        logger.warning(
            "Sem fallback para PyTorch. Ele deve ser pré-instalado pelo Colab."
        )
        return False

    def describe_problem(self) -> str:
        try:
            import torch

            if not torch.cuda.is_available():
                return (
                    "PyTorch está instalado mas CUDA não está disponível. "
                    "O Forge rodará em modo CPU (muito lento). "
                    "Selecione um runtime com GPU no Colab."
                )
            return "Problema desconhecido com PyTorch."
        except ImportError:
            return (
                "PyTorch não está instalado. Isso é incomum no Colab. "
                "Reinicie o runtime."
            )


# ══════════════════════════════════════════════════════════════
# Vaccine 8: BitsandbytesVaccine
# ══════════════════════════════════════════════════════════════

class BitsandbytesVaccine(Vaccine):
    """Ensure bitsandbytes is installed for quantization."""

    @property
    def name(self) -> str:
        return "bitsandbytes"

    @property
    def description(self) -> str:
        return "Verificar bitsandbytes para quantização de modelos"

    def check(self) -> bool:
        """Check if bitsandbytes can be imported."""
        try:
            self._invalidate_import_cache("bitsandbytes")
            import bitsandbytes  # type: ignore[import]  # noqa: F401, F811
            logger.info(
                "bitsandbytes %s — OK.",
                getattr(bitsandbytes, "__version__", "?"),
            )
            return True
        except ImportError:
            return False
        except Exception as exc:
            logger.warning("bitsandbytes import error: %s", exc)
            return False

    def fix(self) -> bool:
        """Install pinned version of bitsandbytes."""
        logger.info("Instalando bitsandbytes%s...", vp.BITSANDBYTES_PIN)
        ok, _, stderr = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install "
            f"'bitsandbytes{vp.BITSANDBYTES_PIN}' --quiet",
            timeout=120,
        )
        if not ok:
            logger.warning("Instalação do bitsandbytes falhou: %s", stderr[:300])
        return ok

    def verify(self) -> bool:
        """Verify bitsandbytes imports."""
        self._invalidate_import_cache("bitsandbytes")
        return self.check()

    def fallback(self) -> bool:
        """Install latest version as fallback."""
        logger.info("Fallback: instalando bitsandbytes (última versão)...")
        ok, _, _ = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install bitsandbytes --quiet",
            timeout=120,
        )
        return ok

    def describe_problem(self) -> str:
        return (
            "bitsandbytes não instalado. Necessário para quantização 4/8-bit. "
            "Modelos grandes podem não carregar sem ele."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 9: OnnxruntimeVaccine
# ══════════════════════════════════════════════════════════════

class OnnxruntimeVaccine(Vaccine):
    """Ensure onnxruntime (GPU preferred) is installed for ReActor."""

    @property
    def name(self) -> str:
        return "ONNX Runtime"

    @property
    def description(self) -> str:
        return "Verificar onnxruntime para ReActor face swap"

    def _detect_cuda_major(self) -> Optional[int]:
        """Detect the CUDA major version from nvcc or torch."""
        ok, stdout, _ = _run_cmd("nvcc --version 2>/dev/null", timeout=10)
        if ok and "release" in stdout:
            # Parse "release 12.2" pattern
            for token in stdout.split():
                if "." in token:
                    try:
                        major = int(token.split(".")[0])
                        if major in (11, 12):
                            return major
                    except ValueError:
                        continue

        # Fallback: check torch.version.cuda
        try:
            import torch  # noqa: F811

            cuda_ver = getattr(torch.version, "cuda", None)
            if cuda_ver:
                return int(cuda_ver.split(".")[0])
        except (ImportError, ValueError, AttributeError):
            pass

        return None

    def check(self) -> bool:
        """Check if onnxruntime is importable."""
        try:
            self._invalidate_import_cache("onnxruntime")
            import onnxruntime as ort  # type: ignore[import]  # noqa: F811

            logger.info("onnxruntime %s — OK.", ort.__version__)
            providers = ort.get_available_providers()
            logger.info("Providers disponíveis: %s", providers)
            return True
        except ImportError:
            return False
        except Exception as exc:
            logger.warning("onnxruntime import error: %s", exc)
            return False

    def fix(self) -> bool:
        """Install onnxruntime-gpu with the correct CUDA index URL."""
        cuda_major = self._detect_cuda_major()
        if cuda_major == 12:
            index_url = vp.ONNXRUNTIME_CUDA12_INDEX
        elif cuda_major == 11:
            index_url = vp.ONNXRUNTIME_CUDA11_INDEX
        else:
            logger.warning(
                "CUDA não detectado (major=%s). Tentando instalação padrão.",
                cuda_major,
            )
            index_url = vp.ONNXRUNTIME_CUDA12_INDEX  # Default to 12

        logger.info(
            "Instalando onnxruntime-gpu%s (CUDA %s)...",
            vp.ONNXRUNTIME_GPU_PIN,
            cuda_major or "?",
        )
        ok, _, stderr = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install "
            f"'onnxruntime-gpu{vp.ONNXRUNTIME_GPU_PIN}' "
            f"--extra-index-url {index_url} --quiet",
            timeout=180,
        )
        if not ok:
            logger.warning("Instalação do onnxruntime-gpu falhou: %s", stderr[:300])
        return ok

    def verify(self) -> bool:
        """Verify onnxruntime imports."""
        self._invalidate_import_cache("onnxruntime")
        return self.check()

    def fallback(self) -> bool:
        """Install CPU-only onnxruntime as fallback."""
        logger.info("Fallback: instalando onnxruntime (CPU)...")
        # Uninstall GPU version if partially installed
        _run_cmd(
            f"{vp.PYTHON_CMD} -m pip uninstall onnxruntime-gpu -y --quiet",
            timeout=30,
        )
        ok, _, _ = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install onnxruntime --quiet",
            timeout=120,
        )
        return ok

    def describe_problem(self) -> str:
        return (
            "ONNX Runtime não instalado. Necessário para o ReActor (face swap). "
            "Sem ele, face swap não funcionará."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 10: InsightfaceVaccine
# ══════════════════════════════════════════════════════════════

class InsightfaceVaccine(Vaccine):
    """Ensure insightface is installed for face analysis."""

    @property
    def name(self) -> str:
        return "InsightFace"

    @property
    def description(self) -> str:
        return "Verificar insightface para análise facial (ReActor)"

    def check(self) -> bool:
        """Check if insightface can be imported."""
        try:
            self._invalidate_import_cache("insightface")
            import insightface  # type: ignore[import]  # noqa: F401, F811
            logger.info(
                "insightface %s — OK.",
                getattr(insightface, "__version__", "?"),
            )
            return True
        except ImportError:
            return False
        except Exception as exc:
            logger.warning("insightface import error: %s", exc)
            return False

    def fix(self) -> bool:
        """Install pinned version of insightface."""
        logger.info("Instalando insightface%s...", vp.INSIGHTFACE_PIN)
        ok, _, stderr = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install "
            f"'insightface{vp.INSIGHTFACE_PIN}' "
            f"'onnx{vp.ONNX_PIN}' "
            f"'albumentations{vp.ALBUMENTATIONS_PIN}' --quiet",
            timeout=180,
        )
        if not ok:
            logger.warning("Instalação do insightface falhou: %s", stderr[:300])
        return ok

    def verify(self) -> bool:
        """Verify insightface imports."""
        self._invalidate_import_cache("insightface")
        return self.check()

    def fallback(self) -> bool:
        """Try a newer version of insightface as fallback."""
        logger.info("Fallback: tentando insightface==1.0.1...")
        # First ensure numpy is compatible
        _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install 'numpy{vp.NUMPY_PIN}' --quiet",
            timeout=60,
        )
        ok, _, _ = _run_cmd(
            f"{vp.PYTHON_CMD} -m pip install insightface==1.0.1 "
            f"'onnx{vp.ONNX_PIN}' --quiet",
            timeout=180,
        )
        return ok

    def describe_problem(self) -> str:
        return (
            "insightface não instalado. Necessário para detecção e análise "
            "de rostos no ReActor. Frequentemente falha por incompatibilidade "
            "de ABI com NumPy."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 11: LibstdcppVaccine
# ══════════════════════════════════════════════════════════════

class LibstdcppVaccine(Vaccine):
    """Ensure libstdc++ is compatible with torch and other C++ extensions."""

    @property
    def name(self) -> str:
        return "libstdc++ (ABI)"

    @property
    def description(self) -> str:
        return "Verificar compatibilidade do libstdc++ com extensões C++"

    def check(self) -> bool:
        """
        Check if torch.tensor creation works (catches GLIBCXX issues).

        A simple tensor operation exercises the C++ runtime.
        """
        try:
            import torch  # noqa: F811

            t = torch.tensor([1.0, 2.0, 3.0])
            result = t.sum().item()
            if result == 6.0:
                logger.info("libstdc++ — operações de tensor OK.")
                return True
            logger.warning("Resultado inesperado do tensor test: %s", result)
            return False
        except ImportError:
            logger.info(
                "PyTorch não instalado — pulando verificação de libstdc++."
            )
            return True  # Can't check without torch
        except Exception as exc:
            logger.error("Falha no teste de tensor (provável problema ABI): %s", exc)
            return False

    def fix(self) -> bool:
        """Update libstdc++6 via apt."""
        logger.info("Atualizando libstdc++6 via apt...")
        ok, _, stderr = _run_cmd(
            "apt-get update -qq && apt-get install -y -qq libstdc++6",
            timeout=120,
        )
        if not ok:
            logger.warning("Atualização do libstdc++ falhou: %s", stderr[:300])
        return ok

    def verify(self) -> bool:
        """Verify tensor operations work after fix."""
        return self.check()

    def fallback(self) -> bool:
        """Reinstall libstdc++ from scratch."""
        logger.info("Fallback: reinstalando libstdc++6...")
        ok, _, _ = _run_cmd(
            "apt-get install -y -qq --reinstall libstdc++6",
            timeout=120,
        )
        return ok

    def describe_problem(self) -> str:
        return (
            "libstdc++ (GLIBCXX) incompatível. Operações de tensor falham. "
            "Geralmente causado por atualização do Colab que dessincroniza "
            "a versão do GCC."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 12: DriveVaccine
# ══════════════════════════════════════════════════════════════

class DriveVaccine(Vaccine):
    """Check if Google Drive is mounted (Colab-only)."""

    @property
    def name(self) -> str:
        return "Google Drive"

    @property
    def description(self) -> str:
        return "Verificar se o Google Drive está montado"

    def check(self) -> bool:
        """
        Check if Drive is mounted.

        If not on Colab, always returns True (not applicable).
        """
        if not is_colab():
            logger.info("Não está no Colab — Drive check não aplicável.")
            return True

        drive_mount = "/content/drive"
        if os.path.ismount(drive_mount):
            logger.info("Google Drive montado em %s.", drive_mount)
            # Also check if data folder exists
            data_path = vp.DEFAULT_DRIVE_PATH
            if os.path.isdir(data_path):
                logger.info("Pasta de dados encontrada: %s", data_path)
            else:
                logger.warning(
                    "Pasta de dados NÃO encontrada: %s "
                    "(será criada automaticamente).",
                    data_path,
                )
            return True

        logger.warning("Google Drive NÃO montado em %s.", drive_mount)
        return False

    def fix(self) -> bool:
        """
        Cannot auto-mount Drive — requires user authentication.

        Returns False to signal the doctor this needs manual action.
        """
        if not is_colab():
            return True

        logger.warning(
            "Google Drive não pode ser montado automaticamente. "
            "Execute: from google.colab import drive; drive.mount('/content/drive')"
        )
        return False

    def verify(self) -> bool:
        """Verify Drive is mounted."""
        return self.check()

    def fallback(self) -> bool:
        """No automatic fallback for Drive mounting."""
        if not is_colab():
            return True

        logger.warning(
            "Sem fallback para montagem do Drive. "
            "O usuário precisa autenticar manualmente."
        )
        return False

    def describe_problem(self) -> str:
        return (
            "Google Drive não está montado. Os modelos e configurações "
            "são salvos no Drive para persistência entre sessões. "
            "Execute a célula de montagem do Drive manualmente."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 13: ForgeIntegrityVaccine
# ══════════════════════════════════════════════════════════════

class ForgeIntegrityVaccine(Vaccine):
    """Verify Forge installation integrity."""

    @property
    def name(self) -> str:
        return "Forge (Integridade)"

    @property
    def description(self) -> str:
        return "Verificar se o repositório do Forge está intacto"

    def _forge_path(self) -> Path:
        """Get the expected Forge installation path."""
        return Path(vp.DEFAULT_FORGE_PATH)

    def check(self) -> bool:
        """Check if launch.py exists in the Forge directory."""
        launch_file = self._forge_path() / vp.FORGE_LAUNCH_FILE
        if launch_file.is_file():
            logger.info("Forge encontrado: %s", launch_file)
            return True
        logger.warning("Forge NÃO encontrado: %s", launch_file)
        return False

    def fix(self) -> bool:
        """Re-clone the Forge repository."""
        forge_path = self._forge_path()
        logger.info("Clonando Forge de %s...", vp.FORGE_REPO_URL)

        # Remove broken installation if present
        if forge_path.exists():
            logger.info("Removendo instalação anterior: %s", forge_path)
            shutil.rmtree(forge_path, ignore_errors=True)

        ok, _, stderr = _run_cmd(
            f"git clone {vp.FORGE_REPO_URL} {forge_path}",
            timeout=300,
        )
        if not ok:
            logger.error("Clone do Forge falhou: %s", stderr[:300])
        return ok

    def verify(self) -> bool:
        """Verify launch.py exists after clone."""
        return self.check()

    def fallback(self) -> bool:
        """Provide error message — no other fallback for Forge."""
        logger.error(
            "Não foi possível restaurar o Forge. Verifique sua conexão com a internet "
            "e tente novamente. URL: %s",
            vp.FORGE_REPO_URL,
        )
        return False

    def describe_problem(self) -> str:
        return (
            f"Repositório do Forge não encontrado ou corrompido em "
            f"{self._forge_path()}. O arquivo {vp.FORGE_LAUNCH_FILE} "
            f"não existe."
        )


# ══════════════════════════════════════════════════════════════
# Vaccine 14: SymlinkVaccine
# ══════════════════════════════════════════════════════════════

class SymlinkVaccine(Vaccine):
    """Ensure all Forge symlinks point to cache directories."""

    @property
    def name(self) -> str:
        return "Symlinks"

    @property
    def description(self) -> str:
        return "Verificar symlinks entre Forge e cache local"

    def _get_expected_links(self) -> list[tuple[str, str]]:
        """
        Return list of (link_path, target_path) for all expected symlinks.

        Based on FORGE_SYMLINK_MAP from version_pins.
        """
        forge_models = Path(vp.DEFAULT_FORGE_PATH) / "models"
        cache_base = Path(vp.DEFAULT_CACHE_PATH)
        links = []

        for forge_name, cache_subdir in vp.FORGE_SYMLINK_MAP.items():
            link_path = str(forge_models / forge_name)
            target_path = str(cache_base / cache_subdir)
            links.append((link_path, target_path))

        # Also include the outputs symlink
        outputs_link = str(Path(vp.DEFAULT_FORGE_PATH) / "outputs")
        outputs_target = vp.DEFAULT_OUTPUTS_TEMP
        links.append((outputs_link, outputs_target))

        return links

    def check(self) -> bool:
        """Check if all expected symlinks exist and point to the right targets."""
        expected = self._get_expected_links()
        all_ok = True

        for link_path, target_path in expected:
            if os.path.islink(link_path):
                actual_target = os.readlink(link_path)
                if actual_target == target_path:
                    logger.debug("Symlink OK: %s → %s", link_path, target_path)
                else:
                    logger.warning(
                        "Symlink aponta para local errado: %s → %s (esperado: %s)",
                        link_path,
                        actual_target,
                        target_path,
                    )
                    all_ok = False
            elif os.path.exists(link_path):
                # It exists but is not a symlink (it's a real directory)
                logger.warning(
                    "Caminho existe mas NÃO é symlink: %s",
                    link_path,
                )
                all_ok = False
            else:
                # Doesn't exist at all — only a problem if Forge dir exists
                if os.path.isdir(vp.DEFAULT_FORGE_PATH):
                    logger.warning("Symlink ausente: %s", link_path)
                    all_ok = False
                else:
                    logger.debug(
                        "Forge não instalado — symlink check adiado: %s",
                        link_path,
                    )

        return all_ok

    def fix(self) -> bool:
        """Create or recreate all expected symlinks."""
        expected = self._get_expected_links()
        all_ok = True

        for link_path, target_path in expected:
            try:
                # Ensure target directory exists
                os.makedirs(target_path, exist_ok=True)

                # Remove existing path (symlink, file, or directory)
                if os.path.islink(link_path):
                    os.unlink(link_path)
                elif os.path.isdir(link_path):
                    # Move contents to target before removing
                    if os.listdir(link_path):
                        logger.info(
                            "Movendo conteúdo de %s para %s antes de criar symlink...",
                            link_path,
                            target_path,
                        )
                        for item in os.listdir(link_path):
                            src = os.path.join(link_path, item)
                            dst = os.path.join(target_path, item)
                            if not os.path.exists(dst):
                                shutil.move(src, dst)
                    shutil.rmtree(link_path, ignore_errors=True)
                elif os.path.isfile(link_path):
                    os.unlink(link_path)

                # Ensure parent directory exists
                os.makedirs(os.path.dirname(link_path), exist_ok=True)

                # Create symlink
                os.symlink(target_path, link_path)
                logger.info("Symlink criado: %s → %s", link_path, target_path)

            except Exception as exc:
                logger.error(
                    "Falha ao criar symlink %s → %s: %s",
                    link_path,
                    target_path,
                    exc,
                )
                all_ok = False

        return all_ok

    def verify(self) -> bool:
        """Verify all symlinks are correct."""
        return self.check()

    def fallback(self) -> bool:
        """Copy files instead of symlinking as fallback."""
        expected = self._get_expected_links()
        all_ok = True

        for link_path, target_path in expected:
            try:
                os.makedirs(target_path, exist_ok=True)

                if os.path.islink(link_path):
                    os.unlink(link_path)

                if not os.path.exists(link_path):
                    # Copy target to link location (reversed — target becomes source)
                    os.makedirs(link_path, exist_ok=True)
                    logger.info(
                        "Fallback: diretório criado (sem symlink): %s",
                        link_path,
                    )
            except Exception as exc:
                logger.error("Fallback de symlink falhou para %s: %s", link_path, exc)
                all_ok = False

        return all_ok

    def describe_problem(self) -> str:
        return (
            "Symlinks entre o Forge e o cache local estão ausentes ou "
            "apontando para locais errados. Sem eles, modelos baixados "
            "não serão encontrados pelo Forge."
        )


# ══════════════════════════════════════════════════════════════
# EnvironmentDoctor — Orchestrator
# ══════════════════════════════════════════════════════════════

class EnvironmentDoctor:
    """
    Orchestrates all 14 vaccines for automatic environment healing.

    Usage:
        doctor = EnvironmentDoctor()
        report = doctor.heal_all()
        print(report.to_text())
    """

    def __init__(self, skip_vaccines: Optional[list[str]] = None) -> None:
        """
        Initialize the EnvironmentDoctor.

        Args:
            skip_vaccines: Optional list of vaccine names to skip.
        """
        # Limpa qualquer resquício de execução anterior da memória para não quebrar builds
        import os
        os.environ.pop("PIP_CONSTRAINT", None)
        
        self._skip = set(skip_vaccines or [])
        self._vaccines: list[Vaccine] = self._build_vaccine_list()

    def _build_vaccine_list(self) -> list[Vaccine]:
        """
        Build the ordered list of vaccines.

        Order matters: dependencies should be checked first.
        """
        all_vaccines: list[Vaccine] = [
            PythonVersionVaccine(),     # 1.  Python 3.10
            PIPVaccine(),               # 2.  pip
            NumPyVaccine(),             # 3.  NumPy version
            ScikitImageVaccine(),       # 4.  scikit-image
            CLIPVaccine(),              # 5.  CLIP
            TorchCUDAVaccine(),         # 6.  PyTorch / CUDA
            BitsandbytesVaccine(),      # 7.  bitsandbytes
            OnnxruntimeVaccine(),       # 8.  ONNX Runtime
            InsightfaceVaccine(),       # 9. InsightFace
            LibstdcppVaccine(),         # 10. libstdc++ ABI
            PIPConstraintVaccine(),     # 11. PIP_CONSTRAINT (Moved to end to not block wheel builds)
            DriveVaccine(),             # 12. Google Drive
            ForgeIntegrityVaccine(),    # 13. Forge installation
            SymlinkVaccine(),           # 14. Symlinks
        ]

        if self._skip:
            return [v for v in all_vaccines if v.name not in self._skip]
        return all_vaccines

    def _apply_vaccine(self, vaccine: Vaccine) -> VaccineResult:
        """
        Apply a single vaccine through the 4-step protocol.

        Steps:
            1. check()    → If healthy, skip.
            2. fix()      → Attempt to fix.
            3. verify()   → Check if fix worked.
            4. fallback() → Last resort if fix didn't work.

        Returns:
            VaccineResult with status and details.
        """
        start = time.time()
        vaccine_name = vaccine.name

        logger.info("── Vacina: %s ──", vaccine_name)
        logger.info("   %s", vaccine.description)

        # Step 1: Check
        try:
            if vaccine.check():
                duration = time.time() - start
                return VaccineResult(
                    vaccine_name=vaccine_name,
                    status=VaccineStatus.HEALTHY,
                    message="Saudável — nenhuma ação necessária.",
                    duration_seconds=duration,
                )
        except Exception as exc:
            logger.error("Erro durante check() de %s: %s", vaccine_name, exc)

        logger.info("   Problema detectado: %s", vaccine.describe_problem())

        # Step 2: Fix
        fix_ok = False
        try:
            fix_ok = vaccine.fix()
        except Exception as exc:
            logger.error("Erro durante fix() de %s: %s", vaccine_name, exc)

        # Step 3: Verify (only if fix reported success)
        if fix_ok:
            try:
                if vaccine.verify():
                    duration = time.time() - start
                    return VaccineResult(
                        vaccine_name=vaccine_name,
                        status=VaccineStatus.FIXED,
                        message="Corrigido com sucesso!",
                        details=vaccine.describe_problem(),
                        duration_seconds=duration,
                    )
            except Exception as exc:
                logger.error("Erro durante verify() de %s: %s", vaccine_name, exc)

        # Step 4: Fallback
        logger.info("   Fix não resolveu — tentando fallback para %s...", vaccine_name)
        fallback_ok = False
        try:
            fallback_ok = vaccine.fallback()
        except Exception as exc:
            logger.error("Erro durante fallback() de %s: %s", vaccine_name, exc)

        duration = time.time() - start

        if fallback_ok:
            # Verify after fallback
            try:
                if vaccine.verify():
                    return VaccineResult(
                        vaccine_name=vaccine_name,
                        status=VaccineStatus.FIXED,
                        message="Corrigido via fallback.",
                        details=vaccine.describe_problem(),
                        duration_seconds=duration,
                    )
            except Exception as exc:
                logger.error(
                    "Erro ao verificar fallback de %s: %s",
                    vaccine_name,
                    exc,
                )

        # Special case: TorchCUDA and Drive are warnings, not failures
        if isinstance(vaccine, (TorchCUDAVaccine, DriveVaccine)):
            return VaccineResult(
                vaccine_name=vaccine_name,
                status=VaccineStatus.WARNING,
                message=vaccine.describe_problem(),
                details="Ação manual pode ser necessária.",
                duration_seconds=duration,
            )

        # All steps failed
        return VaccineResult(
            vaccine_name=vaccine_name,
            status=VaccineStatus.FAILED,
            message="Todas as tentativas de correção falharam.",
            details=vaccine.describe_problem(),
            duration_seconds=duration,
        )

    def heal_all(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> HealReport:
        """
        Apply all vaccines and return a comprehensive HealReport.

        Args:
            progress_callback: Optional function(current, total, vaccine_name)
                called before each vaccine to report progress.

        Returns:
            HealReport containing results of all vaccines.
        """
        report = HealReport()
        total = len(self._vaccines)

        logger.info("=" * 60)
        logger.info("🏥 EnvironmentDoctor — Iniciando diagnóstico completo")
        logger.info("   %d vacinas a aplicar.", total)
        logger.info("=" * 60)

        for i, vaccine in enumerate(self._vaccines):
            if progress_callback:
                try:
                    progress_callback(i, total, vaccine.name)
                except Exception:
                    pass  # Don't let callback errors break healing

            result = self._apply_vaccine(vaccine)
            report.add(result)

            # Log inline result
            logger.info(
                "   %s %s — %s (%s)",
                result.emoji,
                result.vaccine_name,
                result.status.value,
                result.message,
            )

        report.finalize()

        logger.info("=" * 60)
        logger.info("🏥 Diagnóstico completo em %.1fs", report.total_duration)
        if report.all_healthy:
            logger.info("✅ Ambiente 100%% saudável!")
        elif report.critical_failures:
            logger.error(
                "❌ %d falha(s) crítica(s) detectada(s).",
                len(report.critical_failures),
            )
        else:
            logger.warning("⚠️  Ambiente funcional com %d aviso(s).", len(report.warnings))
        logger.info("=" * 60)

        return report

    def check_only(self) -> HealReport:
        """
        Run only the check() step of each vaccine (no fixing).

        Useful for quick diagnostics without modifying the environment.
        """
        report = HealReport()

        logger.info("🔍 Modo diagnóstico (sem correção)...")

        for vaccine in self._vaccines:
            start = time.time()
            try:
                healthy = vaccine.check()
            except Exception as exc:
                healthy = False
                logger.error("Erro em check() de %s: %s", vaccine.name, exc)

            duration = time.time() - start

            if healthy:
                result = VaccineResult(
                    vaccine_name=vaccine.name,
                    status=VaccineStatus.HEALTHY,
                    message="OK",
                    duration_seconds=duration,
                )
            else:
                result = VaccineResult(
                    vaccine_name=vaccine.name,
                    status=VaccineStatus.WARNING,
                    message=vaccine.describe_problem(),
                    duration_seconds=duration,
                )
            report.add(result)

        report.finalize()
        return report


# ══════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════

def _parse_args() -> dict[str, Any]:
    """Parse command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description="EnvironmentDoctor — Diagnóstico e cura automática do ambiente.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  python auto_healer.py                # Diagnóstico + cura\n"
            "  python auto_healer.py --check-only    # Somente diagnóstico\n"
            "  python auto_healer.py --skip NumPy    # Pular vacina NumPy\n"
            "  python auto_healer.py --json           # Saída em JSON\n"
        ),
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Executar somente diagnóstico, sem tentar correções.",
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        default=[],
        metavar="VACINA",
        help="Nome(s) de vacina(s) a pular (ex: 'Google Drive' 'NumPy').",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprimir resultado em formato JSON.",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Imprimir resultado em formato HTML.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ativar logging detalhado (DEBUG).",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suprimir logs (somente resultado final).",
    )

    args = parser.parse_args()
    return vars(args)


def main() -> int:
    """Main entry point for CLI usage."""
    import json as json_mod

    args = _parse_args()

    # Configure logging level
    if args.get("quiet"):
        logger.setLevel(logging.CRITICAL)
    elif args.get("verbose"):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Build doctor
    doctor = EnvironmentDoctor(skip_vaccines=args.get("skip", []))

    # Progress callback for terminal
    def _progress(current: int, total: int, name: str) -> None:
        pct = ((current) / total) * 100 if total > 0 else 0
        print(f"\r  [{current + 1}/{total}] {pct:5.1f}% — {name}...", end="", flush=True)

    # Execute
    if args.get("check_only"):
        report = doctor.check_only()
    else:
        report = doctor.heal_all(progress_callback=_progress)
        print()  # Newline after progress

    # Output
    if args.get("json"):
        print(json_mod.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    elif args.get("html"):
        print(report.to_html())
    else:
        print(report.to_text())

    # Exit code: 0 if no failures, 1 if critical failures
    return 0 if not report.critical_failures else 1


if __name__ == "__main__":
    sys.exit(main())
