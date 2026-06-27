"""
install.py
Instala dependências da extensão cache-manager e aplica patches necessários.
Executado automaticamente pelo Forge na inicialização.
"""

import launch
import os
import sys

DEPENDENCIES = [
    {"package": "psutil", "name": "psutil", "desc": "Monitoramento de RAM e CPU"},
]

def install_deps():
    """Instala dependências PIP."""
    for dep in DEPENDENCIES:
        if not launch.is_installed(dep["package"]):
            print(f"[cache-manager] Instalando {dep['name']} ({dep['desc']})...")
            launch.run_pip(
                f"install {dep['name']}",
                f"{dep['desc']} for cache-manager",
            )
        else:
            print(f"[cache-manager] {dep['name']} já instalado.")

def apply_patches():
    """Aplica patches se necessário."""
    try:
        import torch
        if not torch.cuda.is_available():
            print("[cache-manager] Modo CPU detectado. Aplicando patch de VRAM...")
            # Tenta importar o patcher da biblioteca compartilhada
            sys.path.insert(0, "/content")
            try:
                from lib.patches.cpu_memory_patch import apply_cpu_memory_patch
                forge_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                success, msg = apply_cpu_memory_patch(forge_root)
                print(f"[cache-manager] {msg}")
            except ImportError:
                print("[cache-manager] Patch de CPU indisponível (biblioteca não encontrada).")
    except ImportError:
        pass

def install():
    """Fluxo principal de instalação."""
    install_deps()
    apply_patches()

install()
