# Dependências e Patches

Todas as correções aplicadas para garantir compatibilidade entre o Colab, as bibliotecas Python e o Forge.

---

## O Problema

O Google Colab atualiza frequentemente suas bibliotecas. Isso quebra o Forge porque:

1. **Numpy v2+** muda estruturas C internas, quebrando scikit-image compilado para v1.x
2. **CLIP (OpenAI)** tem problemas de compilação no ambiente do Colab
3. **Insightface** precisa de versões específicas para funcionar com ReActor

---

## Vacina 1: CLIP (OpenAI)

### O Erro

```
error: metadata-generation-failed
× Encountered error while generating package.
```

### A Solução

```python
# Instala dependências manualmente
!python3.10 -m pip install -q ftfy regex tqdm

# Força instalação via GitHub com --no-build-isolation
!python3.10 -m pip install -q https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip --no-build-isolation
```

### Por Que `--no-build-isolation`?

Por padrão, o PIP compila pacotes em um ambiente isolado. O `--no-build-isolation` força a compilação usando as bibliotecas já instaladas no sistema, evitando conflitos de versão.

### Por Que o Commit Específico?

`d50d76daa670286dd6cacf3bcd80b5e4823fc8e1` é um commit testado e funcional. Usar `pip install clip` (PyPI) causa erros de compilação no Colab.

---

## Vacina 2: Numpy (Erro Matemático)

### O Erro

```
numpy.dtype size changed, may indicate binary incompatibility.
Expected 96 from C header, got 88 from PyObject
```

### O Que Acontece

O Colab instala Numpy v2.x por padrão. Bibliotecas como scikit-image foram compiladas contra Numpy v1.x. Quando o Numpy é atualizado, as estruturas C internas mudam de tamanho, causando erro de compilação.

### A Solução

```python
# Remove completamente as versões atuais
!python3.10 -m pip uninstall -y scikit-image numpy scipy

# Instala versões compatíveis
!python3.10 -m pip install "numpy<2.0.0" "scikit-image<0.23.0" "scipy<1.13.0"
```

### Versões Fixadas

| Pacote | Versão Instalada | Versão do Colab (Problemática) |
|--------|-----------------|-------------------------------|
| numpy | 1.26.4 | 2.2.6 |
| scikit-image | 0.22.0 | 0.21.0 |
| scipy | 1.12.0 | 1.15.3 |

---

## Vacina 3: ReActor (Insightface)

### O Que É

O ReActor é uma extensão para face swap (troca de rostos). Precisa de:
- `joblib`: para processamento paralelo (mistura de bordas em inpainting)
- `insightface`: biblioteca de reconhecimento facial

### A Solução

```python
!python3.10 -m pip install -q joblib insightface
```

---

## PIP_CONSTRAINT: A Blindagem Global

### O Problema

Mesmo aplicando as vacinas, alguma dependência do Forge pode tentar atualizar o Numpy de volta para v2+ durante a instalação.

### A Solução

```python
# Cria arquivo de restrições
with open('/content/restricao_pip.txt', 'w') as f:
    f.write("numpy<2.0.0\nscikit-image<0.23.0\nscipy<1.13.0\n")

# Injeta no PIP via variável de ambiente
os.environ["PIP_CONSTRAINT"] = "/content/restricao_pip.txt"
```

### Como Funciona

O `PIP_CONSTRAINT` é uma variável de ambiente que o PIP verifica antes de instalar **qualquer** pacote. Se um pacote tentar instalar Numpy 2.x, o PIP bloqueia automaticamente.

**Arquivo `/content/restricao_pip.txt`:**
```
numpy<2.0.0
scikit-image<0.23.0
scipy<1.13.0
```

### Ordem de Execução

```
1. Desinstala pacotes problemáticos
2. Cria arquivo de restrições
3. Define PIP_CONSTRAINT
4. Reinstala versões corretas
```

---

## Ordem Correta de Instalação

```
┌─────────────────────────────────────────────┐
│ 1. Python 3.10 + PIP                        │
├─────────────────────────────────────────────┤
│ 2. CLIP (com --no-build-isolation)          │
├─────────────────────────────────────────────┤
│ 3. Numpy <2.0 + Scikit-image <0.23          │
├─────────────────────────────────────────────┤
│ 4. Insightface + Joblib                     │
├─────────────────────────────────────────────┤
│ 5. PIP_CONSTRAINT (blindagem)               │
├─────────────────────────────────────────────┤
│ 6. Forge (que pode reinstalar deps)         │
│    → PIP_CONSTRAINT protege contra regressão│
└─────────────────────────────────────────────┘
```

---

## Dependências do Forge (Instaladas Automaticamente)

O `launch.py` do Forge instala suas próprias dependências. Algumas das principais:

| Pacote | Versão | Função |
|--------|--------|--------|
| torch | 2.10.0+cu128 | Framework de IA (PyTorch com CUDA) |
| torchvision | - | Processamento de imagens |
| gradio | - | Interface web |
| transformers | - | Modelos HuggingFace |
| diffusers | - | Pipeline de difusão |
| safetensors | - | Leitura de modelos seguros |
| xformers | - | Otimização de atenção |
| open-clip-torch | 2.20.0 | CLIP para modelos SDXL |

---

## Conflitos Conhecidos (Não Fatais)

Mesmo com as vacinas, podem aparecer avisos de conflito:

```
ERROR: pip's dependency resolver does not currently take into account
all the packages that are installed.
albumentations 2.0.8 requires pydantic>=2.9.2, but you have pydantic 2.8.2
onnx 1.20.1 requires protobuf>=4.25.1, but you have protobuf 3.20.0
opencv-contrib-python requires numpy>=2, but you have numpy 1.26.4
```

**Esses avisos são normais e não afetam o funcionamento.** O Forge funciona perfeitamente com essas versões.

---

## Voltar para o índice

[← Modelos e Pastas](./05-modelos-e-pastas.md) | [Extensões →](./07-extensoes.md)
