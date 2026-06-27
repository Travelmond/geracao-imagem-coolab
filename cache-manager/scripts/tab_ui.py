"""
tab_ui.py
Interface Gradio para o Cache Manager no Stable Diffusion WebUI Forge.
Registra a aba "Cache Manager" via script_callbacks.on_ui_tabs.
Gerencia modelos, recursos do sistema, configurações e logs.
"""

import os
import sys
import gradio as gr
from modules import script_callbacks

try:
    from .hardware_detector import HardwareDetector
    from .session_manager import SessionManager
    from .cache_manager import CacheManager
    from .memory_monitor import MemoryMonitor
    from .forge_bridge import ForgeBridge
except ImportError:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    if _script_dir not in sys.path:
        sys.path.insert(0, _script_dir)
    from hardware_detector import HardwareDetector
    from session_manager import SessionManager
    from cache_manager import CacheManager
    from memory_monitor import MemoryMonitor
    from forge_bridge import ForgeBridge

_hardware: HardwareDetector = None
_session: SessionManager = None
_cache: CacheManager = None
_monitor: MemoryMonitor = None
_bridge: ForgeBridge = None
_initialized: bool = False

DEFAULT_DRIVE_PATH = "/content/drive/MyDrive/Stable_Diffusion_Dados"
DEFAULT_CACHE_PATH = "/content/cache"
MODEL_TYPES = ["checkpoint", "lora", "vae", "text_encoder"]
MODEL_TYPE_LABELS = {
    "checkpoint": "Checkpoints",
    "lora": "LoRAs",
    "vae": "VAEs",
    "text_encoder": "Text Encoders",
}
DRIVE_DIRS = {
    "checkpoint": "Modelos_Base",
    "lora": "LoRAs",
    "vae": "VAEs",
    "text_encoder": "Text_Encoders",
}


def _log_callback(msg: str):
    """Callback de log que registra no session manager se disponível."""
    if _session is not None:
        _session.log_event("info", msg)


def _init_managers(drive_path: str = None, cache_path: str = None):
    """Inicializa todos os gerenciadores de forma lazy.

    Args:
        drive_path: Caminho do Google Drive. Usa padrão se None.
        cache_path: Caminho do cache local. Usa padrão se None.
    """
    global _hardware, _session, _cache, _monitor, _bridge, _initialized
    if _initialized:
        return

    dp = drive_path or DEFAULT_DRIVE_PATH
    cp = cache_path or DEFAULT_CACHE_PATH

    try:
        _hardware = HardwareDetector()
        _hardware.detect_all()
    except Exception as e:
        print(f"[cache-manager] Aviso: HardwareDetector falhou: {e}")
        _hardware = HardwareDetector()

    try:
        _session = SessionManager(dp)
        _session.load_config()
    except Exception as e:
        print(f"[cache-manager] Aviso: SessionManager falhou: {e}")
        _session = SessionManager(dp)

    try:
        _cache = CacheManager(dp, cp, log_callback=_log_callback)
        _cache.init_cache_dirs()
    except Exception as e:
        print(f"[cache-manager] Aviso: CacheManager falhou: {e}")
        _cache = CacheManager(dp, cp)

    try:
        _monitor = MemoryMonitor(_cache, _session)
        thresholds = _session.get_thresholds() if _session else {}
        _monitor.set_thresholds(
            vram=thresholds.get("vram_percent", 85),
            ram=thresholds.get("ram_percent", 75),
            disk=thresholds.get("disk_percent", 90),
        )
    except Exception as e:
        print(f"[cache-manager] Aviso: MemoryMonitor falhou: {e}")
        _monitor = MemoryMonitor(_cache, _session)

    try:
        forge_path = os.environ.get("FORGE_PATH", "/content/stable-diffusion-webui-forge")
        _bridge = ForgeBridge(forge_path, cp, dp, log_callback=_log_callback)
        _bridge.setup_symlinks()
    except Exception as e:
        print(f"[cache-manager] Aviso: ForgeBridge falhou: {e}")
        _bridge = ForgeBridge("/content/stable-diffusion-webui-forge", cp, dp)

    try:
        if _session:
            _session.log_event("success", "Cache Manager inicializado com sucesso.")
    except Exception:
        pass

    _initialized = True


def _get_drive_path() -> str:
    """Retorna o caminho do Google Drive a partir da configuração."""
    if _session is not None:
        config = _session._get_config()
        return config.get("drive_path", DEFAULT_DRIVE_PATH)
    return DEFAULT_DRIVE_PATH


