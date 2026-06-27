# Arquitetura do Sistema

Visão geral de como o sistema é estruturado após a refatoração com a extensão `cache-manager`.

---

## Diagrama de Alto Nível

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GOOGLE COLAB                                  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              DiffusionUI_v2.ipynb (Notebook Simplificado)      │  │
│  │                                                                │  │
│  │  Célula 1: Drive + Pastas     Célula 2: Forge + Python 3.10   │  │
│  │  Célula 3: Vacinas            Célula 4: Extensões              │  │
│  │  Célula 5: Verificação        Célula 6: Launch                 │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              Stable Diffusion WebUI Forge                      │  │
│  │                                                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │  │
│  │  │  Interface    │  │  Motor       │  │  Extensões          │  │  │
│  │  │  (Gradio)     │  │  (PyTorch)   │  │  ├─ CivitAI Browser+│  │  │
│  │  │              │  │  + CUDA      │  │  ├─ ReActor          │  │  │
│  │  │  ┌─────────┐ │  │              │  │  └─ ⭐ cache-manager │  │  │
│  │  │  │💾 Cache │ │  │              │  │     (NOVA)           │  │  │
│  │  │  │ Manager │ │  │              │  │                     │  │  │
│  │  │  │  (ABA)  │ │  │              │  │                     │  │  │
│  │  │  └─────────┘ │  │              │  │                     │  │  │
│  │  └──────────────┘  └──────────────┘  └─────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│              symlinks        │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              /content/cache/ (Disco Local - RÁPIDO)             │  │
│  │  ┌──────────────┐ ┌────────┐ ┌──────┐ ┌───────────────┐      │  │
│  │  │ checkpoints  │ │ loras  │ │ vaes │ │ text_encoders │      │  │
│  │  └──────────────┘ └────────┘ └──────┘ └───────────────┘      │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│              copy/sync       │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              Google Drive (Persistente - 2TB)                   │  │
│  │  ┌──────────────┐ ┌────────┐ ┌──────┐ ┌───────────────┐      │  │
│  │  │ Modelos_Base │ │ LoRAs  │ │ VAEs │ │Text_Encoders  │      │  │
│  │  └──────────────┘ └────────┘ └──────┘ └───────────────┘      │  │
│  │  ┌──────────────────┐ ┌────────────────┐ ┌─────────────────┐  │  │
│  │  │ Imagens_Geradas  │ │ cache-manager/ │ │ .cache_config   │  │  │
│  │  └──────────────────┘ └────────────────┘ └─────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Hierarquia de Memória

```
┌─────────────────────────────────────────────────────────────┐
│                    HIERARQUIA DE MEMÓRIA                      │
│                                                              │
│  CAMADA 1: Google Drive (Persistente, ~2TB, LENTO)           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Stable_Diffusion_Dados/                                │  │
│  │   Modelos_Base/ LoRAs/ VAEs/ Text_Encoders/           │  │
│  └────────────────────────────────────────────────────────┘  │
│       │ Copiar para cache (1x por seleção do usuário)        │
│       ▼                                                      │
│  CAMADA 2: Disco Local Colab (Efêmero, ~100GB SSD, RÁPIDO)  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ /content/cache/                                        │  │
│  │   checkpoints/ loras/ vaes/ text_encoders/             │  │
│  └────────────────────────────────────────────────────────┘  │
│       │ Pré-carregar (opcional, via OS page cache)           │
│       ▼                                                      │
│  CAMADA 3: RAM (Efêmera, 12-52GB, MUITO RÁPIDO)             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Modelos carregados em memória Python                   │  │
│  │ OS page cache acelera leitura do disco                 │  │
│  └────────────────────────────────────────────────────────┘  │
│       │ Carregar para inferência (via Forge)                  │
│       ▼                                                      │
│  CAMADA 4: VRAM (Efêmera, 15-80GB, ULTRA RÁPIDO)            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Modelo ativo + LoRA ativo (para geração)               │  │
│  │ Gerenciado pelo Forge + monitor automático             │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes da Extensão cache-manager

```
cache-manager/
│
├── install.py                     ← Instala psutil
│
└── scripts/
    ├── hardware_detector.py       ← Detecta GPU, VRAM, RAM, Disco
    │   └── Classifica em: GPU_LUXO, GPU_MEDIA, GPU_ECONOMICA, CPU_TURBO
    │
    ├── session_manager.py         ← Config persistente (.cache_config.json)
    │   ├── Salva/carrega config do Drive
    │   ├── Gerencia seleção de modelos
    │   ├── Histórico de uso (LRU)
    │   └── Logs de sessão (JSON no Drive)
    │
    ├── cache_manager.py           ← Core: Drive → Disco → RAM
    │   ├── copy_to_cache() com progresso em tempo real
    │   ├── preload_to_ram()
    │   ├── remove_from_cache()
    │   └── Gerencia /content/cache/
    │
    ├── memory_monitor.py          ← Monitor background (thread daemon)
    │   ├── VRAM via torch.cuda
    │   ├── RAM via psutil
    │   ├── Disco via shutil
    │   └── Auto-evict se threshold ultrapassado
    │
    ├── forge_bridge.py            ← Integração com Forge
    │   ├── Symlinks: Forge → Cache
    │   ├── refresh_models()
    │   └── backup_outputs_to_drive()
    │
    └── tab_ui.py                  ← Aba Gradio no Forge
        ├── 📊 Recursos (VRAM, RAM, Disco)
        ├── ⚙️ Configurações
        ├── 📦 Modelos (por tipo, com status em cada camada)
        └── 📝 Log de atividades
