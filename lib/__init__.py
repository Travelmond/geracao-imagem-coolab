"""
__init__.py — Módulo lib
=========================

Pacote de bibliotecas auxiliares para o projeto geracao-imagem-coolab.

Módulos:
    - version_pins: Versões fixadas centralizadas
    - auto_healer: Sistema de diagnóstico e auto-correção (EnvironmentDoctor)
    - clip_installer: Instalador multi-estratégia do CLIP
"""

from . import version_pins

__all__ = ["version_pins"]
