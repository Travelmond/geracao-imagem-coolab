# Problemas Conhecidos e Soluções

Erros reais encontrados durante o uso do notebook e suas soluções.

---

## Erros de Bibliotecas

### 1. `numpy.dtype size changed`

**Erro:**
```
numpy.dtype size changed, may indicate binary incompatibility.
Expected 96 from C header, got 88 from PyObject
```

**Causa:** O Colab atualizou o Numpy para v2+, mas scikit-image foi compilado para v1.x.

**Solução:** A Célula 3 (Vacinas) já corrige isso automaticamente. Se persistir:
```python
!python3.10 -m pip uninstall -y scikit-image numpy scipy
!python3.10 -m pip install "numpy<2.0.0" "scikit-image<0.23.0" "scipy<1.13.0"
```

---

### 2. CLIP Ausente

**Erro:**
```
ModuleNotFoundError: No module named 'clip'
```

**Causa:** O Colab resetou a sessão e o CLIP (instalado na sessão anterior) foi perdido.

**Solução:** A Célula 6 (Ignição) detecta e corrige automaticamente. Se precisar corrigir manualmente:
```python
!python3.10 -m pip install -q --upgrade pip setuptools wheel
!python3.10 -m pip install -q ftfy regex tqdm
!python3.10 -m pip install -q https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip --no-build-isolation
```

---

### 3. `NoneType object has no attribute 'filename'` (LoRA)

**Erro:**
```
activating extra network lora with arguments [...]: AttributeError
'NoneType' object has no attribute 'filename'
```

**Causa:** O Forge tentou carregar um LoRA que não foi encontrado no disco. Pode acontecer quando:
- O LoRA foi apagado do Drive mas ainda está referenciado na interface
- O symlink está quebrado

**Solução:**
1. Verifique se o arquivo existe no Drive
2. Reinicie o Forge (célula de ignição novamente)
3. Se o symlink estiver quebrado, execute a Célula 2 novamente

---

### 4. `Mountpoint must not already contain files`

**Erro:**
```
Mountpoint must not already contain files
```

**Causa:** O Google Drive já está montado em `/content/drive` e contém arquivos.

**Solução:** A versão melhorada usa `force_remount=True`:
```python
drive.mount('/content/drive', force_remount=True)
```

---

### 5. PIP Ausente no Python 3.10

**Erro:**
```
/usr/bin/python3.10: No module named pip
```

**Causa:** O Python 3.10 foi instalado sem o PIP.

**Solução:** A Célula 6 (Ignição) detecta e corrige automaticamente:
```python
os.system("curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10 > /dev/null 2>&1")
```

---

## Erros de Hardware

### 6. Low VRAM Warning

**Erro:**
```
[Low VRAM Warning] You just set Forge to use 100% GPU memory (14912.00 MB)
to load model weights. This means you will have 0% GPU memory (0.00 MB)
to do matrix computation. Computations may fallback to CPU or go Out of Memory.
```

**Causa:** O modelo carregado é grande demais para a VRAM da T4 (~15 GB).

**Soluções:**
1. Usar versões FP8 de modelos grandes (FLUX FP8 em vez de FP16)
2. Na interface do Forge, reduzir "GPU Weights" (topo da página)
3. Clique na opção "all" na área "UI" (canto superior esquerdo) para ver o controle

---

### 7. TPU Detectada

**Erro:**
```
❌ ERRO FATAL: TPU DETECTADA! O Forge não compila em XLA/TPU.
```

**Causa:** O Colab atribuiu uma TPU em vez de GPU.

**Solução:** Mude o tipo de runtime:
1. Menu: Runtime → Change runtime type
2. Selecione "GPU" (T4, L4 ou A100)
3. Reinicie a sessão

---

### 8. Geração Extremamente Lenta (Modo CPU)

**Sintoma:** Cada step leva 5-10 segundos em vez de 0.5-1 segundo.

**Causa:** O Colab não atribuiu GPU e o sistema está rodando em CPU.

**Solução:** Verifique se há GPU atribuída:
```python
import torch
print(torch.cuda.is_available())  # Deve ser True
print(torch.cuda.get_device_name(0))  # Deve mostrar T4, L4, etc.
```

Se retornar `False`, mude o runtime para GPU.

---

## Erros de Download

### 9. Download Falha Silenciosamente

**Sintoma:** O wget roda mas o arquivo não aparece no Drive.

**Causa:** O link pode estar quebrado ou a API Key está incorreta.

**Soluções:**
1. Verifique se o link funciona no navegador
2. Se for do Civitai, verifique se a API Key está correta
3. O sistema já verifica se o arquivo tem mais de 50 KB (arquivos menores são considerados erros)

---

### 10. Extensão Não Carrega

**Erro nos logs:**
```
CivitAI Browser+: Basemodel fetch error extracting options: 'issues'
```

**Causa:** A extensão não conseguiu conectar à API do Civitai.

**Solução:** Este erro é não fatal. A extensão funciona normalmente para downloads. O erro de "issues" é um bug conhecido da extensão.

---

## Erros de Configuração

### 11. Forge Corrompido Após Reset

**Sintoma:** `launch.py` não encontrado.

**Causa:** O Colab resetou a sessão e a pasta do Forge ficou incompleta.

**Solução:** A Célula 2 (versão melhorada) detecta e corrige automaticamente:
```python
if not os.path.exists(f"{forge_path}/launch.py"):
    !rm -rf {forge_path}
    !git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git {forge_path}
```

---

### 12. Symlink Quebrado

**Sintoma:** Modelos não aparecem na interface do Forge.

**Causa:** O symlink aponta para uma pasta que não existe ou foi renomeada.

**Solução:** Execute a Célula 2 novamente para recriar todos os symlinks.

---

## Dicas de Performance

### Para T4 (15 GB VRAM)

- Use modelos FP8 em vez de FP16
- FLUX FP8 cabe na T4; FLUX FP16 não
- Reduza "GPU Weights" se receber avisos de VRAM baixa
- Use resoluções menores (512x512 ou 768x768) para modelos SDXL

### Para L4 (24 GB VRAM)

- A maioria dos modelos cabe sem problemas
- FLUX FP16 cabe com folga
- Pode usar resoluções maiores (1024x1024)

### Para A100 (40-80 GB VRAM)

- Todos os modelos cabem
- Use FP16 para melhor qualidade
- Pode carregar múltiplos modelos simultaneamente

---

## Voltar para o índice

[← Versão Legada](./08-versao-legada.md) | [Glossário →](./10-glossario.md)
