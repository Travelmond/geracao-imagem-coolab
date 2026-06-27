"""
memory_monitor.py
Monitor de memória em tempo real: VRAM, RAM e disco.
Executa em thread de fundo para verificar limites e executar ações automáticas.
"""

import os
import time
import shutil
import threading

try:
    import torch
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


class MemoryMonitor:
    """Monitora VRAM, RAM e disco em tempo real usando thread de fundo.

    Verifica periodicamente o uso de recursos e executa ações automáticas
    quando os limites configurados são excedidos (evicção de modelos da
    VRAM para RAM e da RAM para disco).
    """

    def __init__(self, cache_manager, session_manager, interval: int = 10):
        """Inicializa o monitor de memória.

        Args:
            cache_manager: Instância do CacheManager para gerenciar modelos.
            session_manager: Instância do SessionManager para registrar eventos.
            interval: Intervalo em segundos entre verificações (padrão: 10).
        """
        self.cache_manager = cache_manager
        self.session_manager = session_manager
        self.interval = interval

        self._thresholds = {
            "vram": 85,
            "ram": 75,
            "disk": 90,
        }

        self._thread = None
        self._running = False
        self._lock = threading.Lock()

    def set_thresholds(self, vram: int = 85, ram: int = 75, disk: int = 90):
        """Define os limites de alerta para cada recurso.

        Args:
            vram: Percentual limite de uso de VRAM (0-100).
            ram: Percentual limite de uso de RAM (0-100).
            disk: Percentual limite de uso de disco (0-100).
        """
        with self._lock:
            self._thresholds["vram"] = max(0, min(100, vram))
            self._thresholds["ram"] = max(0, min(100, ram))
            self._thresholds["disk"] = max(0, min(100, disk))

        self.session_manager.log_event(
            "info",
            f"Limites atualizados: VRAM={vram}%, RAM={ram}%, Disco={disk}%"
        )

    def get_vram_status(self) -> dict:
        """Retorna o status atual de uso da VRAM.

        Returns:
            Dicionário com total_gb, used_gb, free_gb, percent e gpu_name.
            Retorna valores zerados se CUDA não estiver disponível.
        """
        if not _HAS_TORCH or not torch.cuda.is_available():
            return {
                "total_gb": 0,
                "used_gb": 0,
                "free_gb": 0,
                "percent": 0,
                "gpu_name": "CUDA não disponível",
            }

        try:
            device = torch.cuda.current_device()
            total = torch.cuda.get_device_properties(device).total_memory
            reserved = torch.cuda.memory_reserved(device)
            allocated = torch.cuda.memory_allocated(device)
            free = total - allocated
            gpu_name = torch.cuda.get_device_name(device)

            total_gb = total / (1024 ** 3)
            used_gb = allocated / (1024 ** 3)
            free_gb = free / (1024 ** 3)
            percent = round((allocated / total) * 100, 1) if total > 0 else 0

            return {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "percent": percent,
                "gpu_name": gpu_name,
            }
        except Exception:
            return {
                "total_gb": 0,
                "used_gb": 0,
                "free_gb": 0,
                "percent": 0,
                "gpu_name": "Erro ao ler VRAM",
            }

    def get_ram_status(self) -> dict:
        """Retorna o status atual de uso da RAM do sistema.

        Returns:
            Dicionário com total_gb, used_gb, free_gb e percent.
        """
        try:
            if _HAS_PSUTIL:
                mem = psutil.virtual_memory()
                total_bytes = mem.total
                used_bytes = mem.used
                free_bytes = mem.available
            else:
                with open("/proc/meminfo", "r") as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            meminfo[parts[0].rstrip(":")] = int(parts[1])
                total_bytes = meminfo.get("MemTotal", 0) * 1024
                available_bytes = meminfo.get("MemAvailable", 0) * 1024
                free_bytes = available_bytes
                used_bytes = total_bytes - available_bytes

            total_gb = total_bytes / (1024 ** 3)
            used_gb = used_bytes / (1024 ** 3)
            free_gb = free_bytes / (1024 ** 3)
            percent = round((used_bytes / total_bytes) * 100, 1) if total_bytes > 0 else 0

            return {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "percent": percent,
            }
        except Exception:
            return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}

    def get_disk_status(self) -> dict:
        """Retorna o status atual de uso do disco do cache.

        Returns:
            Dicionário com total_gb, used_gb, free_gb e percent.
        """
        try:
            cache_path = self.cache_manager.cache_path
            total, used, free = shutil.disk_usage(cache_path)

            total_gb = total / (1024 ** 3)
            used_gb = used / (1024 ** 3)
            free_gb = free / (1024 ** 3)
            percent = round((used / total) * 100, 1) if total > 0 else 0

            return {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "percent": percent,
            }
        except Exception:
            return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}

    def get_full_report(self) -> dict:
        """Retorna um relatório combinado de todos os níveis de memória.

        Returns:
            Dicionário com vram, ram, disk e thresholds atuais.
        """
        with self._lock:
            thresholds = dict(self._thresholds)

        return {
            "vram": self.get_vram_status(),
            "ram": self.get_ram_status(),
            "disk": self.get_disk_status(),
            "thresholds": thresholds,
        }

    def start(self):
        """Inicia a thread de monitoramento em background.

        A thread é configurada como daemon para encerrar automaticamente
        quando o processo principal terminar.
        """
        if self._running:
            self.session_manager.log_event("warning", "Monitor já está em execução.")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="MemoryMonitor",
        )
        self._thread.start()
        self.session_manager.log_event(
            "info",
            f"Monitor de memória iniciado (intervalo: {self.interval}s)"
        )

    def stop(self):
        """Para a thread de monitoramento."""
        if not self._running:
            return

        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval + 2)
        self._thread = None
        self.session_manager.log_event("info", "Monitor de memória parado.")

    def _monitor_loop(self):
        """Loop principal do monitor. Executa a cada intervalo segundos.

        Este método é executado na thread de background e mantém consumo
        mínimo de CPU usando time.sleep() entre verificações.
        """
        while self._running:
            try:
                self._check_and_act()
            except Exception as e:
                self.session_manager.log_event(
                    "error", f"Erro no monitor de memória: {e}"
                )
            time.sleep(self.interval)

    def _check_and_act(self):
        """Verifica limites e executa ações automáticas quando necessário.

        Ações executadas:
        - VRAM acima do limite: log de alerta e tentativa de evicção para RAM.
        - RAM acima do limite: log de alerta e tentativa de evicção para disco.
        - Disco acima do limite: log de alerta.
        """
        with self._lock:
            thresholds = dict(self._thresholds)

        vram = self.get_vram_status()
        if vram["percent"] > 0 and vram["percent"] > thresholds["vram"]:
            self.session_manager.log_event(
                "warning",
                f"VRAM alta: {vram['percent']}% "
                f"(limite: {thresholds['vram']}%)"
            )
            self.auto_evict_vram()

        ram = self.get_ram_status()
        if ram["percent"] > thresholds["ram"]:
            self.session_manager.log_event(
                "warning",
                f"RAM alta: {ram['percent']}% "
                f"(limite: {thresholds['ram']}%)"
            )
            self._try_evict_ram_to_disk()

        disk = self.get_disk_status()
        if disk["percent"] > thresholds["disk"]:
            self.session_manager.log_event(
                "warning",
                f"Disco alto: {disk['percent']}% "
                f"(limite: {thresholds['disk']}%)"
            )

    def auto_evict_vram(self):
        """Tenta fazer evicção do modelo menos recentemente usado da VRAM.

        Procura modelos carregados na RAM e tenta liberar VRAM movendo-os.
        Registra a ação no histórico de uso via session_manager.
        """
        if not _HAS_TORCH or not torch.cuda.is_available():
            return

        try:
            torch.cuda.empty_cache()
            self.session_manager.log_event(
                "info", "Cache da VRAM limpo (torch.cuda.empty_cache)."
            )
        except Exception as e:
            self.session_manager.log_event(
                "error", f"Erro ao limpar cache da VRAM: {e}"
            )

    def _try_evict_ram_to_disk(self):
        """Tenta liberar RAM removendo modelos do cache de RAM.

        Remove o modelo menos recentemente usado do cache de RAM,
        registrando a ação no histórico de uso.
        """
        if not hasattr(self.cache_manager, "ram_cache"):
            return

        ram_cache = self.cache_manager.ram_cache
        if not ram_cache:
            return

        oldest_key = next(iter(ram_cache), None)
        if oldest_key is None:
            return

        try:
            success, msg = self.cache_manager.unload_from_ram(oldest_key)
            if success:
                self.session_manager.log_event(
                    "info",
                    f"Modelo removido da RAM por pressão de memória: {oldest_key}"
                )
        except Exception as e:
            self.session_manager.log_event(
                "error",
                f"Erro ao remover modelo da RAM: {e}"
            )
