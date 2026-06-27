"""
hardware_detector.py
Módulo de detecção de hardware para o Google Colab.
Detecta GPU, VRAM, RAM, disco e classifica o perfil de hardware.
"""

import shutil
import multiprocessing


class HardwareDetector:
    """Detecta e classifica o hardware disponível no Google Colab."""

    PROFILES = {
        "GPU_LUXO": {
            "gpus": ["H100", "A100"],
            "forge_args": "--theme dark --cuda-malloc --cuda-stream",
            "description": "Desempenho Extremo",
        },
        "GPU_MEDIA": {
            "gpus": ["L4"],
            "forge_args": "--theme dark",
            "description": "Custo-Benefício",
        },
        "GPU_ECONOMICA": {
            "gpus": ["T4", "G4"],
            "forge_args": "--theme dark --always-offload-from-vram",
            "description": "Economia de Memória",
        },
        "CPU_TURBO": {
            "gpus": [],
            "forge_args": "--theme dark --use-cpu all --skip-torch-cuda-test --no-half --precision full",
            "description": "Modo CPU",
        },
    }

    def __init__(self):
        self.gpu_name = "Nenhuma (CPU)"
        self.vram_gb = 0.0
        self.ram_gb = 0.0
        self.disk_total_gb = 0.0
        self.disk_free_gb = 0.0
        self.cpu_cores = 0
        self.hardware_type = "UNKNOWN"
        self.forge_args = "--theme dark"
        self._detected = False

    def detect_all(self) -> dict:
        """Executa detecção completa e retorna dicionário com todos os dados."""
        self._detect_gpu()
        self._detect_ram()
        self._detect_disk()
        self._detect_cpu()
        self._classify()
        self._detected = True
        return self.get_report()

    def _detect_gpu(self):
        """Detecta GPU e VRAM via PyTorch CUDA."""
        try:
            import torch
            if torch.cuda.is_available():
                self.gpu_name = torch.cuda.get_device_name(0)
                self.vram_gb = round(
                    torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 1
                )
            else:
                self.gpu_name = "Nenhuma (CPU)"
                self.vram_gb = 0.0
        except Exception:
            self.gpu_name = "Nenhuma (CPU)"
            self.vram_gb = 0.0

    def _detect_ram(self):
        """Detecta RAM total do sistema."""
        try:
            import psutil
            self.ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
        except ImportError:
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            kb = int(line.split()[1])
                            self.ram_gb = round(kb / (1024 * 1024), 1)
                            break
            except Exception:
                self.ram_gb = 0.0

    def _detect_disk(self):
        """Detecta espaço em disco total e livre."""
        try:
            total, _, free = shutil.disk_usage("/content")
            self.disk_total_gb = round(total / (1024 ** 3), 1)
            self.disk_free_gb = round(free / (1024 ** 3), 1)
        except Exception:
            self.disk_total_gb = 0.0
            self.disk_free_gb = 0.0

    def _detect_cpu(self):
        """Detecta número de núcleos da CPU."""
        self.cpu_cores = multiprocessing.cpu_count()

    def _classify(self):
        """Classifica o hardware em um perfil conhecido."""
        gpu_upper = self.gpu_name.upper()

        # Verifica TPU primeiro
        try:
            import torch_xla
            self.hardware_type = "TPU"
            self.forge_args = "ERRO_TPU"
            return
        except ImportError:
            pass

        # Classifica GPU
        for profile_name, profile in self.PROFILES.items():
            if profile_name == "CPU_TURBO":
                continue
            for gpu_keyword in profile["gpus"]:
                if gpu_keyword in gpu_upper:
                    self.hardware_type = profile_name
                    self.forge_args = profile["forge_args"]
                    return

        # Fallback: CPU
        if self.vram_gb == 0:
            self.hardware_type = "CPU_TURBO"
            self.forge_args = self.PROFILES["CPU_TURBO"]["forge_args"]
            # Otimizações de CPU
            import os
            os.environ["OMP_NUM_THREADS"] = str(self.cpu_cores)
            os.environ["MKL_NUM_THREADS"] = str(self.cpu_cores)
            os.environ["OPENBLAS_NUM_THREADS"] = str(self.cpu_cores)
        else:
            self.hardware_type = "GPU_ECONOMICA"
            self.forge_args = self.PROFILES["GPU_ECONOMICA"]["forge_args"]

    def get_report(self) -> dict:
        """Retorna relatório completo do hardware detectado."""
        return {
            "gpu_name": self.gpu_name,
            "vram_gb": self.vram_gb,
            "ram_gb": self.ram_gb,
            "disk_total_gb": self.disk_total_gb,
            "disk_free_gb": self.disk_free_gb,
            "cpu_cores": self.cpu_cores,
            "hardware_type": self.hardware_type,
            "forge_args": self.forge_args,
            "description": self.PROFILES.get(self.hardware_type, {}).get(
                "description", "Desconhecido"
            ),
        }

    def get_report_text(self) -> str:
        """Retorna relatório formatado como texto para exibição."""
        if not self._detected:
            self.detect_all()

        lines = [
            f"🖥️ GPU: {self.gpu_name}",
            f"💾 VRAM: {self.vram_gb} GB" if self.vram_gb > 0 else "💾 VRAM: N/A",
            f"🧠 RAM: {self.ram_gb} GB",
            f"💿 Disco: {self.disk_free_gb}/{self.disk_total_gb} GB livres",
            f"⚙️ CPU: {self.cpu_cores} núcleos",
            f"📋 Perfil: {self.hardware_type} ({self.PROFILES.get(self.hardware_type, {}).get('description', '')})",
        ]
        return " | ".join(lines)

    def get_forge_args(self) -> str:
        """Retorna argumentos otimizados para o Forge."""
        if not self._detected:
            self.detect_all()
        return self.forge_args

    def get_vram_for_cache(self) -> float:
        """Retorna VRAM disponível considerando threshold (em GB)."""
        if not self._detected:
            self.detect_all()
        # Reserva 15% para operações do sistema
        return self.vram_gb * 0.85

    def get_ram_for_cache(self) -> float:
        """Retorna RAM disponível para cache de modelos (em GB)."""
        if not self._detected:
            self.detect_all()
        # Reserva 25% para OS + Python + Forge
        return self.ram_gb * 0.75

    def can_fit_in_vram(self, model_size_gb: float) -> bool:
        """Verifica se um modelo cabe na VRAM."""
        return model_size_gb <= self.get_vram_for_cache()

    def can_fit_in_ram(self, model_size_gb: float, current_ram_used_gb: float = 0) -> bool:
        """Verifica se um modelo cabe na RAM considerando uso atual."""
        available = self.get_ram_for_cache() - current_ram_used_gb
        return model_size_gb <= available
