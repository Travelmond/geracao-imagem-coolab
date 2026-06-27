# Versão Legada (Células 1-6 Originais)

Documentação da versão original do notebook, localizada no **início** do arquivo. Esta versão foi substituída pela [versão melhorada](./02-fluxo-de-execucao.md), mas é mantida aqui para referência.

---

## Diferenças Principais

| Aspecto | Versão Legada | Versão Melhorada |
|---------|--------------|------------------|
| Localização | Início do notebook | Final do notebook |
| Detecção de Hardware | Célula separada (Célula 2) | Integrada na Célula 6 |
| Central de Downloads | 3 abas (Download, Upload, Gerenciar) | 2 abas (Download, Gerenciar) |
| Upload Nativo | Sim (aba separada com `files.upload()`) | Não |
| Extensões | Não incluídas | CivitAI Browser+ e ReActor |
| Autodiagnóstico | Não tem | Verifica PIP, CLIP, Numpy |
| Python | Usa o padrão do Colab | Força Python 3.10 |
| API Key | Placeholder sem exemplo | Placeholder com exemplo de chave |
| Civitai Detection | Verifica `if "civitai" in url` | Sempre injeta se chave existe |

---

## Fluxo da Versão Legada

```
Célula 1: Conexão com o Drive
       ↓
Célula 2: Radar de Hardware (define variáveis de ambiente)
       ↓
Célula 3: Instalação do Forge + Symlinks
       ↓
Célula 4: Vacinas e Dependências
       ↓
Célula 5: Central de Downloads (3 abas)
       ↓
Célula 6: Ignição (lança o Forge)
```

---

## Célula 1: Conexão com o Drive

```python
from google.colab import drive
import os

print("📂 ETAPA 1: CONECTANDO AO GOOGLE DRIVE")
print("--------------------------------------------------")
drive.mount('/content/drive')

base_path = '/content/drive/MyDrive/Stable_Diffusion_Dados'
pastas = ['Modelos_Base', 'LoRAs', 'VAEs', 'Text_Encoders', 'Imagens_Geradas']

for pasta in pastas:
    caminho_completo = os.path.join(base_path, pasta)
    os.makedirs(caminho_completo, exist_ok=True)

print("✅ Pastas verificadas e sincronizadas com sucesso!")
```

**Diferença da melhorada:** Não tem `force_remount=True` e não verifica se as pastas já existem (usa `exist_ok=True` em vez de verificar individualmente).

---

## Célula 2: Radar de Hardware

```python
import torch
import os
import multiprocessing

print("🧠 ETAPA 2: DETECÇÃO DE HARDWARE E OTIMIZAÇÃO PROFUNDA")
print("--------------------------------------------------")

hardware_type = "UNKNOWN"
args_otimizados = ""
cores = multiprocessing.cpu_count()

if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    print(f"✅ GPU NVIDIA Detectada: {gpu_name} (CPU Cores: {cores})")

    if "H100" in gpu_name or "A100" in gpu_name:
        hardware_type = "GPU_LUXO"
        args_otimizados = "--theme dark --cuda-malloc --cuda-stream"

    elif "L4" in gpu_name:
        hardware_type = "GPU_MEDIA"
        args_otimizados = "--theme dark"

    elif "T4" in gpu_name or "G4" in gpu_name:
        hardware_type = "GPU_ECONOMICA"
        args_otimizados = "--theme dark --always-offload-from-vram"
else:
    try:
        import torch_xla
        hardware_type = "TPU"
        args_otimizados = "ERRO_TPU"
    except ImportError:
        hardware_type = "CPU_TURBO"
        os.environ['OMP_NUM_THREADS'] = str(cores)
        os.environ['MKL_NUM_THREADS'] = str(cores)
        os.environ['OPENBLAS_NUM_THREADS'] = str(cores)
        args_otimizados = "--theme dark --use-cpu all --skip-torch-cuda-test --no-half --precision full"

os.environ['FORGE_ARGS'] = args_otimizados
os.environ['HARDWARE_TYPE'] = hardware_type
```

**Diferença da melhorada:** Na versão legada, esta é uma célula separada. Na versão melhorada, a detecção de hardware é feita dentro da célula de ignição.

---

## Célula 3: Instalação do Forge

```python
import os

print("⚙️ ETAPA 3: INSTALANDO FORGE E CONSTRUINDO PONTES")
print("--------------------------------------------------")

!git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git

forge_models = '/content/stable-diffusion-webui-forge/models'
forge_outputs = '/content/stable-diffusion-webui-forge/output'

# Limpa o lixo padrão
!rm -rf {forge_models}/Stable-diffusion {forge_models}/Lora {forge_models}/VAE {forge_outputs}

# Conecta ao seu Drive
!ln -s /content/drive/MyDrive/Stable_Diffusion_Dados/Modelos_Base {forge_models}/Stable-diffusion
!ln -s /content/drive/MyDrive/Stable_Diffusion_Dados/LoRAs {forge_models}/Lora
!ln -s /content/drive/MyDrive/Stable_Diffusion_Dados/VAEs {forge_models}/VAE
!mkdir -p {forge_models}/text_encoder
!ln -s /content/drive/MyDrive/Stable_Diffusion_Dados/Text_Encoders/* {forge_models}/text_encoder/ 2>/dev/null || true
!ln -s /content/drive/MyDrive/Stable_Diffusion_Dados/Imagens_Geradas {forge_outputs}
```

