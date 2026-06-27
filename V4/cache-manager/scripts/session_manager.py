"""
session_manager.py
Gerenciador de sessão e configuração persistente no Google Drive.
Controla modelos selecionados, histórico de uso, limites de recursos e logs.
"""

import os
import json
from datetime import datetime


class SessionManager:
    """Gerencia configuração persistente, sessões e logs no Google Drive."""

    MODEL_TYPES = ["checkpoint", "lora", "vae", "text_encoder"]
    LOG_LEVELS = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
    CONFIG_FILENAME = ".cache_config.json"
    LOGS_DIR = "logs"

    def __init__(self, drive_path: str):
        """Inicializa o gerenciador de sessão.

        Args:
            drive_path: Caminho base no Google Drive para armazenamento.
        """
        self.drive_path = drive_path
        self.config_path = os.path.join(drive_path, self.CONFIG_FILENAME)
        self.logs_path = os.path.join(drive_path, self.LOGS_DIR)
        self._config = None
        self._session_log = []

    def load_config(self) -> dict:
        """Carrega configuração do Drive ou cria uma nova se não existir.

        Returns:
            Dicionário com a configuração carregada.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                self._ensure_config_fields()
                return self._config
            except (json.JSONDecodeError, IOError):
                self._config = self.get_default_config()
                self.save_config()
                return self._config
        else:
            self._config = self.get_default_config()
            self.save_config()
            return self._config

    def save_config(self) -> bool:
        """Salva configuração atual no Drive.

        Returns:
            True se salvou com sucesso, False caso contrário.
        """
        if self._config is None:
            self._config = self.get_default_config()
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def get_default_config(self) -> dict:
        """Retorna a estrutura padrão de configuração.

        Returns:
            Dicionário com configuração padrão.
        """
        return {
            "version": "2.0",
            "drive_path": self.drive_path,
            "civitai_api_key": "",
            "cache_path": "/content/cache",
            "thresholds": {
                "vram_percent": 85,
                "ram_percent": 75,
                "disk_percent": 90,
            },
            "auto_preload_ram": True,
            "selected_models": {
                model_type: {
                    "active": None,
                    "preload_ram": model_type == "checkpoint",
                    "cached_on_disk": [],
                }
                for model_type in self.MODEL_TYPES
            },
            "usage_history": [],
            "last_hardware": {},
            "last_session": {
                "date": None,
                "models_in_cache": [],
                "models_in_ram": [],
            },
        }

    def _ensure_config_fields(self):
        """Garante que todos os campos obrigatórios existam na configuração."""
        default = self.get_default_config()
        for key, value in default.items():
            if key not in self._config:
                self._config[key] = value
            elif isinstance(value, dict) and key != "usage_history":
                for sub_key, sub_value in value.items():
                    if sub_key not in self._config[key]:
                        self._config[key][sub_key] = sub_value

    def _get_config(self) -> dict:
        """Retorna configuração carregada, carregando se necessário."""
        if self._config is None:
            self.load_config()
        return self._config

    def restore_last_session(self) -> dict:
        """Restaura os dados da última sessão salva.

        Returns:
            Dicionário com dados da última sessão (date, models_in_cache, models_in_ram).
        """
        config = self._get_config()
        return config.get("last_session", {
            "date": None,
            "models_in_cache": [],
            "models_in_ram": [],
        })

    def update_last_session(self, models_in_cache: list, models_in_ram: list):
        """Salva o estado atual da sessão.

        Args:
            models_in_cache: Lista de modelos atualmente em cache no disco.
            models_in_ram: Lista de modelos atualmente carregados na RAM.
        """
        config = self._get_config()
        config["last_session"] = {
            "date": datetime.now().isoformat(),
            "models_in_cache": models_in_cache,
            "models_in_ram": models_in_ram,
        }
        self.save_config()

    def get_selected_models(self) -> dict:
        """Retorna os modelos selecionados organizados por tipo.

        Returns:
            Dicionário com modelos selecionados por tipo (checkpoint, lora, etc).
        """
        config = self._get_config()
        return config.get("selected_models", {})

    def set_selected_model(self, model_type: str, filename: str,
                           active: bool = False, preload_ram: bool = False):
        """Marca um modelo como selecionado para um tipo.

        Args:
            model_type: Tipo do modelo (checkpoint, lora, vae, text_encoder).
            filename: Nome do arquivo do modelo.
            active: Se True, define como modelo ativo para o tipo.
            preload_ram: Se True, habilita pré-carregamento em RAM.
        """
        if model_type not in self.MODEL_TYPES:
            return

        config = self._get_config()
        selected = config["selected_models"]

        if model_type not in selected:
            selected[model_type] = {
                "active": None,
                "preload_ram": False,
                "cached_on_disk": [],
            }

        if filename not in selected[model_type]["cached_on_disk"]:
            selected[model_type]["cached_on_disk"].append(filename)

        if active:
            selected[model_type]["active"] = filename

        if preload_ram:
            selected[model_type]["preload_ram"] = True

        self.save_config()

    def remove_selected_model(self, model_type: str, filename: str):
        """Remove um modelo da lista de selecionados.

        Args:
            model_type: Tipo do modelo (checkpoint, lora, vae, text_encoder).
            filename: Nome do arquivo do modelo.
        """
        if model_type not in self.MODEL_TYPES:
            return

        config = self._get_config()
        selected = config["selected_models"]

        if model_type not in selected:
            return

        if filename in selected[model_type]["cached_on_disk"]:
            selected[model_type]["cached_on_disk"].remove(filename)

        if selected[model_type]["active"] == filename:
            selected[model_type]["active"] = None

        self.save_config()

    def get_active_model(self, model_type: str) -> str:
        """Retorna o modelo ativo para um determinado tipo.

        Args:
            model_type: Tipo do modelo (checkpoint, lora, vae, text_encoder).

        Returns:
            Nome do arquivo do modelo ativo, ou None se nenhum estiver ativo.
        """
        config = self._get_config()
        selected = config.get("selected_models", {})
        if model_type in selected:
            return selected[model_type].get("active")
        return None

    def get_cached_on_disk(self, model_type: str) -> list:
        """Retorna a lista de modelos em cache no disco para um tipo.

        Args:
            model_type: Tipo do modelo (checkpoint, lora, vae, text_encoder).

        Returns:
            Lista com os nomes dos arquivos em cache.
        """
        config = self._get_config()
        selected = config.get("selected_models", {})
        if model_type in selected:
            return selected[model_type].get("cached_on_disk", [])
        return []

    def get_thresholds(self) -> dict:
        """Retorna os limites de recursos configurados.

        Returns:
            Dicionário com thresholds (vram_percent, ram_percent, disk_percent).
        """
        config = self._get_config()
        return config.get("thresholds", {
            "vram_percent": 85,
            "ram_percent": 75,
            "disk_percent": 90,
        })

    def set_threshold(self, key: str, value):
        """Define um limite de recurso.

        Args:
            key: Nome do limite (vram_percent, ram_percent, disk_percent).
            value: Valor do limite (0-100).
        """
        config = self._get_config()
        if "thresholds" not in config:
            config["thresholds"] = {}
        config["thresholds"][key] = value
        self.save_config()

    def get_api_key(self) -> str:
        """Retorna a chave de API do CivitAI armazenada.

        Returns:
            Chave de API como string, ou string vazia se não configurada.
        """
        config = self._get_config()
        return config.get("civitai_api_key", "")

    def set_api_key(self, key: str):
        """Define a chave de API do CivitAI.

        Args:
            key: Chave de API do CivitAI.
        """
        config = self._get_config()
        config["civitai_api_key"] = key
        self.save_config()

    def add_usage_history(self, model_type: str, filename: str, action: str):
        """Registra uma ação no histórico de uso (LRU).

        Args:
            model_type: Tipo do modelo (checkpoint, lora, vae, text_encoder).
            filename: Nome do arquivo do modelo.
            action: Ação realizada (ex: loaded, unloaded, cached, evicted).
        """
        config = self._get_config()
        if "usage_history" not in config:
            config["usage_history"] = []

        entry = {
            "timestamp": datetime.now().isoformat(),
            "model_type": model_type,
            "filename": filename,
            "action": action,
        }
        config["usage_history"].append(entry)

        if len(config["usage_history"]) > 500:
            config["usage_history"] = config["usage_history"][-500:]

        self.save_config()

    def get_usage_history(self, limit: int = 50) -> list:
        """Retorna o histórico de uso mais recente.

        Args:
            limit: Número máximo de entradas a retornar.

        Returns:
            Lista de entradas do histórico (mais recentes primeiro).
        """
        config = self._get_config()
        history = config.get("usage_history", [])
        return list(reversed(history[-limit:]))

    def log_event(self, level: str, message: str):
        """Adiciona um evento ao log da sessão atual.

        Args:
            level: Nível do evento (info, success, warning, error).
            message: Mensagem descritiva do evento.
        """
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level if level in self.LOG_LEVELS else "info",
            "message": message,
        }
        self._session_log.append(entry)

    def get_session_log(self) -> list:
        """Retorna todas as entradas do log da sessão atual.

        Returns:
            Lista de entradas do log.
        """
        return list(self._session_log)

    def get_session_log_text(self) -> str:
        """Retorna o log da sessão formatado como texto.

        Returns:
            String com o log formatado para exibição.
        """
        if not self._session_log:
            return "Nenhum evento registrado nesta sessão."

        lines = []
        for entry in self._session_log:
            icon = self.LOG_LEVELS.get(entry["level"], "ℹ️")
            lines.append(f"[{entry['timestamp']}] {icon} {entry['message']}")
        return "\n".join(lines)

    def save_log(self, filename: str = None) -> tuple:
        """Salva o log da sessão no Drive.

        Args:
            filename: Nome do arquivo. Se None, gera nome com data/hora.

        Returns:
            Tupla (sucesso: bool, mensagem: str, caminho: str).
        """
        if not self._session_log:
            return (False, "Nenhum evento no log para salvar.", "")

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{timestamp}.json"

        filepath = os.path.join(self.logs_path, filename)

        try:
            os.makedirs(self.logs_path, exist_ok=True)
            log_data = {
                "session_date": datetime.now().isoformat(),
                "total_events": len(self._session_log),
                "events": self._session_log,
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            return (True, f"Log salvo com sucesso: {filename}", filepath)
        except IOError as e:
            return (False, f"Erro ao salvar log: {e}", "")

    def export_log_text(self) -> str:
        """Exporta o log como texto formatado completo com cabeçalho.

        Returns:
            String formatada com informações da sessão e log completo.
        """
        header = [
            "=" * 60,
            f"LOG DA SESSÃO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "=" * 60,
            f"Total de eventos: {len(self._session_log)}",
            "-" * 60,
            "",
        ]
        body = self.get_session_log_text()
        footer = ["", "-" * 60, "Fim do log"]

        return "\n".join(header) + "\n" + body + "\n" + "\n".join(footer)
