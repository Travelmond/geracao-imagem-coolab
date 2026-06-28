# Documentação do Sistema — DiffusionUI V4

Sistema automatizado para geração de imagens por IA usando Stable Diffusion WebUI Forge no Google Colab, com gestão inteligente de cache e memória.

---

## O Que É Este Projeto?

Um notebook Jupyter (`DiffusionUI.ipynb`) + extensão Forge (`cache-manager`) que automatiza toda a configuração, execução e gestão de modelos do Stable Diffusion WebUI Forge no Google Colab.

### Funcionalidades

- **Geração de imagens** por IA usando GPUs gratuitas do Colab
- **Cache inteligente** de modelos: Google Drive → Disco Local → RAM → VRAM
- **Interface integrada** no Forge (aba "💾 Cache Manager") para gerenciar modelos
- **Monitoramento em tempo real** de VRAM, RAM e disco
- **Auto-evict** quando VRAM/RAM ficam cheios (>85% VRAM, >75% RAM)
- **Persistência** de configurações e logs entre sessões
- **Download/Upload** de modelos via URL ou PC local

---

## Como Executar

1. No seu computador, **compacte a pasta `cache-manager/` em um arquivo `.zip`**
2. Abra `DiffusionUI.ipynb` no Google Colab
3. Execute a **Célula 0** — faça upload do `cache-manager.zip`
4. Execute as demais células **em ordem** (1 → 2 → 3 → 4 → 4.2 → 4.5 → 4.6 → 5 → 6)
5. Na Célula 5, verifique se todos os itens estão com ✅
6. Na Célula 6, aguarde o link público (`.gradio.live`) e clique nele
7. Na interface do Forge, clique na aba **"💾 Cache Manager"**
8. Use **📥 Download por URL** para baixar modelos ou **📤 Upload do PC** para enviar
9. Selecione modelos → [📥 Cache] → [🧠 RAM] → [🎯 VRAM]

---

## Estrutura do Projeto

```
V4/
├── DiffusionUI.ipynb              ← Notebook principal (Google Colab)
│
├── cache-manager/                 ← Extensão Forge
│   ├── install.py                 ← Instala dependências (psutil)
│   └── scripts/
│       ├── hardware_detector.py   ← Detecção de GPU/RAM/Disco
│       ├── session_manager.py     ← Config persistente + logs
│       ├── cache_manager.py       ← Core: Drive→Disco→RAM com progresso
│       ├── memory_monitor.py      ← Thread de monitoramento (10s interval)
│       ├── forge_bridge.py        ← Symlinks + integração Forge
│       └── tab_ui.py              ← Interface Gradio no Forge
│
├── docker/                        ← Ambiente bolha local
│   ├── Dockerfile                 ← Imagem com CUDA 12.1 + Ubuntu 22.04
│   ├── docker-compose.yml         ← Orquestração com GPU
│   └── colab-simulator.sh         ← Script que simula o Colab
│
└── docs/                          ← Esta documentação
    ├── README.md                  ← Este arquivo
    ├── 01-arquitetura.md
    ├── 02-fluxo-de-execucao.md
    ├── 03-interface-widgets.md
    ├── 04-hardware-otimizacao.md
    ├── 05-modelos-e-pastas.md
    ├── 06-dependencias-e-patches.md
    ├── 07-extensoes.md
    ├── 08-versao-legada.md
    ├── 09-problemas-conhecidos.md
    ├── 10-glossario.md
    ├── 11-ambiente-local.md
    └── 14-estrategia-hibrida.md   ← NOVO: Estratégia A+B (AutoHealer v4.1.0)
```

---

## Fluxo do Sistema

```
Notebook (DiffusionUI.ipynb)
    │
    ├── Célula 0: Upload do cache-manager.zip → Drive
    ├── Célula 0.5: Upload do ReActor.zip → Drive (opcional)
    ├── Célula 1: Conecta Drive + cria pastas/cache
    ├── Célula 2: Instala Forge + Python 3.10 + symlinks
    ├── Célula 3: Vacinas (Numpy, CLIP, Insightface, bitsandbytes)
    ├── Célula 4: Copia extensões (cache-manager, ReActor, civbrowser)
    ├── Célula 4.2: Reaplica vacinas (pós-extensões)
    ├── Célula 4.5: Download por URL (opcional)
    ├── Célula 4.6: Upload do PC (opcional)
    ├── Célula 5: Verificação final (checklist)
    └── Célula 6: Lança Forge com link público Gradio
              │
              ▼
    Forge + Extensão cache-manager
              │
              ├── Aba "💾 Cache Manager" no Forge
              │   ├── 📊 Recursos (VRAM, RAM, Disco)
              │   ├── ⚙️ Configurações
              │   ├── 📦 Modelos (por tipo)
              │   └── 📝 Log
              │
              ├── Monitor background (10s interval)
              │   └── Auto-evict se VRAM > 85% ou RAM > 75%
              │
              └── Symlinks → /content/cache/ (disco local rápido)
```

---

## Tecnologias

| Tecnologia | Função |
|-----------|--------|
| Python 3.10 | Linguagem principal |
| PyTorch + CUDA | Framework de IA com aceleração GPU |
| Stable Diffusion WebUI Forge | Motor de geração de imagens |
| Gradio | Interface web do Forge + aba cache-manager |
| Google Drive | Armazenamento persistente (2TB+) |
| psutil | Monitoramento de RAM e CPU |
| CivitAI Browser+ | Gerenciamento de modelos via interface |
| ReActor | Face swap e consistência de personagens |

---

## Suporte de Hardware

| GPU | VRAM | RAM | Disco | Performance |
|-----|------|-----|-------|-------------|
| A100 | 40-80 GB | 52 GB | 200 GB | Máxima |
| L4 | 24 GB | 26 GB | 150 GB | Boa |
| T4 | 15 GB | 12 GB | 100 GB | Limitada |
| CPU | 0 GB | 12 GB | 100 GB | Muito lenta |

---

## Licença

Este projeto é para uso pessoal. O Stable Diffusion WebUI Forge é licenciado sob AGPL-3.0.
