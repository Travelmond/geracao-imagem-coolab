# 🤖 AI Assistant Context & Guidelines
**System Prompt / Contexto Crítico para IAs e LLMs**

> [!WARNING]
> **Atenção IA Assistente**: Se você estiver lendo este arquivo para ajudar o usuário com este projeto no Google Colab, leia e compreenda **TODAS** as regras abaixo antes de sugerir qualquer comando de instalação (`pip install`), alteração de versão ou refatoração. O Google Colab possui bibliotecas pré-instaladas altamente instáveis, e este projeto possui uma arquitetura inviolável ("EnvironmentDoctor") especificamente desenhada para sobreviver a essas mutações.

## 1. O Problema (Por que o projeto é assim?)
O **Stable Diffusion WebUI Forge** requer dependências sensíveis e específicas. O Google Colab atualiza constantemente suas bibliotecas base (Python, PyTorch, NumPy). Quando o Colab atualiza o NumPy para `>=2.1.0`, ele quebra a interface ABI C++ de bibliotecas como `scikit-image`, `scipy` e `insightface`.
Se um simples `pip install pacote-aleatorio` for executado, o pip pode tentar atualizar silenciosamente o NumPy, quebrando todo o ambiente de forma irreparável e exigindo um factory reset da VM.

## 2. A Solução (A Arquitetura `EnvironmentDoctor`)
Não instalamos dependências aleatoriamente no Notebook. Existe um sistema de auto-cura (Auto-Healing) executado antes da WebUI:

1. **`lib/version_pins.py`**: A **ÚNICA** fonte de verdade (Single Source of Truth) para versões. Nunca escreva versões diretamente em scripts bash no notebook. Se precisar mudar uma versão, mude neste arquivo.
2. **`lib/auto_healer.py`**: Roda 14 vacinas (checks e correções) que forçam a instalação da versão exata registrada no `version_pins.py`.
3. **`PIP_CONSTRAINT` Global**: Um arquivo de restrição (`/tmp/pip_constraints_sd.txt`) é gerado e injetado via variável de ambiente. Ele força que **qualquer** chamada futura de `pip install` (feita por extensões, pelo ReActor, etc) nunca instale versões proibidas do numpy, scipy, etc.

## 3. Matriz de Versões Críticas Obrigatórias
*(Baseado em `lib/version_pins.py`)*

Se você, IA, for sugerir a instalação de um novo plugin ou biblioteca, garanta que suas dependências não violem esta matriz:

| Framework / Biblioteca | Versão Obrigatória / Pin | Motivo Estratégico |
| :--- | :--- | :--- |
| **Python** | `3.10.x` | O Forge quebra no Python 3.12 (padrão atual do Colab). Instalado via PPA deadsnakes. |
| **NumPy** | `<2.1.0` (ideal: `==1.26.4`) | **CRÍTICO**. Versões 2.1+ quebram a ABI (Application Binary Interface) C++ do Insightface e Scikit-Image. |
| **Scikit-Image** | `<0.23.0` | Versões novas exigem NumPy 2.x, causando quebra em cascata. |
| **SciPy** | `<2.0.0` | Versões novas exigem NumPy 2.x, causando quebra em cascata. |
| **Insightface** | `==0.7.3` | Usado pelo ReActor (Face Swap). A versão `0.7.3` requer pré-compilação com `libstdc++6` e NumPy `<2.1`. |
| **Onnxruntime-GPU** | Específica da CUDA | O ReActor tenta desinstalar o onnxruntime. Um patch (`lib/patches/reactor_colab.py`) impede isso. O `EnvironmentDoctor` detecta a versão da CUDA (11 ou 12) e instala a build respectiva. |
| **OpenAI CLIP** | *Build via source* | A partir do `setuptools >= 70`, a build do CLIP nativo quebra. Usamos `--no-build-isolation` ou nosso `clip_installer.py`. |

## 4. Regras de Ação para a IA (Strict Guidelines)

1. **NUNCA** sugira `!pip install [pacote]` diretamente no notebook sem usar a flag `--constraint /tmp/pip_constraints_sd.txt`.
2. **NUNCA** sugira atualizar o Python nativo do Colab alterando os symlinks globais do sistema operacional. O `auto_healer.py` isola o ambiente chamando explicitamente `python3.10`.
3. **SEMPRE** que o usuário relatar um "ImportError" em `skimage`, `cv2`, ou `insightface`, o diagnóstico número #1 que você deve fazer é verificar a versão instalada do NumPy.
4. **NÃO ADICIONE** clonagens `git clone` no código principal do notebook para extensões. Nós mantemos as extensões baixadas de forma persistente no Google Drive do usuário (`/extensoes/`) para não sofrermos com quebras se repositórios do Github sumirem (exemplo: `sd-webui-reactor`).
5. Se precisar adicionar uma nova regra de versão, adicione como uma nova `Vaccine` no arquivo `lib/auto_healer.py`.