def _get_cache_path() -> str:
    """Retorna o caminho do cache local a partir da configuração."""
    if _session is not None:
        config = _session._get_config()
        return config.get("cache_path", DEFAULT_CACHE_PATH)
    return DEFAULT_CACHE_PATH


def _format_resource_bar(status: dict, label: str) -> str:
    """Formata uma barra de recurso com texto descritivo.

    Args:
        status: Dicionário com used_gb, total_gb, percent.
        label: Nome do recurso (VRAM, RAM, Disco).

    Returns:
        String formatada para exibição.
    """
    used = status.get("used_gb", 0)
    total = status.get("total_gb", 0)
    percent = status.get("percent", 0)
    return f"{label}: {used:.1f} / {total:.1f} GB ({percent:.1f}%)"


def _build_model_table_data(model_type: str) -> list:
    """Constrói os dados da tabela de modelos para um tipo específico.

    Args:
        model_type: Tipo do modelo (checkpoint, lora, vae, text_encoder).

    Returns:
        Lista de listas com dados das linhas da tabela.
    """
    if _cache is None:
        return []

    try:
        all_status = _cache.get_all_models_status()
        if not isinstance(all_status, dict):
            return []
        models = all_status.get(model_type, [])
        if not isinstance(models, list):
            return []
    except Exception:
        return []

    rows = []
    for m in models:
        name = m.get("name", "")
        size_mb = m.get("size_mb", 0)
        on_drive = m.get("on_drive", False)
        on_disk = m.get("on_disk", False)
        in_ram = m.get("in_ram", False)

        size_str = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb / 1024:.1f} GB"

        rows.append([
            False,
            name,
            size_str,
            "✅" if on_drive else "❌",
            "✅" if on_disk else "❌",
            "✅" if in_ram else "❌",
            "❌",
            "📥 🧠 🎯 🗑️🗑️",
        ])

    return rows


def refresh_resources():
    """Atualiza as barras de recursos do sistema.

    Returns:
        Tuple com strings formatadas para VRAM, RAM, Disco e info de hardware.
    """
    _init_managers()

    vram = _monitor.get_vram_status()
    ram = _monitor.get_ram_status()
    disk = _monitor.get_disk_status()

    vram_text = _format_resource_bar(vram, "VRAM")
    ram_text = _format_resource_bar(ram, "RAM")
    disk_text = _format_resource_bar(disk, "Disco")

    hw_report = _hardware.get_report()
    hw_info = (
        f"GPU: {hw_report['gpu_name']} | "
        f"CPU: {hw_report['cpu_cores']} núcleos | "
        f"Perfil: {hw_report['hardware_type']} ({hw_report['description']})"
    )

    vram_progress = vram.get("percent", 0) / 100
    ram_progress = ram.get("percent", 0) / 100
    disk_progress = disk.get("percent", 0) / 100

    return (
        vram_text, ram_text, disk_text, hw_info,
        vram_progress, ram_progress, disk_progress,
    )


def refresh_model_table(model_type: str):
    """Atualiza a tabela de modelos para um tipo específico.

    Args:
        model_type: Tipo do modelo.

    Returns:
        Dados atualizados para gr.Dataframe.
    """
    _init_managers()
    return _build_model_table_data(model_type)


def refresh_all():
    """Atualiza todas as tabelas de modelos e barras de recursos.

    Returns:
        Lista com todos os valores atualizados para os componentes da UI.
    """
    try:
        _init_managers()
    except Exception:
        pass

    try:
        resources = list(refresh_resources())
    except Exception:
        resources = ["Erro ao ler recursos", "Erro ao ler RAM", "Erro ao ler Disco",
                     "Erro ao detectar hardware", 0, 0, 0]

    try:
        tables = [_build_model_table_data(mt) for mt in MODEL_TYPES]
    except Exception:
        empty_row = [["—"] * 8]
        tables = [empty_row] * 4

    try:
        log_text = _session.get_session_log_text() if _session else ""
    except Exception:
        log_text = "Log indisponível."

    return resources + tables + [log_text]


