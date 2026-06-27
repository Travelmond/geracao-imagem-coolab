# Dependências e Patches — V4

Todas as correções aplicadas para garantir compatibilidade entre o Colab, as bibliotecas Python e o Forge.

---

## O Problema

O Google Colab atualiza frequentemente suas bibliotecas. As extensões do Forge também instalam suas próprias dependências durante o startup. Isso causa conflitos:

1. **Numpy v2+** muda estruturas C internas, quebrando scikit-image
2. **CLIP (OpenAI)** tem problemas de compilação no ambiente do Colab
3. **Insightface** precisa de versões específicas para funcionar com ReActor
4. **Bitsandbytes** exige GLIBCXX_3.4.32 que não está no Colab

---

## Vacina 1: CLIP (OpenAI)

### O Erro

```
error: metadata-generation-failed
× Encountered error while generating package.
```

### A Solução

```python
!python3.10 -m pip install ftfy regex tqdm
!python3.10 -m pip install https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip --no-build-isolation
```

### Por Que `--no-build-isolation`?

Força a compilação usando as bibliotecas já instaladas, evitando conflitos de versão.

### Verificação Correta

```python
r = subprocess.run(['python3.10', '-c', 'import clip; print("OK")'], capture_output=True, text=True)
if 'OK' in r.stdout:
    print('✅ CLIP funcional')
```

**Importante:** Não use `import clip` diretamente no notebook — roda no Python do Colab (3.11+), não no python3.10.

---

## Vacina 2: NumPy

### O Erro

```
numpy.dtype size changed, may indicate binary incompatibility.
Expected 96 from C header, got 88 from PyObject
```

### A Solução

```python
!python3.10 -m pip install 'numpy<2.1.0' --force-reinstall
```

**Nota:** Aceitamos `numpy 2.0.x` (compatível com scikit-image 0.22+). Bloqueamos apenas `2.1+`.

---

## Vacina 3: Bitsandbytes

### O Erro

```
GLIBCXX_3.4.32 not found (required by bitsandbytes)
```

### A Solução

```python
!python3.10 -m pip install bitsandbytes==0.43.3
```

Versão 0.43.3 é compatível com o libstdc++ do Colab.

---

## Vacina 4: Insightface

### O Erro

```
ModuleNotFoundError: No module named 'insightface'
```

### A Solução

```python
!python3.10 -m pip install opencv-python-headless
!python3.10 -m pip install insightface joblib
```

**Importante:** Instalar `opencv-python-headless` antes do insightface.

---

## PIP_CONSTRAINT: A Blindagem Global

```python
with open('/tmp/pip_constraints.txt', 'w') as f:
    f.write('numpy<2.1.0\nscikit-image<0.23.0\nscipy<2.0.0\n')
os.environ['PIP_CONSTRAINT'] = '/tmp/pip_constraints.txt'
```

Impede que **qualquer** instalação futura de pacote sobrescreva as versões corretas.

---

## Célula 4.2: Reaplicar Vacinas

**Por que existe:** As extensões rodam `install.py` durante o startup do Forge, sobrescrevendo versões. A Célula 4.2 reaplica as vacinas **depois** das extensões.

```python
!python3.10 -m pip install 'numpy<2.1.0' 'scikit-image<0.23.0' 'scipy<2.0.0' 'opencv-python-headless' --force-reinstall -q
```

---

## Voltar para o índice

[← Modelos e Pastas](./05-modelos-e-pastas.md) | [Extensões →](./07-extensoes.md)
