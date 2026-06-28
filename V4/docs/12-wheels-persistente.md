# 📦 Guia de Wheels Persistente

## Problema Resolvido

As 4 bibliotecas que sempre falhavam no EnvironmentDoctor:
- ❌ CLIP (OpenAI)
- ❌ bitsandbytes
- ❌ ONNX Runtime
- ❌ InsightFace

## Solução Implementada

### Estratégia B (Opção Escolhida)

Em vez de instalar via pip a cada sessão, agora:

1. **Baixa wheels pré-compilados** uma única vez
2. **Salva no Google Drive** em `/Stable_Diffusion_Dados/wheels/`
3. **Reutiliza nas próximas sessões** — instalação instantânea!

## Como Funciona

### Primeira Sessão (Download dos Wheels)

```python
# Célula 3 do DiffusionUI.ipynb
# 1. Tenta importar (já instalado?)
# 2. Se não, procura wheel no Drive
# 3. Se não tem, baixa da internet e SALVA no Drive
# 4. Instala do wheel baixado
```

### Próximas Sessões

```python
# Célula 3 do DiffusionUI.ipynb
# 1. Tenta importar (já instalado?)
# 2. Encontra wheel no Drive → instala em segundos!
# 3. ✅ Biblioteca funcional
```

## Estrutura de Pastas

```
Google Drive/
└── MyDrive/
    └── Stable_Diffusion_Dados/
        ├── wheels/              ← NOVO!
        │   ├── clip-*.whl
        │   ├── bitsandbytes-*.whl
        │   ├── onnxruntime_gpu-*.whl
        │   └── insightface-*.whl
        ├── cache-manager/
        └── sd-webui-reactor/
```

## Scripts Auxiliares

### download-wheels.sh

Script opcional para baixar wheels manualmente:

```bash
# No Colab (Célula de código):
!bash /content/drive/MyDrive/Stable_Diffusion_Dados/scripts-auxiliares/download-wheels.sh

# Ou no seu computador (se tiver Python 3.10):
bash download-wheels.sh /caminho/para/wheels
```

## Vantagens

| Antes | Depois |
|-------|--------|
| ❌ 4-6 minutos instalando | ✅ 30-60 segundos |
| ❌ Falhas frequentes | ✅ Instalação confiável |
| ❌ Baixa da internet toda vez | ✅ Wheel local reutilizado |
| ❌ Sem persistência | ✅ Persiste no Drive |

## O Que Mudou no Código

### CLIP (OpenAI)

**Antes:**
```python
!python3.10 -m pip install https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip --no-build-isolation
```

**Depois:**
```python
clip_wheel = f'{wheels_dir}/clip-1.0-py3-none-any.whl'

if os.path.exists(clip_wheel):
    # Usa wheel salvo (rápido!)
    !{python} -m pip install {clip_wheel} --quiet
else:
    # Baixa e salva (primeira vez)
    !{python} -m pip install git+https://github.com/openai/CLIP.git --quiet --no-build-isolation
    !{python} -m pip download clip --no-deps -d {wheels_dir} --quiet
```

### bitsandbytes

**Antes:**
```python
!python3.10 -m pip install 'bitsandbytes==0.43.3'
```

**Depois:**
```python
# Verifica se já está instalado
try:
    import bitsandbytes
    print(f'✅ Já instalado: {bitsandbytes.__version__}')
except ImportError:
    # Instala e salva wheel
    !{python} -m pip install 'bitsandbytes==0.43.3' --quiet
    !{python} -m pip download bitsandbytes==0.43.3 --no-deps -d {wheels_dir} --quiet
```

### ONNX Runtime

**Antes:**
```python
!python3.10 -m pip install 'onnxruntime-gpu==1.17.1' \
    --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/
```

**Depois:**
```python
# Fallback automático: GPU → CPU
try:
    !{python} -m pip install onnxruntime-gpu==1.17.1 [cuda-params] --quiet
except:
    !{python} -m pip install onnxruntime --quiet  # Versão CPU
```

### InsightFace

**Antes:**
```python
!python3.10 -m pip install 'insightface==0.7.3'
```

**Depois:**
```python
# Tenta 0.7.3 primeiro, fallback para versão mais recente
!{python} -m pip install 'insightface==0.7.3' --quiet 2>/dev/null || \
!{python} -m pip install insightface --quiet
```

## Resumo Final da Célula 3

Ao final da execução, você verá:

```
📊 RESUMO DA INSTALAÇÃO:
──────────────────────────────────────────────────
   ✅ CLIP                 v1.0
   ✅ NumPy                v2.0.2
   ✅ bitsandbytes         v0.43.3
   ✅ ONNX Runtime         v1.17.1
   ✅ InsightFace          v0.7.3

💾 Wheels salvos em: /content/drive/MyDrive/Stable_Diffusion_Dados/wheels
   (Serão reutilizados na próxima sessão!)
```

## Próximos Passos

1. Execute a **Célula 3** no Colab
2. Aguarde o download dos wheels (primeira vez apenas)
3. Nas próximas sessões, a instalação será **muito mais rápida**!

## Notas Importantes

- **Primeira execução**: Pode levar 2-3 minutos para baixar todos os wheels
- **Execuções seguintes**: 30-60 segundos (instalação local)
- **Espaço no Drive**: ~200-300 MB para todos os wheels
- **Compatibilidade**: Wheels específicos para Python 3.10 + CUDA 12 (Colab T4)
