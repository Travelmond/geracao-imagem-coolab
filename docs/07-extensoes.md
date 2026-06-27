# Extensões

Extensões instaladas automaticamente pelo notebook e como adicionar novas.

---

## Extensões Instaladas

### 1. cache-manager (NOVA)

**Localização:** `cache-manager/` (no repositório, copiada para Forge/extensions/)

**O que faz:**
- Aba "💾 Cache Manager" integrada na interface do Forge
- Gestão inteligente de cache: Google Drive → Disco Local → RAM → VRAM
- Cópia de modelos com barra de progresso em tempo real
- Monitoramento de VRAM, RAM e disco em background
- Auto-evict quando memória fica cheia (>85% VRAM, >75% RAM)
- Persistência de configurações entre sessões
- Logs de atividades salvos no Drive

**Módulos:**
- `hardware_detector.py` — Detecta GPU, VRAM, RAM, Disco
- `session_manager.py` — Config persistente + logs
- `cache_manager.py` — Core: Drive→Disco→RAM com progresso
- `memory_monitor.py` — Thread de monitoramento (10s interval)
- `forge_bridge.py` — Symlinks + integração Forge
- `tab_ui.py` — Interface Gradio no Forge

**Como usar:**
1. Abra a interface do Forge
2. Clique na aba "💾 Cache Manager"
3. **📥 Download por URL:** Cole URL do Civitai/HuggingFace e baixe direto para o Drive
4. **📤 Upload do PC:** Envie arquivos do seu computador para o Drive
5. Selecione modelos do Drive
6. Clique [📥 Cache] para copiar para disco local
7. Clique [🧠 RAM] para pré-carregar em RAM
8. Clique [🎯 VRAM] para definir como modelo ativo
9. **💾 Salvar Cache → Drive:** Persiste modelos do cache no Drive
10. **📤 Salvar Imagens no Drive:** Copia imagens geradas para o Drive

**Documentação completa:** Veja os docstrings dos módulos e o README principal.

---

### 2. sd-webui-civbrowser

**Repositório:** [github.com/SignalFlagZ/sd-webui-civbrowser](https://github.com/SignalFlagZ/sd-webui-civbrowser)

**O que faz:**
- Interface dentro do Forge para navegar o site Civitai
- Download direto de modelos (checkpoints, LoRAs, VAEs) sem sair da interface
- Visualização de previews e informações dos modelos
- Gerenciamento de downloads com Aria2

**Como usar:**
1. Abra a interface do Forge
2. Procure a aba "CivitAI Browser+" no menu
3. Navegue pelos modelos do Civitai
4. Clique em "Download" para baixar diretamente para o Drive (via symlink)

**Configuração:** A API Key do Civitai é necessária para downloads autenticados. Configure na aba "CivitAI Browser+" do Forge.

---

### 3. sd-webui-civbrowser

**Repositório:** [github.com/SignalFlagZ/sd-webui-civbrowser](https://github.com/SignalFlagZ/sd-webui-civbrowser)

**O que faz:**
- Navega, busca e baixa modelos do Civitai diretamente da interface do Forge
- Múltiplas abas de busca simultânea
- Fila de downloads com multi-threading
- Verificação de integridade via SHA256
- Suporte a API Key do Civitai
- Cards coloridos por tipo de modelo base
- Botão "enviar para txt2img" nas imagens de preview

**Dependências:**
- Nenhuma extra (além do insightface já instalado para face detection)

**Como usar:**
1. Abra a interface do Forge
2. Clique na aba "Civbrowser"
3. Pesquise modelos por palavra-chave, tag ou ID
4. Clique em "Download" para baixar diretamente

**Suporte:** A1111, Forge e SD.Next.

---

## Como Adicionar Novas Extensões

### Método 1: Editar o Notebook

Na célula das extensões, adicione a URL do repositório na lista:

```python
extensoes = [
    "https://github.com/SignalFlagZ/sd-webui-civbrowser",
    "https://github.com/NOVA-URL/NOVA-extensao"  # ← Nova extensão
]
```

### Método 2: Instalar Manualmente (Durante Sessão)

```bash
cd /content/stable-diffusion-webui-forge/extensions
git clone https://github.com/NOVA-URL/NOVA-extensao
```

**Nota:** Extensões instaladas manualmente são perdidas ao fechar a sessão. Para persistir, adicione ao notebook.

---

## Extensões Incluídas no Forge (Não Precisam Instalar)

O Forge já vem com extensões built-in:

| Extensão | Função |
|----------|--------|
| ControlNet | Guiar geração com imagens de referência |
| Lora | Carregar e aplicar LoRAs |
| Extra Networks | Gerenciar modelos na interface |
| Prompt Matrix | Gerar múltiplas variações de prompt |
| X/Y Plot | Comparar parâmetros em grade |

---

## Verificando Extensões Instaladas

Após o boot do Forge, as extensões aparecem nos logs:

```
sd-webui-civbrowser: Starting...
ControlNet - INFO - ControlNet UI callback registered.
```

Se uma extensão falhar ao carregar, o Forge exibe um erro mas continua funcionando.

---

## Voltar para o índice

[← Dependências e Patches](./06-dependencias-e-patches.md) | [Versão Legada →](./08-versao-legada.md)
