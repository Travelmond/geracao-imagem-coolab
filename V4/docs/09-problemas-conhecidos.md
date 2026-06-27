# Problemas Conhecidos — V4

Erros reais encontrados durante o uso do notebook e suas soluções.

---

## Erro 1: `GLIBCXX_3.4.32 not found` (bitsandbytes)

**Erro:**
```
/lib/x86_64-linux-gnu/libstdc++.so.6: version `GLIBCXX_3.4.32' not found
```

**Causa:** O bitsandbytes 0.45.3 exige GLIBCXX_3.4.32 (GCC 13+), mas o Colab tem GCC 11.

**Solução:** Pin para bitsandbytes 0.43.3 na Célula 3:
```python
!python3.10 -m pip install bitsandbytes==0.43.3
```

---

## Erro 2: `numpy.dtype size changed`

**Erro:**
```
ValueError: numpy.dtype size changed, may indicate binary incompatibility.
Expected 96 from C header, got 88 from PyObject
```

**Causa:** O scikit-image 0.21.0 foi compilado para numpy 1.x, mas o numpy foi atualizado para 2.0.x pelas extensões.

**Solução:** Célula 4.2 reaplica versões compatíveis:
```python
!python3.10 -m pip install 'numpy<2.1.0' 'scikit-image<0.23.0' 'scipy<2.0.0' 'opencv-python-headless' --force-reinstall
```

---

## Erro 3: `import clip` falha no notebook

**Erro:**
```
ModuleNotFoundError: No module named 'clip'
```

**Causa:** O CLIP é instalado no `python3.10`, mas o `import clip` roda no Python do notebook (3.11+).

**Solução:** Verificar com subprocess:
```python
r = subprocess.run(['python3.10', '-c', 'import clip; print("OK")'], capture_output=True, text=True)
```

---

## Erro 4: `opencv-python-headless` bloqueia downgrade do numpy

**Erro:**
```
opencv-python 4.13.0.92 requires numpy>=2; python_version >= "3.9"
```

**Causa:** O opencv-python-headless 4.13 exige numpy>=2. Quando tentamos forçar numpy<2.0, o pip rejeita.

**Solução:** Incluir opencv no pip install da Célula 4.2:
```python
!python3.10 -m pip install ... 'opencv-python-headless' --force-reinstall
```

---

## Erro 5: URLs de extensões quebradas

**Erro:**
```
fatal: repository not found
```

**Causa:** Repositórios removidos/desabilitados pelo GitHub.

| Repositório | Status |
|-------------|--------|
| `Haoming02/sd-webui-civitai-browser-plus` | ❌ 404 |
| `Gourieff/sd-webui-reactor` | ❌ Desabilitado (ToS) |
| `BlafKing/sd-civitai-browser-plus` | 🟡 Arquivado |

**Solução:** Usar `SignalFlagZ/sd-webui-civbrowser` + ZIP local do ReActor.

---

## Erro 6: UI do Gradio congela

**Erro:** A aba Cache Manager carrega infinitamente sem mostrar conteúdo.

**Causa:** `on_tab_load()` lança exceção sem try/except.

**Solução:** Try/except em todos os callbacks da `tab_ui.py`:
```python
def on_tab_load():
    try:
        _init_managers()
        results = refresh_all()
        return results
    except Exception as e:
        return [f"❌ Erro: {e}"] * total_outputs
```

---

## Erro 7: `2>&1 | tail -3` esconde erros

**Erro:** Comandos falham silenciosamente, sem mostrar o erro real.

**Causa:** Redirecionamento engole a saída de erro.

**Solução:** Remover todos os `tail` e `/dev/null` dos comandos pip.

---

## Erro 8: Symlinks quebrados

**Erro:** O Forge não encontra os modelos.

**Causa:** O cache local não existe antes de criar os symlinks.

**Solução:** Criar pastas antes de criar symlinks:
```python
os.makedirs('/content/cache/checkpoints', exist_ok=True)
!ln -s /content/cache/checkpoints {forge_dir}/models/Stable-diffusion
```

---

## Erro 9: Extensões sobrescrevem vacinas

**Erro:** Após a Célula 4, o numpy volta para 2.0.2 e scikit-image quebra.

**Causa:** As extensões rodam `install.py` durante o startup do Forge (Célula 6), sobrescrevendo as vacinas da Célula 3.

**Solução:** Célula 4.2 reaplica vacinas **depois** das extensões, mas **antes** do Forge iniciar.

---

## Erro 10: `GradioDeprecationWarning: password`

**Erro:**
```
GradioDeprecationWarning: unexpected argument for Textbox: password
```

**Causa:** O parâmetro `password=True` foi depreciado em versões recentes do Gradio.

**Solução:** Usar `type="password"`:
```python
gr.Textbox(label="API Key", type="password")
```

---

## Voltar para o índice

[← Versão Legada](./08-versao-legada.md) | [Glossário →](./10-glossario.md)
