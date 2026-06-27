"""
Patch: reactor_colab.py
=======================

Este patch modifica o arquivo install.py do ReActor para 
prevenir que ele sobrescreva as dependências críticas (como onnxruntime).
"""

import os
from typing import Tuple


def apply_reactor_patch(reactor_path: str) -> Tuple[bool, str]:
    """
    Aplica o patch de instalação no ReActor.
    
    Args:
        reactor_path: Caminho raiz do ReActor
    
    Returns:
        (sucesso, mensagem)
    """
    install_file = os.path.join(reactor_path, "install.py")
    req_file = os.path.join(reactor_path, "requirements.txt")
    
    if not os.path.exists(install_file):
        return False, f"❌ Arquivo não encontrado: {install_file}"
        
    try:
        # Tocar o requirements.txt para remover versões estritas se existirem
        if os.path.exists(req_file):
            with open(req_file, "r") as f:
                lines = f.readlines()
            
            new_lines = []
            for line in lines:
                # Removemos as versões exatas para que o pip constraint controle
                if "onnxruntime-gpu" in line or "insightface" in line:
                    new_lines.append(line.split("==")[0] + "\n")
                else:
                    new_lines.append(line)
                    
            with open(req_file, "w") as f:
                f.writelines(new_lines)

        # Editar install.py
        with open(install_file, "r", encoding="utf-8") as f:
            code = f.read()
            
        # Adiciona proteção: o ReActor tenta desinstalar onnxruntime
        if "pip_uninstall(\"onnxruntime\", \"onnxruntime-gpu\")" in code:
            code = code.replace(
                "pip_uninstall(\"onnxruntime\", \"onnxruntime-gpu\")",
                "# Patched for Colab: pip_uninstall(\"onnxruntime\", \"onnxruntime-gpu\")"
            )
            
        with open(install_file, "w", encoding="utf-8") as f:
            f.write(code)
            
        return True, "✅ Patch ReActor aplicado com sucesso"
        
    except IOError as e:
        return False, f"❌ Erro ao aplicar patch no ReActor: {e}"