def copy_model_to_cache(model_type: str, filename: str, progress=gr.Progress()):
    """Copia um modelo do Google Drive para o cache local com progresso.

    Args:
        model_type: Tipo do modelo.
        filename: Nome do arquivo do modelo.
        progress: Objeto de progresso do Gradio.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    if not filename:
        return "Nenhum modelo selecionado."

    try:
        def progress_callback(current, total, desc=""):
            if total > 0:
                progress(current / total, desc=desc)

        success, msg = _cache.copy_to_cache(model_type, filename, progress_callback)
        if success:
            _session.log_event("success", f"Copiado para cache: {filename}")
        else:
            _session.log_event("error", f"Falha ao copiar: {msg}")
        return msg
    except Exception as e:
        _session.log_event("error", f"Erro ao copiar modelo: {e}")
        return f"Erro: {e}"


def preload_model_to_ram(model_type: str, filename: str):
    """Pré-carrega um modelo do disco para a RAM.

    Args:
        model_type: Tipo do modelo.
        filename: Nome do arquivo do modelo.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    if not filename:
        return "Nenhum modelo selecionado."

    try:
        success, msg = _cache.preload_to_ram(model_type, filename)
        if success:
            _session.add_usage_history(model_type, filename, "preload_ram")
            _session.log_event("success", f"Pré-carregado na RAM: {filename}")
        else:
            _session.log_event("error", f"Falha ao pré-carregar: {msg}")
        return msg
    except Exception as e:
        _session.log_event("error", f"Erro ao pré-carregar: {e}")
        return f"Erro: {e}"


def set_model_active(model_type: str, filename: str):
    """Define um modelo como ativo, carregando-o na VRAM via Forge.

    Args:
        model_type: Tipo do modelo.
        filename: Nome do arquivo do modelo.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    if not filename:
        return "Nenhum modelo selecionado."

    try:
        _session.set_selected_model(model_type, filename, active=True)
        _session.add_usage_history(model_type, filename, "activated")
        _session.log_event("success", f"Modelo definido como ativo: {filename}")

        if _bridge:
            _bridge.refresh_models()

        return f"'{filename}' definido como modelo ativo."
    except Exception as e:
        _session.log_event("error", f"Erro ao ativar modelo: {e}")
        return f"Erro: {e}"


def remove_from_disk(model_type: str, filename: str):
    """Remove um modelo do cache local em disco.

    Args:
        model_type: Tipo do modelo.
        filename: Nome do arquivo do modelo.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    if not filename:
        return "Nenhum modelo selecionado."

    try:
        success, msg = _cache.remove_from_cache(model_type, filename)
        if success:
            _session.add_usage_history(model_type, filename, "evicted")
            _session.log_event("info", f"Removido do disco: {filename}")
        else:
            _session.log_event("error", f"Falha ao remover do disco: {msg}")
        return msg
    except Exception as e:
        _session.log_event("error", f"Erro ao remover do disco: {e}")
        return f"Erro: {e}"


def remove_from_ram(filename: str):
    """Remove um modelo da RAM.

    Args:
        filename: Nome do arquivo do modelo.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    if not filename:
        return "Nenhum modelo selecionado."

    try:
        success, msg = _cache.unload_from_ram(filename)
        if success:
            _session.add_usage_history("unknown", filename, "unloaded_ram")
            _session.log_event("info", f"Removido da RAM: {filename}")
        else:
            _session.log_event("error", f"Falha ao remover da RAM: {msg}")
        return msg
    except Exception as e:
        _session.log_event("error", f"Erro ao remover da RAM: {e}")
        return f"Erro: {e}"


def sync_selected(
    checkpoint_data, lora_data, vae_data, te_data,
    progress=gr.Progress(),
):
    """Sincroniza todos os modelos selecionados para o cache local.

    Args:
        checkpoint_data: Dados da tabela de checkpoints.
        lora_data: Dados da tabela de LoRAs.
        vae_data: Dados da tabela de VAEs.
        te_data: Dados da tabela de Text Encoders.
        progress: Objeto de progresso do Gradio.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    tables = {
        "checkpoint": checkpoint_data,
        "lora": lora_data,
        "vae": vae_data,
        "text_encoder": te_data,
    }

    selected = {}
    for model_type, data in tables.items():
        if data is None:
            continue
        filenames = []
        for row in data:
            if isinstance(row, list) and len(row) >= 2 and row[0]:
                filenames.append(row[1])
        if filenames:
            selected[model_type] = filenames

    if not selected:
        return "Nenhum modelo selecionado para sincronizar."

    try:
        total_files = sum(len(f) for f in selected.values())
        progress(0, total_files, desc="Iniciando sincronização...")

        results = _cache.sync_selected_to_cache(selected, progress)

        success_count = sum(1 for _, _, s, _ in results if s)
        fail_count = total_files - success_count

        msg = f"Sincronização concluída: {success_count} sucesso(s), {fail_count} falha(s)."
        _session.log_event("success" if fail_count == 0 else "warning", msg)
        return msg
    except Exception as e:
        _session.log_event("error", f"Erro na sincronização: {e}")
        return f"Erro: {e}"


