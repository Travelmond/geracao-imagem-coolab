"""
install.py
Instala dependências da extensão cache-manager.
Executado automaticamente pelo Forge na inicialização.
"""

import launch

DEPENDENCIES = [
    {"package": "psutil", "name": "psutil", "desc": "Monitoramento de RAM e CPU"},
]


def install():
    """Instala todas as dependências necessárias."""
    for dep in DEPENDENCIES:
        if not launch.is_installed(dep["package"]):
            print(f"[cache-manager] Instalando {dep['name']} ({dep['desc']})...")
            launch.run_pip(
                f"install {dep['name']}",
                f"{dep['desc']} for cache-manager",
            )
            print(f"[cache-manager] {dep['name']} instalado com sucesso.")
        else:
            print(f"[cache-manager] {dep['name']} já instalado.")


install()
