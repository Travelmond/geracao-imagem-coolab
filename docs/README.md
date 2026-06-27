# Documentação do Sistema — geracao-imagem-coolab

Sistema automatizado para geração de imagens por IA usando Stable Diffusion WebUI Forge no Google Colab, com gestão inteligente de cache e memória.

---

## O Que É Este Projeto?

Um notebook Jupyter (`DiffusionUI_v2.ipynb`) + extensão Forge (`cache-manager`) que automatiza toda a configuração, execução e gestão de modelos do Stable Diffusion WebUI Forge no Google Colab.

### Funcionalidades

- **Geração de imagens** por IA usando GPUs gratuitas do Colab
- **Cache inteligente** de modelos: Google Drive → Disco Local → RAM → VRAM
- **Interface integrada** no Forge (aba "💾 Cache Manager") para gerenciar modelos
- **Monitoramento em tempo real** de VRAM, RAM e disco
- **Persistência** de configurações e logs entre sessões
- **Auto-evict** quando VRAM/RAM ficam cheios

---

## Pré-Requisitos

- Conta Google (para Colab e Drive)
- Navegador web
- (Opcional) API Key do Civitai para downloads autenticados

---

## Como Executar

1. No seu computador, **compacte a pasta `cache-manager/` em um arquivo `.zip`**
2. Abra `DiffusionUI_v2.ipynb` no Google Colab
3. Execute a **Célula 0** — faça upload do `cache-manager.zip`
4. Execute as demais células **em ordem** (1 → 2 → 3 → 4 → 4.5 → 4.6 → 5 → 6)
4. Na Célula 5, verifique se todos os itens estão com ✅
5. Na Célula 6, aguarde o link público (`.gradio.live`) e clique nele
5. Na Célula 6, aguarde o link público (`.gradio.live`) e clique nele
6. Na interface do Forge, clique na aba **"💾 Cache Manager"**
7. Use **📥 Download por URL** para baixar modelos ou **📤 Upload do PC** para enviar
8. Selecione modelos → [📥 Cache] → [🧠 RAM] → [🎯 VRAM]

---

## Estrutura do Projeto

```
geracao-imagem-coolab/
│
├── DiffusionUI.ipynb              ← Notebook legado (referência)
├── DiffusionUI_v2.ipynb           ← Notebook principal (simplificado)
│
├── cache-manager/                 ← Extensão Forge (NOVA)
│   ├── install.py                 ← Instala dependências (psutil)
│   └── scripts/
│       ├── hardware_detector.py   ← Detecção de GPU/RAM/Disco
│       ├── session_manager.py     ← Config persistente + logs
│       ├── cache_manager.py       ← Core: Drive→Disco→RAM
│       ├── memory_monitor.py      ← Monitor background + auto-evict
│       ├── forge_bridge.py        ← Symlinks + integração Forge
│       └── tab_ui.py              ← Aba Gradio no Forge
│
└── docs/                          ← Documentação
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
    └── 10-glossario.md
```

**No Google Drive:**
```
Stable_Diffusion_Dados/
├── Modelos_Base/                  ← Checkpoints (persistente)
├── LoRAs/                         ← LoRAs (persistente)
├── VAEs/                          ← VAEs (persistente)
├── Text_Encoders/                 ← Text Encoders (persistente)
├── Imagens_Geradas/               ← Outputs (persistente)
├── logs/                          ← Logs de sessão (persistente)
├── .cache_config.json             ← Config persistente
└── cache-manager/                 ← Extensão (fonte, copiada para Forge)
```

**No Colab (efêmero):**
```
/content/
├── cache/                         ← Cache local rápido (efêmero)
│   ├── checkpoints/
│   ├── loras/
│   ├── vaes/
│   └── text_encoders/
├── outputs_temp/                  ← Outputs temporários (copiados ao final)
└── stable-diffusion-webui-forge/
    └── extensions/
        └── cache-manager/         ← Extensão (copiada do Drive)
```

---

## Hierarquia de Memória

```
CAMADA 1: Google Drive (Persistente, ~2TB, LENTO)
    │ Copiar para cache (1x por seleção)
    ▼
CAMADA 2: Disco Local Colab (Efêmero, ~100GB SSD, RÁPIDO)
    │ Pré-carregar (opcional)
    ▼
CAMADA 3: RAM (Efêmera, 12-52GB, MUITO RÁPIDO)
    │ Carregar para inferência
    ▼
CAMADA 4: VRAM (Efêmera, 15-80GB, ULTRA RÁPIDO)
    └── Modelo ativo + LoRA ativo
```

---

## Documentação

### Início Rápido

| Documento | Descrição |
|-----------|-----------|
| [Arquitetura](./01-arquitetura.md) | Visão geral do sistema, diagrama de componentes |
| [Fluxo de Execução](./02-fluxo-de-execucao.md) | Passo a passo de cada célula com código completo |

### Referência Técnica

| Documento | Descrição |
|-----------|-----------|
| [Interface de Widgets](./03-interface-widgets.md) | Documentação da UI: abas, botões, callbacks |
| [Hardware e Otimização](./04-hardware-otimizacao.md) | Detecção de GPU/CPU, argumentos adaptativos |
| [Modelos e Pastas](./05-modelos-e-pastas.md) | Tipos de modelos, estrutura de pastas, symlinks |
| [Dependências e Patches](./06-dependencias-e-patches.md) | Numpy, CLIP, Insightface, PIP_CONSTRAINT |
| [Extensões](./07-extensoes.md) | CivitAI Browser+, ReActor, cache-manager |

### Manutenção

| Documento | Descrição |
|-----------|-----------|
| [Versão Legada](./08-versao-legada.md) | Documentação da versão antiga |
| [Problemas Conhecidos](./09-problemas-conhecidos.md) | Erros comuns e soluções |
| [Glossário](./10-glossario.md) | Termos técnicos explicados |

---

## Fluxo do Sistema

```
Notebook (DiffusionUI_v2.ipynb)
    │
    ├── Célula 0: Upload do cache-manager.zip → Drive
    ├── Célula 1: Conecta Drive + cria pastas/cache
    ├── Célula 2: Instala Forge + Python 3.10 + symlinks → cache
    ├── Célula 3: Vacinas (Numpy, CLIP, Insightface) + libstdc++6 fix
    ├── Célula 4: Copia cache-manager do Drive → Forge/extensions/
    ├── Célula 4.5: Download de modelos por URL (wget + API Key)
    ├── Célula 4.6: Upload de modelos do PC (files.upload())
    ├── Célula 5: Verificação final (checklist)
    └── Célula 6: Launch Forge (--share)
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
| Google Drive | Armazenamento persistente (2TB) |
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