def copy_all(progress=gr.Progress()):
    """Copia todos os modelos do Google Drive para o cache local.

    Args:
        progress: Objeto de progresso do Gradio.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    try:
        all_status = _cache.get_all_models_status()
        total_files = sum(len(models) for models in all_status.values())

        if total_files == 0:
            return "Nenhum modelo encontrado no Drive."

        progress(0, total_files, desc="Copiando todos os modelos...")

        copied = 0
        errors = 0
        current = 0

        for model_type, models in all_status.items():
            for m in models:
                current += 1
                name = m.get("name", "")
                if not m.get("on_drive"):
                    continue

                progress(current, total_files, desc=f"Copiando {name}...")
                success, msg = _cache.copy_to_cache(model_type, name)
                if success:
                    copied += 1
                else:
                    errors += 1

        result = f"Cópia concluída: {copied} copiado(s), {errors} erro(s) de {total_files} total."
        _session.log_event("success" if errors == 0 else "warning", result)
        return result
    except Exception as e:
        _session.log_event("error", f"Erro ao copiar todos: {e}")
        return f"Erro: {e}"


def clear_cache(model_type: str):
    """Limpa o cache local em disco para um tipo de modelo ou todos.

    Args:
        model_type: Tipo do modelo ou "all" para limpar tudo.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    try:
        target = None if model_type == "all" else model_type
        success, msg = _cache.clear_cache(target)
        if success:
            _session.log_event("success", msg)
        else:
            _session.log_event("error", msg)
        return msg
    except Exception as e:
        _session.log_event("error", f"Erro ao limpar cache: {e}")
        return f"Erro: {e}"


def save_config(
    drive_path, api_key, vram_threshold, ram_threshold, disk_threshold, auto_preload,
):
    """Salva a configuração atual no Google Drive.

    Args:
        drive_path: Caminho do Google Drive.
        api_key: Chave de API do CivitAI.
        vram_threshold: Limite de VRAM (%).
        ram_threshold: Limite de RAM (%).
        disk_threshold: Limite de disco (%).
        auto_preload: Se deve pré-carregar automaticamente na RAM.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    try:
        config = _session._get_config()
        config["drive_path"] = drive_path
        config["civitai_api_key"] = api_key
        config["thresholds"]["vram_percent"] = int(vram_threshold)
        config["thresholds"]["ram_percent"] = int(ram_threshold)
        config["thresholds"]["disk_percent"] = int(disk_threshold)
        config["auto_preload_ram"] = bool(auto_preload)
        _session.save_config()

        _monitor.set_thresholds(
            vram=int(vram_threshold),
            ram=int(ram_threshold),
            disk=int(disk_threshold),
        )

        _session.log_event("success", "Configuração salva com sucesso.")
        return "Configuração salva com sucesso!"
    except Exception as e:
        _session.log_event("error", f"Erro ao salvar configuração: {e}")
        return f"Erro ao salvar: {e}"


def restore_defaults():
    """Restaura a configuração padrão.

    Returns:
        Tuple com os valores padrão para os componentes da UI.
    """
    _init_managers()

    try:
        default = SessionManager(_get_drive_path()).get_default_config()
        _session._config = default
        _session.save_config()

        _monitor.set_thresholds(vram=85, ram=75, disk=90)

        _session.log_event("info", "Configuração restaurada para padrão.")

        return (
            default["drive_path"],
            default.get("civitai_api_key", ""),
            default["thresholds"]["vram_percent"],
            default["thresholds"]["ram_percent"],
            default["thresholds"]["disk_percent"],
            default["auto_preload_ram"],
            "Configuração padrão restaurada!",
        )
    except Exception as e:
        _session.log_event("error", f"Erro ao restaurar padrão: {e}")
        return (DEFAULT_DRIVE_PATH, "", 85, 75, 90, True, f"Erro: {e}")


def restore_last_session():
    """Restaura a última sessão salva no Google Drive.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    try:
        last = _session.restore_last_session()
        date = last.get("date", "N/A")
        cached = last.get("models_in_cache", [])
        ram = last.get("models_in_ram", [])

        if date is None:
            return "Nenhuma sessão anterior encontrada."

        msg = (
            f"Sessão restaurada de {date}.\n"
            f"Modelos em cache: {len(cached)} | "
            f"Modelos em RAM: {len(ram)}"
        )
        _session.log_event("success", msg)
        return msg
    except Exception as e:
        _session.log_event("error", f"Erro ao restaurar sessão: {e}")
        return f"Erro: {e}"


