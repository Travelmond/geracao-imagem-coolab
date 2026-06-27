# Fluxo de Execução — V4

Documentação completa de cada célula do notebook `DiffusionUI.ipynb` V4.

---

## Visão Geral das Células

| Ordem | Célula | Propósito | Obrigatória? |
|-------|--------|-----------|-------------|
| 0 | Upload cache-manager.zip | Envia extensão para o Drive | Sim |
| 0.5 | Upload ReActor.zip | Envia face swap para o Drive | Não |
| 1 | Drive + Pastas | Conecta Drive, cria estrutura | Sim |
| 2 | Forge + Python 3.10 | Instala Forge, symlinks | Sim |
| 3 | Vacinas | Corrige incompatibilidades | Sim |
| 4 | Extensões | Copia cache-manager, ReActor, civbrowser | Sim |
| 4.2 | Reaplicar Vacinas | Corrige versões sobrescritas | Sim |
| 4.5 | Download URL | Baixa modelos por URL | Não |
| 4.6 | Upload PC | Envia modelos do PC | Não |
| 5 | Verificação | Checklist de configuração | Sim |
| 6 | Iniciar Forge | Lança com link público | Sim |

---

## Célula 0: Upload cache-manager.zip

**Propósito:** Enviar a extensão cache-manager para o Google Drive.

```python
from google.colab import files
import zipfile, os, shutil

# Upload do ZIP
uploaded = files.upload()

# Extrai para o Drive
dest = '/content/drive/MyDrive/Stable_Diffusion_Dados/cache-manager'
shutil.copytree(zip_path, dest)

# Verifica arquivos essenciais
required = ['install.py', 'scripts/tab_ui.py', 'scripts/cache_manager.py', ...]
```

**Saída esperada:**
```
📦 cache-manager.zip recebido (45.2 KB)
📂 Extraindo arquivos...
🔍 Verificando arquivos essenciais:
   ✅ install.py
   ✅ scripts/tab_ui.py
   ✅ scripts/cache_manager.py
   ...
✅ cache-manager instalado no Drive com sucesso!
```

---

## Célula 0.5: Upload ReActor.zip (Opcional)

**Propósito:** Enviar a extensão ReActor (face swap) para o Google Drive.

Mesma lógica da Célula 0, mas para `sd-webui-reactor/`.

**Arquivos verificados:** `install.py`, `scripts/`, `reactor_modules/`, `reactor_ui/`

---

## Célula 1: Conexão com o Google Drive

**Propósito:** Conectar ao Drive e criar toda a estrutura de pastas.

```python
drive.mount('/content/drive', force_remount=True)

drive_path = '/content/drive/MyDrive/Stable_Diffusion_Dados'
drive_folders = ['Modelos_Base', 'LoRAs', 'VAEs', 'Text_Encoders', 'Imagens_Geradas', 'logs']
cache_folders = ['/content/cache/checkpoints', '/content/cache/loras', ...]
```

**Pastas criadas:**
- Drive: `Modelos_Base/`, `LoRAs/`, `VAEs/`, `Text_Encoders/`, `Imagens_Geradas/`, `logs/`
- Cache local: `checkpoints/`, `loras/`, `vaes/`, `text_encoders/`
- Outputs: `/content/outputs_temp`

---

## Célula 2: Instalação do Forge

**Propósito:** Instalar Python 3.10, clonar o Forge e criar symlinks.

```python
# Python 3.10
!add-apt-repository ppa:deadsnakes/ppa -y
!apt-get install -y python3.10 python3.10-venv python3.10-distutils
!curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

# Clone Forge
!git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git

# Symlinks
symlinks = {
    'models/Stable-diffusion': '/content/cache/checkpoints',
    'models/Lora': '/content/cache/loras',
    'models/VAE': '/content/cache/vaes',
    'models/text_encoder': '/content/cache/text_encoders',
    'outputs': '/content/outputs_temp'
}
```

