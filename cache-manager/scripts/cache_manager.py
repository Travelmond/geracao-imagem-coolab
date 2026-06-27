"""
cache_manager.py
Gerenciador de cache hierárquico: Google Drive → Disco Local → RAM.
Gerencia cópia, pré-carregamento e limpeza de modelos de IA.
"""

import os
import shutil
import time


class CacheManager:
    """Gerencia cache de modelos com hierarquia: Drive → Disco → RAM."""

    DRIVE_DIRS = {
        "checkpoint": "Modelos_Base",
        "lora": "LoRAs",
        "vae": "VAEs",
        "text_encoder": "Text_Encoders",
    }

    CACHE_DIRS = {
        "checkpoint": "checkpoints",
        "lora": "loras",
        "vae": "vaes",
        "text_encoder": "text_encoders",
    }

    def __init__(self, drive_path: str, cache_path: str, log_callback=None):
        """
        Inicializa o gerenciador de cache.

        Args:
            drive_path: Caminho base do Google Drive montado.
            cache_path: Caminho base do cache local em disco.
            log_callback: Função opcional para receber mensagens de log.
        """
        self.drive_path = drive_path
        self.cache_path = cache_path
        self.ram_cache: dict[str, bytes] = {}
        self._log_callback = log_callback

    def _log(self, msg: str):
        """Registra mensagem de log."""
        if self._log_callback:
            self._log_callback(msg)

    def init_cache_dirs(self):
        """Cria a estrutura de diretórios do cache local."""
        for dir_name in self.CACHE_DIRS.values():
            path = os.path.join(self.cache_path, dir_name)
            os.makedirs(path, exist_ok=True)
            self._log(f"Diretório criado/verificado: {path}")

    def list_drive_models(self, model_type: str) -> list:
        """
        Lista modelos disponíveis no Google Drive.

        Args:
            model_type: Tipo do modelo (checkpoint, lora, vae, text_encoder).

        Returns:
            Lista de dicts com name, size_mb e size_human.
        """
        if model_type not in self.DRIVE_DIRS:
            return []

        drive_dir = os.path.join(self.drive_path, self.DRIVE_DIRS[model_type])
        if not os.path.isdir(drive_dir):
            self._log(f"Diretório do Drive não encontrado: {drive_dir}")
            return []

        models = []
        for filename in sorted(os.listdir(drive_dir)):
            filepath = os.path.join(drive_dir, filename)
            if not os.path.isfile(filepath):
                continue
            size_bytes = os.path.getsize(filepath)
            size_mb = round(size_bytes / (1024 ** 2), 1)
            models.append({
                "name": filename,
                "size_mb": size_mb,
                "size_human": self._format_size(size_bytes),
            })

        self._log(f"Encontrados {len(models)} modelos em {drive_dir}")
        return models

    def list_cached_models(self, model_type: str) -> list:
        """
        Lista modelos no cache local em disco.

        Args:
            model_type: Tipo do modelo (checkpoint, lora, vae, text_encoder).

        Returns:
            Lista de dicts com name, size_mb e size_human.
        """
        if model_type not in self.CACHE_DIRS:
            return []

        cache_dir = os.path.join(self.cache_path, self.CACHE_DIRS[model_type])
        if not os.path.isdir(cache_dir):
            return []

        models = []
        for filename in sorted(os.listdir(cache_dir)):
            filepath = os.path.join(cache_dir, filename)
            if not os.path.isfile(filepath):
                continue
            size_bytes = os.path.getsize(filepath)
            size_mb = round(size_bytes / (1024 ** 2), 1)
            models.append({
                "name": filename,
                "size_mb": size_mb,
                "size_human": self._format_size(size_bytes),
            })

        return models

    def list_ram_models(self) -> list:
        """
        Lista modelos carregados na RAM.

        Returns:
            Lista de dicts com name, size_mb e size_human.
        """
        models = []
        for filename, data in self.ram_cache.items():
            size_bytes = len(data)
            size_mb = round(size_bytes / (1024 ** 2), 1)
            models.append({
                "name": filename,
                "size_mb": size_mb,
                "size_human": self._format_size(size_bytes),
            })
        return models

    def get_model_status(self, model_type: str, filename: str) -> dict:
        """
        Retorna o status de um modelo em todos os níveis de cache.

        Args:
            model_type: Tipo do modelo.
            filename: Nome do arquivo do modelo.

        Returns:
            Dict com on_drive, on_disk, in_ram e size_mb.
        """
        status = {
            "on_drive": False,
            "on_disk": False,
            "in_ram": False,
            "size_mb": 0,
        }

        # Verifica no Drive
        if model_type in self.DRIVE_DIRS:
            drive_file = os.path.join(
                self.drive_path, self.DRIVE_DIRS[model_type], filename
            )
            if os.path.isfile(drive_file):
                status["on_drive"] = True
                status["size_mb"] = round(os.path.getsize(drive_file) / (1024 ** 2), 1)

        # Verifica no disco local
        if model_type in self.CACHE_DIRS:
            cache_file = os.path.join(
                self.cache_path, self.CACHE_DIRS[model_type], filename
            )
            if os.path.isfile(cache_file):
                status["on_disk"] = True
                if status["size_mb"] == 0:
                    status["size_mb"] = round(
                        os.path.getsize(cache_file) / (1024 ** 2), 1
                    )

        # Verifica na RAM
        if filename in self.ram_cache:
            status["in_ram"] = True
            if status["size_mb"] == 0:
                status["size_mb"] = round(
                    len(self.ram_cache[filename]) / (1024 ** 2), 1
                )

        return status

    def get_all_models_status(self) -> dict:
        """
        Retorna status de todos os modelos para a interface.

        Returns:
            Dict com chaves por tipo de modelo, cada uma contendo lista de status.
        """
        result = {}
        for model_type in self.DRIVE_DIRS:
            models = []
            # Coleta nomes únicos do Drive e do cache
            names = set()

            drive_dir = os.path.join(self.drive_path, self.DRIVE_DIRS[model_type])
            if os.path.isdir(drive_dir):
                for f in os.listdir(drive_dir):
                    if os.path.isfile(os.path.join(drive_dir, f)):
                        names.add(f)

            cache_dir = os.path.join(self.cache_path, self.CACHE_DIRS[model_type])
            if os.path.isdir(cache_dir):
                for f in os.listdir(cache_dir):
                    if os.path.isfile(os.path.join(cache_dir, f)):
                        names.add(f)

            for name in sorted(names):
                status = self.get_model_status(model_type, name)
                status["name"] = name
                status["type"] = model_type
                models.append(status)

            result[model_type] = models

        return result

    def copy_to_cache(self, model_type: str, filename: str, progress=None) -> tuple:
        """
        Copia modelo do Google Drive para o cache local em disco.

        Args:
            model_type: Tipo do modelo.
            filename: Nome do arquivo.
            progress: Callback de progresso(progress_current, progress_total, desc="...").

        Returns:
            Tupla (sucesso: bool, mensagem: str).
        """
        if model_type not in self.DRIVE_DIRS:
            return False, f"Tipo de modelo inválido: {model_type}"

        src = os.path.join(self.drive_path, self.DRIVE_DIRS[model_type], filename)
        dst_dir = os.path.join(self.cache_path, self.CACHE_DIRS[model_type])
        dst = os.path.join(dst_dir, filename)

        if not os.path.isfile(src):
            return False, f"Arquivo não encontrado no Drive: {src}"

        os.makedirs(dst_dir, exist_ok=True)

        total_size = os.path.getsize(src)
        chunk_size = 1024 * 1024  # 1 MB
        copied = 0

        try:
            if progress:
                progress(0, total_size, desc=f"Copiando {filename}")

            with open(src, "rb") as f_in, open(dst, "wb") as f_out:
                while True:
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    copied += len(chunk)
                    if progress:
                        progress(copied, total_size, desc=f"Copiando {filename}")

            if progress:
                progress(total_size, total_size, desc=f"Concluído: {filename}")

            self._log(f"Copiado para cache: {filename} ({self._format_size(total_size)})")
            return True, f"'{filename}' copiado com sucesso."

        except Exception as e:
            # Remove arquivo parcial em caso de erro
            if os.path.exists(dst):
                os.remove(dst)
            self._log(f"Erro ao copiar {filename}: {e}")
            return False, f"Erro ao copiar '{filename}': {e}"

    def sync_selected_to_cache(self, selected_models: dict, progress=None) -> list:
        """
        Copia todos os modelos selecionados para o cache local.

        Args:
            selected_models: Dict com {model_type: [filename, ...]}.
            progress: Callback de progresso.

        Returns:
            Lista de tuplas (model_type, filename, sucesso, mensagem).
        """
        results = []

        total_files = sum(len(files) for files in selected_models.values())
        current = 0

        for model_type, filenames in selected_models.items():
            for filename in filenames:
                current += 1
                if progress:
                    progress(
                        current,
                        total_files,
                        desc=f"[{current}/{total_files}] {filename}",
                    )

                success, message = self.copy_to_cache(model_type, filename, progress)
                results.append((model_type, filename, success, message))

        return results

    def preload_to_ram(self, model_type: str, filename: str) -> tuple:
        """
        Carrega modelo do disco para a RAM.

        Args:
            model_type: Tipo do modelo.
            filename: Nome do arquivo.

        Returns:
            Tupla (sucesso: bool, mensagem: str).
        """
        if model_type not in self.CACHE_DIRS:
            return False, f"Tipo de modelo inválido: {model_type}"

        cache_file = os.path.join(
            self.cache_path, self.CACHE_DIRS[model_type], filename
        )

        if not os.path.isfile(cache_file):
            return False, f"Arquivo não encontrado no cache: {filename}"

        try:
            with open(cache_file, "rb") as f:
                self.ram_cache[filename] = f.read()

            size_mb = len(self.ram_cache[filename]) / (1024 ** 2)
            self._log(f"Carregado na RAM: {filename} ({size_mb:.1f} MB)")
            return True, f"'{filename}' carregado na RAM ({size_mb:.1f} MB)."

        except Exception as e:
            self._log(f"Erro ao carregar na RAM {filename}: {e}")
            return False, f"Erro ao carregar '{filename}' na RAM: {e}"

    def unload_from_ram(self, filename: str) -> tuple:
        """
        Remove modelo da RAM.

        Args:
            filename: Nome do arquivo.

        Returns:
            Tupla (sucesso: bool, mensagem: str).
        """
        if filename not in self.ram_cache:
            return False, f"'{filename}' não está na RAM."

        size_mb = len(self.ram_cache[filename]) / (1024 ** 2)
        del self.ram_cache[filename]
        self._log(f"Removido da RAM: {filename} ({size_mb:.1f} MB liberados)")
        return True, f"'{filename}' removido da RAM ({size_mb:.1f} MB liberados)."

    def auto_preload_from_config(self, config: dict):
        """
        Pré-carrega na RAM modelos marcados com preload_ram=true na configuração.

        Args:
            config: Dict com configuração dos modelos. Formato esperado:
                    {model_type: {filename: {"preload_ram": bool, ...}, ...}}
        """
        for model_type, models in config.items():
            if not isinstance(models, dict):
                continue
            for filename, settings in models.items():
                if isinstance(settings, dict) and settings.get("preload_ram"):
                    if model_type in self.CACHE_DIRS:
                        cache_file = os.path.join(
                            self.cache_path, self.CACHE_DIRS[model_type], filename
                        )
                        if os.path.isfile(cache_file) and filename not in self.ram_cache:
                            success, msg = self.preload_to_ram(model_type, filename)
                            self._log(f"Auto-preload {filename}: {msg}")

    def remove_from_cache(self, model_type: str, filename: str) -> tuple:
        """
        Remove modelo do cache local em disco.

        Args:
            model_type: Tipo do modelo.
            filename: Nome do arquivo.

        Returns:
            Tupla (sucesso: bool, mensagem: str).
        """
        if model_type not in self.CACHE_DIRS:
            return False, f"Tipo de modelo inválido: {model_type}"

        cache_file = os.path.join(
            self.cache_path, self.CACHE_DIRS[model_type], filename
        )

        if not os.path.isfile(cache_file):
            return False, f"'{filename}' não encontrado no cache."

        try:
            size_bytes = os.path.getsize(cache_file)
            os.remove(cache_file)
            self._log(f"Removido do cache: {filename} ({self._format_size(size_bytes)})")
            return True, f"'{filename}' removido do cache ({self._format_size(size_bytes)} liberados)."
        except Exception as e:
            self._log(f"Erro ao remover do cache {filename}: {e}")
            return False, f"Erro ao remover '{filename}': {e}"

    def clear_cache(self, model_type: str = None) -> tuple:
        """
        Limpa o cache local em disco.

        Args:
            model_type: Tipo específico para limpar, ou None para limpar tudo.

        Returns:
            Tupla (sucesso: bool, mensagem: str).
        """
        try:
            total_freed = 0
            types_to_clear = []

            if model_type:
                if model_type not in self.CACHE_DIRS:
                    return False, f"Tipo de modelo inválido: {model_type}"
                types_to_clear = [model_type]
            else:
                types_to_clear = list(self.CACHE_DIRS.keys())

            for mtype in types_to_clear:
                cache_dir = os.path.join(self.cache_path, self.CACHE_DIRS[mtype])
                if not os.path.isdir(cache_dir):
                    continue
                for filename in os.listdir(cache_dir):
                    filepath = os.path.join(cache_dir, filename)
                    if os.path.isfile(filepath):
                        total_freed += os.path.getsize(filepath)
                        os.remove(filepath)

            scope = model_type if model_type else "todo o cache"
            self._log(f"Cache limpo ({scope}): {self._format_size(total_freed)} liberados")
            return True, f"Cache limpo ({scope}): {self._format_size(total_freed)} liberados."

        except Exception as e:
            self._log(f"Erro ao limpar cache: {e}")
            return False, f"Erro ao limpar cache: {e}"

    def clear_ram(self) -> tuple:
        """
        Limpa todo o cache de RAM.

        Returns:
            Tupla (sucesso: bool, mensagem: str).
        """
        total_mb = sum(len(data) for data in self.ram_cache.values()) / (1024 ** 2)
        count = len(self.ram_cache)
        self.ram_cache.clear()
        self._log(f"RAM limpa: {count} modelos removidos ({total_mb:.1f} MB liberados)")
        return True, f"RAM limpa: {count} modelos removidos ({total_mb:.1f} MB liberados)."

    def get_disk_usage(self) -> dict:
        """
        Retorna informações de uso do disco do cache local.

        Returns:
            Dict com total_gb, used_gb, free_gb e percent.
        """
        try:
            total, used, free = shutil.disk_usage(self.cache_path)
            return {
                "total_gb": round(total / (1024 ** 3), 2),
                "used_gb": round(used / (1024 ** 3), 2),
                "free_gb": round(free / (1024 ** 3), 2),
                "percent": round((used / total) * 100, 1),
            }
        except Exception:
            return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}

    def get_ram_usage(self) -> dict:
        """
        Retorna informações de uso da RAM pelo cache.

        Returns:
            Dict com total_gb, used_by_cache_mb, free_gb e percent.
        """
        try:
            import psutil
            total_bytes = psutil.virtual_memory().total
            free_bytes = psutil.virtual_memory().available
        except ImportError:
            try:
                with open("/proc/meminfo", "r") as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            meminfo[parts[0].rstrip(":")] = int(parts[1])
                    total_bytes = meminfo.get("MemTotal", 0) * 1024
                    free_bytes = meminfo.get("MemAvailable", 0) * 1024
            except Exception:
                total_bytes = 0
                free_bytes = 0

        cache_bytes = sum(len(data) for data in self.ram_cache.values())
        total_gb = total_bytes / (1024 ** 3) if total_bytes else 0
        free_gb = free_bytes / (1024 ** 3) if free_bytes else 0

        return {
            "total_gb": round(total_gb, 2),
            "used_by_cache_mb": round(cache_bytes / (1024 ** 2), 1),
            "free_gb": round(free_gb, 2),
            "percent": round((cache_bytes / total_bytes) * 100, 2) if total_bytes else 0,
        }

    def estimate_copy_time(self, model_type: str, filename: str) -> str:
        """
        Estima o tempo de cópia do Drive para o cache local.

        Args:
            model_type: Tipo do modelo.
            filename: Nome do arquivo.

        Returns:
            String com tempo estimado formatado.
        """
        if model_type not in self.DRIVE_DIRS:
            return "N/A"

        src = os.path.join(self.drive_path, self.DRIVE_DIRS[model_type], filename)
        if not os.path.isfile(src):
            return "Arquivo não encontrado"

        size_bytes = os.path.getsize(src)
        size_mb = size_bytes / (1024 ** 2)

        # Estimativa: ~50 MB/s para Google Drive montado (varia muito)
        estimated_seconds = size_mb / 50

        if estimated_seconds < 1:
            return "< 1s"
        elif estimated_seconds < 60:
            return f"~{int(estimated_seconds)}s"
        elif estimated_seconds < 3600:
            minutes = int(estimated_seconds / 60)
            seconds = int(estimated_seconds % 60)
            return f"~{minutes}m {seconds}s"
        else:
            hours = int(estimated_seconds / 3600)
            minutes = int((estimated_seconds % 3600) / 60)
            return f"~{hours}h {minutes}m"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """
        Formata tamanho em bytes para string legível.

        Args:
            size_bytes: Tamanho em bytes.

        Returns:
            String formatada (ex: "1.5 GB", "256 MB").
        """
        if size_bytes >= 1024 ** 3:
            return f"{size_bytes / (1024 ** 3):.1f} GB"
        elif size_bytes >= 1024 ** 2:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes} B"
