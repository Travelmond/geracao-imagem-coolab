"""
Patch: memory_management.py (CPU Mode)
=======================================

Este patch modifica o arquivo memory_management.py do Forge para permitir
execução em modo CPU quando nenhuma GPU está disponível.

O Forge verifica VRAM e se recusa a carregar modelos sem GPU.
Este patch "engana" o sistema fazendo-o pensar que tem 32 GB de VRAM.

Uso:
    from lib.patches.cpu_memory_patch import apply_cpu_memory_patch
    apply_cpu_memory_patch(forge_path)
"""

import os
from typing import Tuple


def apply_cpu_memory_patch(forge_path: str) -> Tuple[bool, str]:
    """
    Aplica o patch de memória para modo CPU no Forge.
    
    Args:
        forge_path: Caminho raiz do Forge (ex: /content/stable-diffusion-webui-forge)
    
    Returns:
        (sucesso, mensagem)
    """
    mem_file = os.path.join(forge_path, "backend", "memory_management.py")
    
    if not os.path.exists(mem_file):
        return False, f"❌ Arquivo não encontrado: {mem_file}"
    
    try:
        with open(mem_file, "r", encoding="utf-8") as f:
            code = f.read()
    except IOError as e:
        return False, f"❌ Erro ao ler {mem_file}: {e}"
    
    # Verificar se já foi patcheado
    if "DummyProp" in code:
        return True, "ℹ️ Patch CPU já aplicado anteriormente"
    
    # Definição do objeto fake GPU
    fake_gpu = (
        'type("DummyProp", (object,), {'
        '"total_memory": 32*1024*1024*1024, '
        '"major": 8, '
        '"minor": 0, '
        '"name": "CPU-Hacker-GPU"'
        '})()'
    )
    
    # Substituições
    replacements = [
        ("torch.cuda.current_device()", "'cpu'"),
        (
            "torch.cuda.get_device_properties(device).total_memory",
            "(32 * 1024 * 1024 * 1024)",
        ),
        ("torch.cuda.get_device_properties(device)", fake_gpu),
        ('torch.cuda.get_device_properties("cuda")', fake_gpu),
        (
            "torch.cuda.mem_get_info(device)",
            "((32 * 1024 * 1024 * 1024), (32 * 1024 * 1024 * 1024))",
        ),
    ]
    
    applied_count = 0
    for old, new in replacements:
        if old in code:
            code = code.replace(old, new)
            applied_count += 1
    
    if applied_count == 0:
        return True, "ℹ️ Nenhuma substituição necessária (código já compatível)"
    
    try:
        # Backup do original
        backup_path = mem_file + ".bak"
        if not os.path.exists(backup_path):
            with open(backup_path, "w", encoding="utf-8") as f_bak:
                with open(mem_file, "r", encoding="utf-8") as f_orig:
                    f_bak.write(f_orig.read())
        
        with open(mem_file, "w", encoding="utf-8") as f:
            f.write(code)
        
        return True, f"✅ Patch CPU aplicado ({applied_count} substituições)"
    except IOError as e:
        return False, f"❌ Erro ao escrever {mem_file}: {e}"


def revert_cpu_memory_patch(forge_path: str) -> Tuple[bool, str]:
    """
    Reverte o patch de CPU, restaurando o arquivo original.
    
    Args:
        forge_path: Caminho raiz do Forge
    
    Returns:
        (sucesso, mensagem)
    """
    mem_file = os.path.join(forge_path, "backend", "memory_management.py")
    backup_path = mem_file + ".bak"
    
    if not os.path.exists(backup_path):
        return False, "❌ Backup não encontrado — não é possível reverter"
    
    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            original = f.read()
        with open(mem_file, "w", encoding="utf-8") as f:
            f.write(original)
        return True, "✅ Patch CPU revertido — arquivo original restaurado"
    except IOError as e:
        return False, f"❌ Erro ao reverter: {e}"
