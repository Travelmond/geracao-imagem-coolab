# Stable Diffusion WebUI Forge (Colab Optimized) — v3

Esta é a arquitetura refatorada, ultra-robusta e inviolável para execução do **Stable Diffusion WebUI Forge** no Google Colab, com integração completa do **Cache Manager** e **ReActor**.

## 🌟 O que mudou na v3?

A maior barreira no Google Colab são as atualizações silenciosas nas bibliotecas pré-instaladas (Python, PyTorch, NumPy), que frequentemente quebram dependências sensíveis como `scikit-image`, `insightface` e `onnxruntime`. 

Para resolver isso de forma definitiva, esta versão introduz o **EnvironmentDoctor** (Auto-Healer).

### 1. Sistema Auto-Healing (`lib/auto_healer.py`)
Um módulo com mais de 1.900 linhas que age como um "médico" para o Colab. Antes de iniciar a WebUI, ele aplica **14 vacinas** que:
1. Verificam a integridade da dependência.
2. Aplicam uma correção específica (instalação, downgrade, force-reinstall).
3. Verificam se a correção funcionou.
4. Aplicam uma estratégia de *fallback* agressiva caso a primeira falhe.

As proteções incluem:
- **`Python 3.10`**: Forçado via apt/deadsnakes (Colab hoje usa 3.12 por padrão, quebrando o Forge).
- **`NumPy < 2.1.0`**: Evita a quebra da ABI com C++ em `scikit-image` e `insightface`.
- **`CLIP OpenAI`**: Instalação customizada (via wheel local ou fallback) que sobrevive à mudança do `setuptools >= 70`.
- **Blindagem do PIP**: Usa variáveis globais `PIP_CONSTRAINT` para impedir que *qualquer* extensão atualize o NumPy acidentalmente durante a execução do Forge.

### 2. UI Premium (Cache Manager)
O `Cache Manager` recebeu um redesign completo com base na estética de Glassmorphism e Dark Mode:
- **`style.css`**: Design system com variáveis CSS, barras de recursos coloridas dinâmicas e transições suaves.
- **`cache_manager_ui.js`**: Sistema de toasts (notificações pop-up) e auto-refresh em background.

### 3. Notebook Seguro (`DiffusionUI_v3.ipynb`)
O novo Notebook foi reescrito para não baixar extensões instáveis na nuvem. Em vez disso:
- Toda a pasta `lib/` e `extensoes/` fica armazenada permanentemente no seu Google Drive.
- Cópias seguras, patchs no `install.py` do ReActor, e suporte total a CPU e GPU (T4/L4).
- Interface em ipywidgets embutida para download seguro de Modelos via Civitai API.

## 📂 Estrutura do Repositório

```text
/home/fabiano/Documents/Codigo/geracao-imagem-coolab/
├── DiffusionUI_v3.ipynb         # O Notebook principal (rode este no Colab)
├── README.md                    # Esta documentação
├── lib/
│   ├── auto_healer.py           # O "médico" do Colab (14 vacinas)
│   ├── clip_installer.py        # Resolvedor de builds quebradas do CLIP
│   ├── version_pins.py          # Arquivo central (Single Source of Truth) para versões
│   ├── pip_constraints.txt      # O arquivo de blindagem global (injetado via env var)
│   └── patches/
│       ├── cpu_memory_patch.py  # Força parâmetros de CPU quando a GPU T4 não for alocada
│       └── reactor_colab.py     # Impede que o ReActor quebre o onnxruntime
└── extensoes/
    ├── cache-manager/           # Nossa extensão customizada com UI nova
    ├── sd-webui-reactor/        # Face swap plugin (versão congelada segura)
    └── sd-webui-civbrowser/     # Navegador do Civitai embutido
```

## 🚀 Como Usar no Google Colab

1. Envie **toda esta pasta do repositório** para a raiz do seu Google Drive e renomeie para `Stable_Diffusion_Dados` (ou coloque o conteúdo nela).
2. Abra o arquivo `DiffusionUI_v3.ipynb` diretamente no Colab.
3. Se desejar downloads mais fáceis, preencha sua `CIVITAI_API_KEY` na **Célula 0**.
4. No topo, vá em `Runtime > Run all` (Ambiente de Execução > Executar tudo).
5. O `EnvironmentDoctor` analisará seu ambiente Colab, aplicará as vacinas em tempo real (exibindo um log detalhado), fará os *symlinks* do cache, e iniciará o Forge.
6. Clique no link `.gradio.live` ao final do processo.

## 🛠️ Modificando Versões

Se no futuro o Forge exigir uma nova versão de uma biblioteca:
Não altere o código do notebook! Modifique **APENAS** o arquivo `lib/version_pins.py`.
O sistema inteiro (inclusive o `PIP_CONSTRAINT`) lerá deste arquivo automaticamente, propagando a blindagem de versão por todas as dependências (inclusive as de terceiros).