```

---

## Fluxo de Dados

### Inicialização

```
Notebook executa células 1-6
       ↓
Drive montado + pastas criadas
       ↓
Forge clonado + Python 3.10 instalado
       ↓
Vacinas aplicadas (Numpy, CLIP, Insightface)
       ↓
cache-manager copiado do Drive → Forge/extensions/
       ↓
Forge lança com --share
       ↓
Extensão carrega automaticamente:
  1. hardware_detector → detecta hardware
  2. session_manager → carrega config do Drive
  3. cache_manager → cria /content/cache/
  4. forge_bridge → symlinks: Forge → Cache
  5. memory_monitor → inicia thread (10s)
  6. tab_ui → registra aba no Forge
```

### Operação

```
Usuário abre aba "💾 Cache Manager"
       ↓
Vê: recursos (VRAM, RAM, Disco) + modelos do Drive
       ↓
Seleciona modelo → [📥 Cache]
       ↓
cache_manager.copy_to_cache() com progresso
       ↓
Modelo em /content/cache/ (disco local rápido)
       ↓
[🧠 RAM] → preload_to_ram() (opcional)
       ↓
[🎯 VRAM] → Forge carrega modelo (via symlink)
       ↓
Monitor verifica thresholds:
  - VRAM > 85% → auto-evict para RAM
  - RAM > 75% → auto-evict para disco
  - Log: "⚠️ VRAM > 85%: Offload modelo X"
```

### Finalização

```
Usuário salva config → .cache_config.json no Drive
Usuário salva log → logs/session_YYYY-MM-DD.json no Drive
       ↓
Sessão encerra (Colab desconecta)
       ↓
Auto-copy: /content/outputs_temp/ → Drive/Imagens_Geradas/
Auto-save: config atualizado
       ↓
Cache local (efêmero) é perdido
Drive mantém: modelos, config, logs
```

---

## Integração com Forge

### Symlinks

```
Forge/models/Stable-diffusion → /content/cache/checkpoints
Forge/models/Lora            → /content/cache/loras
Forge/models/VAE             → /content/cache/vaes
Forge/models/text_encoder    → /content/cache/text_encoders
Forge/outputs                → /content/outputs_temp
```

### Quando usuário seleciona modelo na UI do Forge

```
1. Forge lê do symlink (que aponta para /content/cache/)
2. Modelo já está no disco local → acesso rápido
3. OS page cache pode manter em RAM → ainda mais rápido
4. Forge gerencia VRAM automaticamente
5. Monitor verifica e offload se necessário
```

---

## Voltar para o índice

[← README](./README.md) | [Fluxo de Execução →](./02-fluxo-de-execucao.md)