def save_log():
    """Salva o log da sessão atual no Google Drive.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    try:
        success, message, path = _session.save_log()
        if success:
            _session.log_event("success", f"Log salvo: {path}")
        return message
    except Exception as e:
        return f"Erro ao salvar log: {e}"


def clear_log():
    """Limpa o log da sessão atual.

    Returns:
        Tuple com texto vazio e mensagem de confirmação.
    """
    _init_managers()

    _session._session_log.clear()
    _session.log_event("info", "Log limpo pelo usuário.")
    return _session.get_session_log_text(), "Log limpo com sucesso."


def refresh_log():
    """Atualiza a exibição do log.

    Returns:
        Texto formatado do log.
    """
    _init_managers()
    return _session.get_session_log_text()


def _get_config_values():
    """Retorna os valores atuais da configuração para preencher a UI.

    Returns:
        Tuple com drive_path, api_key, vram, ram, disk, auto_preload.
    """
    _init_managers()
    config = _session._get_config()
    thresholds = config.get("thresholds", {})
    return (
        config.get("drive_path", DEFAULT_DRIVE_PATH),
        config.get("civitai_api_key", ""),
        thresholds.get("vram_percent", 85),
        thresholds.get("ram_percent", 75),
        thresholds.get("disk_percent", 90),
        config.get("auto_preload_ram", True),
    )


def _extract_selected_filename(data):
    """Extrai o nome do arquivo do primeiro modelo selecionado na tabela.

    Args:
        data: Dados da tabela (lista de listas ou DataFrame).

    Returns:
        Nome do arquivo selecionado ou string vazia.
    """
    if data is None:
        return ""
    try:
        if hasattr(data, "values"):
            rows = data.values.tolist()
        elif isinstance(data, list):
            rows = data
        else:
            return ""
        for row in rows:
            if isinstance(row, list) and len(row) >= 2 and row[0]:
                return str(row[1])
    except Exception:
        pass
    return ""


def download_url_to_drive(model_type, url_str, filename):
    """Baixa modelo via URL diretamente para o Google Drive.

    Args:
        model_type: Tipo do modelo (checkpoint, lora, vae, text_encoder).
        url_str: URL do download.
        filename: Nome do arquivo a salvar.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    if not url_str or not filename:
        return "URL ou nome do arquivo vazio."

    try:
        chave = _session.get_api_key()
        if chave and "civitai" in url_str.lower():
            sep = "&" if "?" in url_str else "?"
            url_str = f"{url_str}{sep}token={chave}"

        dest_dir = os.path.join(
            _session.drive_path, DRIVE_DIRS[model_type]
        )
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, filename)

        import subprocess
        result = subprocess.run(
            ["wget", "-q", "--show-progress", "-O", dest, url_str],
            timeout=1800,
        )

        if result.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 50000:
            size_mb = os.path.getsize(dest) / (1024 ** 2)
            _session.log_event("success", f"Download concluído: {filename} ({size_mb:.1f} MB)")
            _session.set_selected_model(model_type, filename)
            return f"✅ '{filename}' baixado para o Drive ({size_mb:.1f} MB). Use 📥 Cache para acelerar."
        else:
            if os.path.exists(dest):
                os.remove(dest)
            _session.log_event("error", f"Download falhou: {filename}")
            return f"❌ Erro no download de '{filename}'. Verifique a URL."
    except Exception as e:
        _session.log_event("error", f"Erro no download: {e}")
        return f"❌ Erro: {e}"


