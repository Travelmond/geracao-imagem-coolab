# Hardware e Otimização

Detecção automática de GPU/CPU e aplicação de argumentos otimizados para cada tipo de hardware.

---

## Tabela de Hardware Suportado

| Tipo | GPUs | Classificação | Argumentos Aplicados |
|------|------|---------------|---------------------|
| GPU_LUXO | H100, A100 | Desempenho Extremo | `--theme dark --cuda-malloc --cuda-stream` |
| GPU_MEDIA | L4 | Custo-Benefício | `--theme dark` |
| GPU_ECONOMICA | T4, G4 | Economia de Memória | `--theme dark --always-offload-from-vram` |
| TPU | (qualquer TPU) | **Incompatível** | `ERRO_TPU` (aborta) |
| CPU_TURBO | (sem GPU) | Modo CPU | `--theme dark --use-cpu all --skip-torch-cuda-test --no-half --precision full` |

---

## Código de Detecção

```python
import torch
import os
import multiprocessing

hardware_type = "UNKNOWN"
args_otimizados = ""
cores = multiprocessing.cpu_count()

if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)

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

---

## Explicação por Tipo de Hardware

### GPU_LUXO (A100 / H100)

**VRAM:** 40-80 GB
**Perfil:** Desempenho máximo, sem preocupação com memória.

```
--cuda-malloc    → Usa o alocador de memória CUDA otimizado (mais rápido)
--cuda-stream    → Usa streams CUDA paralelos (reduz latência)
```

**Quando usar:** Quando o Colab atribui uma A100 (comum no Colab Pro+). Todos os modelos cabem na VRAM sem problemas.

### GPU_MEDIA (L4)

**VRAM:** ~24 GB
**Perfil:** Bom custo-benefício, cabe a maioria dos modelos.

```
--theme dark     → Apenas tema escuro (sem otimizações extras)
```

**Quando usar:** O L4 tem VRAM suficiente para a maioria dos modelos. Não precisa de offload.

### GPU_ECONOMICA (T4 / G4)

**VRAM:** ~15 GB
**Perfil:** VRAM limitada, precisa de gestão agressiva de memória.

```
--always-offload-from-vram  → Libera VRAM após cada operação
```

**Quando usar:** O T4 é a GPU gratuita mais comum do Colab. Com 15 GB, modelos grandes como FLUX precisam de offload.

**Limitações:**
- Modelos FP16 de 22 GB (como FLUX) não cabem na VRAM
- Recomendado usar versões FP8 para modelos grandes
- Geração será mais lenta (offload para RAM)

### TPU (Incompatível)

**Erro fatal.** O Forge depende de CUDA (NVIDIA). TPU usa XLA, que é incompatível.

Se o Colab atribuir uma TPU, o sistema aborta com mensagem de erro clara.

### CPU_TURBO (Sem GPU)

**Perfil:** Extremamente lento, mas funcional para testes.

**Otimizações aplicadas:**

```python
os.environ['OMP_NUM_THREADS'] = str(cores)
os.environ['MKL_NUM_THREADS'] = str(cores)
os.environ['OPENBLAS_NUM_THREADS'] = str(cores)
```
Força todas as bibliotecas matemáticas a usar todos os núcleos da CPU.

```
--use-cpu all              → Força uso de CPU
--skip-torch-cuda-test     → Pula verificação de CUDA
--no-half                  → Usa FP32 (CPU não suporta FP16 eficientemente)
--precision full           → Precisão total
```

**Hack de memória para CPU:**

Quando roda em CPU, o Forge pode se recusar carregar modelos por achar que não há VRAM. O hack modifica `memory_management.py` para "enganar" o sistema:

```python
# Substitui chamadas de GPU por valores falsos
cod = cod.replace("torch.cuda.current_device()", "'cpu'")
cod = cod.replace("torch.cuda.get_device_properties(device).total_memory", "(32 * 1024 * 1024 * 1024)")
```

Isso faz o Forge pensar que tem 32 GB de VRAM quando na verdade está usando RAM.

---

## Gestão de VRAM (T4)

### O Aviso de VRAM Baixa

Quando a VRAM é insuficiente, o Forge exibe:

```
[Low VRAM Warning] You just set Forge to use 100% GPU memory (14912.00 MB)
to load model weights. This means you will have 0% GPU memory (0.00 MB)
to do matrix computation. Computations may fallback to CPU or go Out of Memory.
```

**Soluções:**
1. Usar versões FP8 de modelos grandes
2. Reduzir "GPU Weights" na interface do Forge
3. Usar `--always-offload-from-vram` (já aplicado automaticamente para T4)

### Exemplo de Uso de VRAM (T4 com Nova 3DCG XL)

```
Total VRAM: 14913 MB (14.6 GB)
Modelo carregado: Nova 3DCG XL.safetensors

[GPU Setting] You will use 93.13% GPU memory (13888.00 MB) to load weights,
and use 6.87% GPU memory (1024.00 MB) to do matrix computation.
```

---

## Variáveis de Ambiente

| Variável | Valor | Propósito |
|----------|-------|-----------|
| `FORGE_ARGS` | Argumentos de linha de comando | Configuração do Forge |
| `HARDWARE_TYPE` | `GPU_LUXO`, `GPU_MEDIA`, etc. | Identificação do hardware |
| `OMP_NUM_THREADS` | Número de cores | Otimização CPU (OpenMP) |
| `MKL_NUM_THREADS` | Número de cores | Otimização CPU (Intel MKL) |
| `OPENBLAS_NUM_THREADS` | Número de cores | Otimização CPU (OpenBLAS) |
| `MPLBACKEND` | `agg` | Impede renderização gráfica no Colab |
| `PIP_CONSTRAINT` | Caminho do arquivo de restrições | Bloqueia atualização do Numpy |

---

## Voltar para o índice

[← Interface de Widgets](./03-interface-widgets.md) | [Modelos e Pastas →](./05-modelos-e-pastas.md)