**Mapa de Symlinks:**
| Forge Path | Aponta para |
|-----------|-------------|
| `models/Stable-diffusion` | `/content/cache/checkpoints` |
| `models/Lora` | `/content/cache/loras` |
| `models/VAE` | `/content/cache/vaes` |
| `models/text_encoder` | `/content/cache/text_encoders` |
| `outputs` | `/content/outputs_temp` |

---

## Célula 3: Vacinas

**Propósito:** Corrigir incompatibilidades de bibliotecas.

```python
# CLIP
!python3.10 -m pip install ftfy regex tqdm
!python3.10 -m pip install https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip --no-build-isolation

# NumPy
!python3.10 -m pip install 'numpy<2.1.0' --force-reinstall

# Bitsandbytes
!python3.10 -m pip install bitsandbytes==0.43.3

# Insightface
!python3.10 -m pip install opencv-python-headless
!python3.10 -m pip install insightface joblib

# PIP_CONSTRAINT
with open('/tmp/pip_constraints.txt', 'w') as f:
    f.write('numpy<2.1.0\n')
os.environ['PIP_CONSTRAINT'] = '/tmp/pip_constraints.txt'
```

**Verificação via subprocess:**
```python
r = subprocess.run(['python3.10', '-c', 'import clip; print("OK")'], capture_output=True, text=True)
```

---

## Célula 4: Instalar Extensões

**Propósito:** Copiar extensões do Drive para o Forge.

```python
# cache-manager
shutil.copytree(f'{drive_path}/cache-manager', f'{ext_path}/cache-manager')

# ReActor (se existir)
if os.path.exists(f'{drive_path}/sd-webui-reactor'):
    shutil.copytree(f'{drive_path}/sd-webui-reactor', f'{ext_path}/sd-webui-reactor')

# CivitAI Browser+
!git clone https://github.com/SignalFlagZ/sd-webui-civbrowser.git {ext_path}/sd-webui-civbrowser
```

---

## Célula 4.2: Reaplicar Vacinas

**Propósito:** Corrigir versões que as extensões sobrescreveram durante o startup.

```python
!python3.10 -m pip install 'numpy<2.1.0' 'scikit-image<0.23.0' 'scipy<2.0.0' 'opencv-python-headless' --force-reinstall -q
```

**Por que é necessária:**
As extensões (civbrowser, ReActor) rodam `install.py` durante o startup do Forge, que pode sobrescrever versões críticas. A Célula 4.2 reaplica as versões corretas **depois** das extensões.

---

## Célula 4.5: Download por URL

**Propósito:** Baixar modelos do Civitai/HuggingFace diretamente para o Drive.

```python
# Injetar API Key do Civitai
if chave and 'civitai' in url.lower():
    sep = '&' if '?' in url else '?'
    url = f'{url}{sep}token={chave}'

# Download
subprocess.run(['wget', '-q', '--show-progress', '-O', destino, url])
```

---

## Célula 4.6: Upload do PC

**Propósito:** Enviar modelos do computador para o Drive.

```python
from google.colab import files
arquivos = files.upload()
for nome, conteudo in arquivos.items():
    with open(f'{destino}/{nome}', 'wb') as f:
        f.write(conteudo)
```

---

## Célula 5: Verificação Final

**Propósito:** Checklist de configuração com 23 verificações.

```python
checks = [
    ('Google Drive montado', os.path.ismount('/content/drive')),
    ('Drive/Modelos_Base', os.path.isdir(f'{drive_path}/Modelos_Base')),
    ...
    ('Symlink: Stable-diffusion', os.path.islink(link) and ...),
    ('Extensão cache-manager', os.path.isdir(ext_cache) and ...),
    ('Forge launch.py', os.path.exists(f'{forge_dir}/launch.py')),
    ('Python 3.10', '3.10' in version),
]
```

---

## Célula 6: Iniciar Forge

**Propósito:** Lançar o Forge com link público Gradio.

```python
os.environ['MPLBACKEND'] = 'agg'
%cd /content/stable-diffusion-webui-forge
!python3.10 launch.py --share --enable-insecure-extension-access --theme dark
```

---

## Voltar para o índice

[← Arquitetura](./01-arquitetura.md) | [Interface de Widgets →](./03-interface-widgets.md)