def save_cache_to_drive():
    """Copia todos os modelos do cache local de volta para o Google Drive.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    try:
        copied = 0
        for model_type, cache_dir in _cache.CACHE_DIRS.items():
            drive_dir = _cache.DRIVE_DIRS[model_type]
            cache_path = os.path.join(_cache.cache_path, cache_dir)
            drive_path = os.path.join(_cache.drive_path, drive_dir)

            if not os.path.isdir(cache_path):
                continue

            for fname in sorted(os.listdir(cache_path)):
                src = os.path.join(cache_path, fname)
                if not os.path.isfile(src):
                    continue
                dst = os.path.join(drive_path, fname)
                if os.path.exists(dst):
                    continue
                import shutil
                shutil.copy2(src, dst)
                copied += 1

        _session.log_event("success", f"Cache salvo no Drive: {copied} arquivo(s)")
        return f"✅ {copied} modelo(s) copiado(s) do cache para o Drive."
    except Exception as e:
        _session.log_event("error", f"Erro ao salvar cache: {e}")
        return f"❌ Erro: {e}"


def save_images_to_drive():
    """Copia imagens geradas para o Google Drive.

    Returns:
        Mensagem de resultado.
    """
    _init_managers()
    try:
        _bridge.backup_outputs_to_drive()
        _session.log_event("success", "Imagens copiadas para o Drive")
        return "✅ Imagens copiadas para o Drive com sucesso!"
    except Exception as e:
        _session.log_event("error", f"Erro ao salvar imagens: {e}")
        return f"❌ Erro: {e}"


def upload_file_to_drive(model_type, file_obj):
    """Envia arquivo do PC para o Google Drive.

    Args:
        model_type: Tipo do modelo.
        file_obj: Objeto de arquivo do Gradio (dict com name e data).

    Returns:
        Mensagem de resultado.
    """
    _init_managers()

    if file_obj is None:
        return "Nenhum arquivo selecionado."

    try:
        if isinstance(file_obj, dict):
            filename = file_obj.get("name", "uploaded_model.safetensors")
            data = file_obj.get("data")
            if data is None:
                data = file_obj.get("content")
        else:
            return "Formato de arquivo não suportado."

        dest_dir = os.path.join(_session.drive_path, DRIVE_DIRS[model_type])
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, filename)

        if isinstance(data, str):
            import base64
            data = base64.b64decode(data)

        if isinstance(data, bytes):
            with open(dest, "wb") as f:
                f.write(data)
        else:
            import shutil
            shutil.copy2(data, dest)

        size_mb = os.path.getsize(dest) / (1024 ** 2)
        _session.log_event("success", f"Upload concluído: {filename} ({size_mb:.1f} MB)")
        _session.set_selected_model(model_type, filename)
        return f"✅ '{filename}' enviado para o Drive ({size_mb:.1f} MB)."
    except Exception as e:
        _session.log_event("error", f"Erro no upload: {e}")
        return f"❌ Erro: {e}"


def on_ui_tabs():
    """Registra a aba Cache Manager no Forge WebUI.

    Returns:
        Lista com tupla (componente, nome_aba, id_aba).
    """
    with gr.Blocks(analytics_enabled=False) as cache_manager_tab:
        gr.Markdown("## 💾 Cache Manager - Gerenciador de Modelos")

        with gr.Row():
            with gr.Column(scale=3):
                vram_bar = gr.Textbox(label="VRAM", interactive=False, max_lines=1)
                vram_progress = gr.Slider(
                    minimum=0, maximum=100, value=0, interactive=False,
                    label="VRAM %",
                )
            with gr.Column(scale=3):
                ram_bar = gr.Textbox(label="RAM", interactive=False, max_lines=1)
                ram_progress = gr.Slider(
                    minimum=0, maximum=100, value=0, interactive=False,
                    label="RAM %",
                )
            with gr.Column(scale=3):
                disk_bar = gr.Textbox(label="Disco", interactive=False, max_lines=1)
                disk_progress = gr.Slider(
                    minimum=0, maximum=100, value=0, interactive=False,
                    label="Disco %",
                )

        hw_info = gr.Textbox(label="Hardware", interactive=False, max_lines=1)
        refresh_btn = gr.Button("🔄 Atualizar Recursos", variant="secondary")

        with gr.Accordion("⚙️ Configurações", open=False):
            drive_path_input = gr.Textbox(
                label="Caminho do Drive",
                value=DEFAULT_DRIVE_PATH,
                max_lines=1,
            )
            api_key_input = gr.Textbox(
                label="CivitAI API Key",
                type="password",
                max_lines=1,
            )
            with gr.Row():
                vram_threshold = gr.Slider(
                    minimum=50, maximum=100, value=85, step=1,
                    label="Limite VRAM (%)",
                )
                ram_threshold = gr.Slider(
                    minimum=50, maximum=100, value=75, step=1,
                    label="Limite RAM (%)",
                )
                disk_threshold = gr.Slider(
                    minimum=50, maximum=100, value=90, step=1,
                    label="Limite Disco (%)",
                )
            auto_preload = gr.Checkbox(
                label="Auto-preload RAM",
                value=True,
            )
            with gr.Row():
                save_config_btn = gr.Button("💾 Salvar Config", variant="primary")
                restore_default_btn = gr.Button("🔄 Restaurar Padrão", variant="secondary")
                restore_session_btn = gr.Button("📋 Restaurar Última Sessão", variant="secondary")
            config_status = gr.Textbox(label="Status", interactive=False, max_lines=1)

        with gr.Accordion("📥 Download por URL (Drive)", open=False):
            with gr.Row():
                dl_type = gr.Dropdown(
                    choices=MODEL_TYPES,
                    label="Tipo",
                    value="checkpoint",
                    scale=1,
                )
                dl_url = gr.Textbox(
                    label="URL do modelo",
                    placeholder="https://civitai.com/... ou https://huggingface.co/...",
                    scale=3,
                )
                dl_name = gr.Textbox(
                    label="Nome do arquivo",
                    placeholder="modelo.safetensors",
                    scale=2,
                )
            with gr.Row():
                dl_btn = gr.Button("⬇️ Baixar para o Drive", variant="primary")
                dl_status = gr.Textbox(label="Status", interactive=False, max_lines=1)

        with gr.Accordion("📤 Upload do PC para o Drive", open=False):
            with gr.Row():
                up_type = gr.Dropdown(
                    choices=MODEL_TYPES,
                    label="Tipo",
                    value="checkpoint",
                    scale=1,
                )
                up_file = gr.File(
                    label="Selecione o arquivo",
                    file_count="single",
                    scale=3,
                )
                up_btn = gr.Button("📤 Enviar para o Drive", variant="primary", scale=1)
            up_status = gr.Textbox(label="Status", interactive=False, max_lines=1)

        model_tables = {}
        model_file_inputs = {}
        model_type_dropdowns = {}

        with gr.Tabs(visible=True):
            for model_type in MODEL_TYPES:
                label = MODEL_TYPE_LABELS[model_type]
                with gr.Tab(label, interactive=True, visible=True):
                    table = gr.Dataframe(
                        headers=[
                            "Selecionado", "Modelo", "Tamanho",
                            "Drive", "Disco", "RAM", "VRAM", "Ações",
                        ],
                        datatype=["bool", "str", "str", "str", "str", "str", "str", "str"],
                        interactive=True,
                        wrap=True,
                        row_count=(0, "dynamic"),
                    )
                    model_tables[model_type] = table

                    with gr.Row():
                        file_input = gr.Textbox(
                            label="Arquivo selecionado",
                            interactive=True,
                            max_lines=1,
                            visible=False,
                        )
                        model_file_inputs[model_type] = file_input

                    with gr.Row():
                        cache_btn = gr.Button("📥 Cache", variant="secondary", scale=1)
                        ram_btn = gr.Button("🧠 RAM", variant="secondary", scale=1)
                        vram_btn = gr.Button("🎯 VRAM", variant="primary", scale=1)
                        rm_disk_btn = gr.Button("🗑️ Disco", variant="stop", scale=1)
                        rm_ram_btn = gr.Button("🗑️ RAM", variant="stop", scale=1)

                    action_status = gr.Textbox(
                        label="Status da Ação", interactive=False, max_lines=1,
                    )

                    def _make_cache_handler(mt):
                        def handler(data):
                            fn = _extract_selected_filename(data)
                            if not fn:
                                return "Selecione um modelo na tabela."
                            return copy_model_to_cache(mt, fn)
                        return handler

                    def _make_ram_handler(mt):
                        def handler(data):
                            fn = _extract_selected_filename(data)
                            if not fn:
                                return "Selecione um modelo na tabela."
                            return preload_model_to_ram(mt, fn)
                        return handler

                    def _make_vram_handler(mt):
                        def handler(data):
                            fn = _extract_selected_filename(data)
                            if not fn:
                                return "Selecione um modelo na tabela."
                            return set_model_active(mt, fn)
                        return handler

                    def _make_rm_disk_handler(mt):
                        def handler(data):
                            fn = _extract_selected_filename(data)
                            if not fn:
                                return "Selecione um modelo na tabela."
                            return remove_from_disk(mt, fn)
                        return handler

                    def _make_rm_ram_handler():
                        def handler(data):
                            fn = _extract_selected_filename(data)
                            if not fn:
                                return "Selecione um modelo na tabela."
                            return remove_from_ram(fn)
                        return handler

                    cache_btn.click(
                        _make_cache_handler(model_type),
                        inputs=[table],
                        outputs=[action_status],
                    )
                    ram_btn.click(
                        _make_ram_handler(model_type),
                        inputs=[table],
                        outputs=[action_status],
                    )
                    vram_btn.click(
                        _make_vram_handler(model_type),
                        inputs=[table],
                        outputs=[action_status],
                    )
                    rm_disk_btn.click(
                        _make_rm_disk_handler(model_type),
                        inputs=[table],
                        outputs=[action_status],
                    )
                    rm_ram_btn.click(
                        _make_rm_ram_handler(),
                        inputs=[table],
                        outputs=[action_status],
                    )

        with gr.Row():
            sync_btn = gr.Button("📥 Sincronizar Selecionados", variant="primary", scale=2)
            copy_all_btn = gr.Button("📥 Copiar Tudo", variant="secondary", scale=1)
            clear_cache_btn = gr.Button("🗑️ Limpar Cache", variant="stop", scale=1)
            clear_type = gr.Dropdown(
                choices=["all"] + MODEL_TYPES,
                value="all",
                label="Tipo para limpar",
                scale=1,
            )
        bulk_status = gr.Textbox(label="Status", interactive=False, max_lines=1)

        with gr.Row():
            save_cache_btn = gr.Button("💾 Salvar Cache → Drive", variant="secondary", scale=2)
            save_images_btn = gr.Button("📤 Salvar Imagens no Drive", variant="secondary", scale=2)
        save_bulk_status = gr.Textbox(label="Status", interactive=False, max_lines=1)

        with gr.Accordion("📋 Log da Sessão", open=True):
            log_display = gr.Textbox(
                label="Log",
                interactive=False,
                lines=10,
                max_lines=20,
            )
            with gr.Row():
                refresh_log_btn = gr.Button("🔄 Atualizar Log", variant="secondary")
                save_log_btn = gr.Button("💾 Salvar Log no Drive", variant="secondary")
                clear_log_btn = gr.Button("🧹 Limpar Log", variant="secondary")
            log_status = gr.Textbox(label="Status do Log", interactive=False, max_lines=1)

        all_outputs = [
            vram_bar, ram_bar, disk_bar, hw_info,
            vram_progress, ram_progress, disk_progress,
            model_tables["checkpoint"],
            model_tables["lora"],
            model_tables["vae"],
            model_tables["text_encoder"],
            log_display,
        ]

        def on_refresh_all():
            try:
                results = refresh_all()
                return results
            except Exception as e:
                empty_row = [["—"] * 8]
                return (
                    [f"❌ Erro: {e}"] * 4
                    + [0, 0, 0]
                    + [empty_row] * 4
                    + [f"❌ Erro ao atualizar: {e}"]
                )

        refresh_btn.click(
            on_refresh_all,
            inputs=[],
            outputs=all_outputs,
        )

        sync_btn.click(
            sync_selected,
            inputs=[
                model_tables["checkpoint"],
                model_tables["lora"],
                model_tables["vae"],
                model_tables["text_encoder"],
            ],
            outputs=[bulk_status],
        )

        copy_all_btn.click(
            copy_all,
            inputs=[],
            outputs=[bulk_status],
        )

        clear_cache_btn.click(
            clear_cache,
            inputs=[clear_type],
            outputs=[bulk_status],
        )

        dl_btn.click(
            download_url_to_drive,
            inputs=[dl_type, dl_url, dl_name],
            outputs=[dl_status],
        )

        up_btn.click(
            upload_file_to_drive,
            inputs=[up_type, up_file],
            outputs=[up_status],
        )

        save_cache_btn.click(
            save_cache_to_drive,
            inputs=[],
            outputs=[save_bulk_status],
        )

        save_images_btn.click(
            save_images_to_drive,
            inputs=[],
            outputs=[save_bulk_status],
        )

        save_config_btn.click(
            save_config,
            inputs=[
                drive_path_input, api_key_input,
                vram_threshold, ram_threshold, disk_threshold,
                auto_preload,
            ],
            outputs=[config_status],
        )

        def on_restore_defaults():
            results = restore_defaults()
            return results

        restore_default_btn.click(
            on_restore_defaults,
            inputs=[],
            outputs=[
                drive_path_input, api_key_input,
                vram_threshold, ram_threshold, disk_threshold,
                auto_preload, config_status,
            ],
        )

        restore_session_btn.click(
            restore_last_session,
            inputs=[],
            outputs=[config_status],
        )

        refresh_log_btn.click(
            refresh_log,
            inputs=[],
            outputs=[log_display],
        )

        save_log_btn.click(
            save_log,
            inputs=[],
            outputs=[log_status],
        )

        def on_clear_log():
            text, msg = clear_log()
            return text, msg

        clear_log_btn.click(
            on_clear_log,
            inputs=[],
            outputs=[log_display, log_status],
        )

        def on_tab_load():
            empty_row = [["—"] * 8]
            safe_defaults = (
                ["Carregando..."] * 4
                + [0, 0, 0]
                + [empty_row] * 4
                + ["Inicializando..."]
                + [DEFAULT_DRIVE_PATH, "", 85, 75, 90, True]
            )
            try:
                results = refresh_all()
                config_vals = list(_get_config_values())
                return list(results) + config_vals
            except Exception as e:
                safe_defaults = list(safe_defaults)
                safe_defaults[0] = f"❌ Erro ao carregar: {e}"
                return safe_defaults

        cache_manager_tab.load(
            on_tab_load,
            inputs=[],
            outputs=all_outputs + [
                drive_path_input, api_key_input,
                vram_threshold, ram_threshold, disk_threshold,
                auto_preload,
            ],
        )

    return [(cache_manager_tab, "💾 Cache Manager", "cache_manager_tab")]


script_callbacks.on_ui_tabs(on_ui_tabs)