**Diferença da melhorada:**
- Não tem verificação de integridade do Forge (não verifica se `launch.py` existe)
- Não instala Python 3.10 (usa o padrão do Colab)
- Symlink para Text Encoders usa `mkdir -p` + glob em vez de symlink direto

---

## Célula 4: Vacinas

```python
print("💉 ETAPA 4: APLICAÇÃO DE VACINAS E DEPENDÊNCIAS")
print("--------------------------------------------------")

print("➤ Corrigindo interpretadores de texto (CLIP)...")
!python3.10 -m pip install -q ftfy regex tqdm
!python3.10 -m pip install -q https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip --no-build-isolation

print("➤ Erradicando erro de C-Header (Numpy Size Changed)...")
!python3.10 -m pip uninstall -y scikit-image numpy scipy
!python3.10 -m pip install "numpy<2.0.0" "scikit-image<0.23.0" "scipy<1.13.0"

print("➤ Instalando dependências de mapeamento facial (ReActor)...")
!python3.10 -m pip install -q joblib insightface
```

**Diferença da melhorada:** Não tem o PIP_CONSTRAINT (blindagem global contra atualização do Numpy).

---

## Célula 5: Central de Downloads (3 Abas)

A versão legada tem **3 abas** na Central de Downloads:

1. **📥 Baixar (Internet):** Download via URL (igual à melhorada)
2. **📤 Upload (PC Local):** Upload nativo do Colab via `files.upload()`
3. **📁 Gerenciar Arquivos:** CRUD de modelos (igual à melhorada)

### Aba de Upload (Exclusiva da Versão Legada)

```python
from google.colab import files

dropdown_destino_upload = widgets.Dropdown(
    options=['Model / Checkpoint', 'LoRA', 'VAE', 'Text Encoder'],
    value='LoRA',
    description='Destino:'
)
btn_iniciar_upload = widgets.Button(description='🚀 Iniciar Uploader do Google', button_style='success')

def acionar_upload_nativo(b):
    with out_upload:
        clear_output()
        tipo = dropdown_destino_upload.value
        pasta = pasta_modelos if tipo == 'Model / Checkpoint' else pasta_loras if tipo == 'LoRA' else pasta_vaes if tipo == 'VAE' else pasta_text_encoders

        print(f"📡 Conectando ao uploader raiz do Google Colab...")
        print(f"➤ Destino escolhido: Pasta de {tipo}")
        print("👇 Clique no botão 'Escolher arquivos' que apareceu logo abaixo:")

        try:
            arquivos_upados = files.upload()

            if not arquivos_upados:
                print("\n⚠️ Nenhum arquivo foi selecionado. Operação cancelada.")
                return

            print(f"\n🚀 Gravando os arquivos direto no seu Google Drive...")

            for nome_arquivo, conteudo_bytes in arquivos_upados.items():
                caminho_final = os.path.join(pasta, nome_arquivo)
                with open(caminho_final, 'wb') as f:
                    f.write(conteudo_bytes)
                if os.path.exists(nome_arquivo):
                    os.remove(nome_arquivo)
                print(f"   ✅ '{nome_arquivo}' salvo com sucesso!")

            print("\n🎉 Lote concluído!")

        except Exception as e:
            print(f"\n❌ ERRO FATAL: {e}")
```

**Por que foi removida da versão melhorada?** O upload nativo do Colab (`files.upload()`) tem limitações de tamanho e é menos confiável que o download via URL.

---

## Célula 6: Ignição

```python
%cd /content/stable-diffusion-webui-forge

print("🚀 ETAPA FINAL: INICIANDO O ESTÚDIO")
print("--------------------------------------------------")
print("➤ Prevenção Visual: Bloqueando a tentativa do Colab de desenhar gráficos na própria tela (MPLBACKEND='agg')...")
print("➤ Motor Gráfico: Direcionando 100% da carga para a Placa A100...")
print("⏳ Aguarde a geração do link público (gradio.live). Isso pode levar cerca de 20 segundos.\n")

!MPLBACKEND="agg" python3.10 launch.py --share --enable-insecure-extension-access --theme dark --skip-torch-cuda-test
```

**Diferença da melhorada:**
- Não tem autodiagnóstico (não verifica PIP, CLIP, Numpy)
- Não tem hack de memória para CPU
- Não usa variável `FORGE_ARGS` (argumentos fixos)
- Usa `python3.10` diretamente (pode falhar se Python 3.10 não estiver instalado)

---

## Por Que a Versão Legada Foi Substituída?

| Problema | Solução na Melhorada |
|----------|---------------------|
| Python 3.10 não instalado | Instalação automática na Célula 2 |
| Forge corrompido após reset | Verificação de `launch.py` + re-clone |
| Numpy atualizado por dependência | PIP_CONSTRAINT como blindagem global |
| CLIP ausente após reset | Autodiagnóstico + reinstalação automática |
| Sem extensões | Instalador automático (CivitAI Browser+, ReActor) |
| Sem aviso de VRAM | Detecção de hardware + avisos de performance |
| CPU não funciona | Hack de memória (DummyProp) |

---

## Voltar para o índice

[← Extensões](./07-extensoes.md) | [Problemas Conhecidos →](./09-problemas-conhecidos.md)
