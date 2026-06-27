# Fluxo de Execução Detalhado

Documentação completa de cada célula da **versão melhorada** do notebook, com código completo e explicação linha a linha.

> **Nota:** Este documento cobre a versão melhorada (células localizadas no **final** do notebook). Para a versão legada, veja [08-versao-legada.md](./08-versao-legada.md).

---

## Visão Geral das Células

| Ordem | Célula | Propósito | Obrigatória? |
|-------|--------|-----------|-------------|
| 1 | Drive | Conecta ao Google Drive e cria pastas | Sim |
| 2 | Forge + Python | Instala Forge, Python 3.10 e symlinks | Sim |
| 3 | Vacinas | Corrige incompatibilidades de bibliotecas | Sim |
| 4 | Central de Downloads | UI para gerenciar modelos | Não (mas recomendada) |
| 5.5 | Extensões | Instala CivitAI Browser+ e ReActor | Não (mas recomendada) |
| 5/6 | Launch | Inicia o Forge com link público | Sim |

---

## Célula 1: A Fundação (Conexão Segura com o Drive)

**Propósito:** Conectar o Colab ao Google Drive e garantir que todas as pastas necessárias existam. Resolve o erro comum `Mountpoint must not already contain files`.

### Código Completo

```python
from google.colab import drive
import os

print("🔍 ETAPA 1: VERIFICAÇÃO DO GOOGLE DRIVE")
print("--------------------------------------------------")

print("➤ Ação: Conectando ao Google Drive...")
drive.mount('/content/drive', force_remount=True)

print("\n➤ Ação: Verificando a estrutura de pastas permanentes...")
pasta_base = '/content/drive/MyDrive/Stable_Diffusion_Dados'
# Adicionamos a pasta Text_Encoders na lista de verificação/criação
pastas = ['Modelos_Base', 'LoRAs', 'VAEs', 'Text_Encoders', 'Imagens_Geradas']

for p in pastas:
    caminho = f"{pasta_base}/{p}"
    if not os.path.exists(caminho):
        print(f"   [+] Criando pasta ausente: {p}")
        os.makedirs(caminho)
    else:
        print(f"   [✓] Pasta {p} já existe e está segura.")

print("--------------------------------------------------")
print("✅ ETAPA 1 CONCLUÍDA: Seu cofre de arquivos está pronto!")
```

### Explicação Linha a Linha

```python
from google.colab import drive
```
Importa o módulo de integração com Google Drive exclusivo do Colab.

```python
drive.mount('/content/drive', force_remount=True)
```
Monta o Google Drive no caminho `/content/drive`. O parâmetro `force_remount=True` força uma reconexão mesmo se já estiver montado (útil quando o Colab perde a conexão).

```python
pasta_base = '/content/drive/MyDrive/Stable_Diffusion_Dados'
```
Define o caminho raiz onde todos os modelos e imagens serão armazenados.

```python
pastas = ['Modelos_Base', 'LoRAs', 'VAEs', 'Text_Encoders', 'Imagens_Geradas']
```
Lista das 5 subpastas que o sistema precisa:

| Pasta | Conteúdo |
|-------|----------|
| `Modelos_Base` | Checkpoints principais (2-25 GB cada) |
| `LoRAs` | Modificadores de estilo (10-500 MB cada) |
| `VAEs` | Decodificadores de imagem (300-400 MB cada) |
| `Text_Encoders` | Codificadores de texto CLIP/T5 (200 MB - 9 GB) |
| `Imagens_Geradas` | Output das imagens criadas pelo Forge |

```python
for p in pastas:
    caminho = f"{pasta_base}/{p}"
    if not os.path.exists(caminho):
        os.makedirs(caminho)
```
Loop que verifica cada pasta. Se não existir, cria automaticamente.

### Saída Esperada

```
🔍 ETAPA 1: VERIFICAÇÃO DO GOOGLE DRIVE
--------------------------------------------------
➤ Ação: Conectando ao Google Drive...
Mounted at /content/drive

➤ Ação: Verificando a estrutura de pastas permanentes...
   [✓] Pasta Modelos_Base já existe e está segura.
   [✓] Pasta LoRAs já existe e está segura.
   [✓] Pasta VAEs já existe e está segura.
   [✓] Pasta Text_Encoders já existe e está segura.
   [✓] Pasta Imagens_Geradas já existe e está segura.
--------------------------------------------------
✅ ETAPA 1 CONCLUÍDA: Seu cofre de arquivos está pronto!
```

---

## Célula 2: O Motor (Instalação e Restauração do Forge)

**Propósito:** Instalar o Python 3.10, clonar o WebUI Forge e criar os symlinks que conectam o Forge ao Google Drive.

### Código Completo

```python
import os
from IPython.display import clear_output

print("🔍 ETAPA 2: VERIFICAÇÃO DO SISTEMA E WEBUI FORGE")
print("--------------------------------------------------")

print("➤ Ação: Configurando o motor Python 3.10...")
!apt-get update -qq
!apt-get install software-properties-common -y -qq
!add-apt-repository ppa:deadsnakes/ppa -y -qq
!apt-get update -qq
!apt-get install python3.10 python3.10-venv python3.10-dev python3.10-distutils -y -qq
!curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10 -q

print("\n➤ Ação: Verificando a integridade do WebUI Forge...")
forge_path = '/content/stable-diffusion-webui-forge'
pasta_base = '/content/drive/MyDrive/Stable_Diffusion_Dados'

if os.path.exists(forge_path):
    if not os.path.exists(f"{forge_path}/launch.py"):
        print("   [!] AVISO: Pasta corrompida detectada! Forçando limpeza...")
        !rm -rf {forge_path}
        !git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git {forge_path}
    else:
        print("   [✓] Forge detectado e intacto.")
else:
    print("   [+] Forge não encontrado. Iniciando download...")
    !git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git {forge_path}

print("\n➤ Ação: Criando as 'Pontes' (Symlinks) entre o Forge e o seu Drive...")
!rm -rf {forge_path}/models/Stable-diffusion && ln -s "{pasta_base}/Modelos_Base" {forge_path}/models/Stable-diffusion
!rm -rf {forge_path}/models/Lora && ln -s "{pasta_base}/LoRAs" {forge_path}/models/Lora
!rm -rf {forge_path}/models/VAE && ln -s "{pasta_base}/VAEs" {forge_path}/models/VAE
# A MÁGICA NOVA: Criando a ponte para a pasta oculta de Text Encoders do Forge
!rm -rf {forge_path}/models/text_encoder && ln -s "{pasta_base}/Text_Encoders" {forge_path}/models/text_encoder
!rm -rf {forge_path}/outputs && ln -s "{pasta_base}/Imagens_Geradas" {forge_path}/outputs

clear_output()
print("✅ ETAPA 2 CONCLUÍDA: Sistema base e atalhos configurados com sucesso!")
```

### Explicação Linha a Linha

#### Instalação do Python 3.10

```python
!apt-get update -qq
```
Atualiza a lista de pacotes do sistema (Ubuntu). `-qq` = modo silencioso.

```python
!apt-get install software-properties-common -y -qq
```
Instala utilitários para gerenciar repositórios PPA.

```python
!add-apt-repository ppa:deadsnakes/ppa -y -qq
```
Adiciona o repositório `deadsnakes` que contém versões alternativas do Python.

```python
!apt-get install python3.10 python3.10-venv python3.10-dev python3.10-distutils -y -qq
```
Instala o Python 3.10 e seus módulos essenciais:
- `python3.10-venv`: ambientes virtuais
- `python3.10-dev`: headers de compilação
- `python3.10-distutils`: ferramentas de distribuição

```python
!curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10 -q
```
Instala o PIP (gerenciador de pacotes) no Python 3.10.

#### Verificação do Forge

```python
forge_path = '/content/stable-diffusion-webui-forge'
```
Caminho onde o Forge será instalado (memória temporária do Colab).

```python
if os.path.exists(forge_path):
    if not os.path.exists(f"{forge_path}/launch.py"):
        print("   [!] AVISO: Pasta corrompida detectada! Forçando limpeza...")
        !rm -rf {forge_path}
        !git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git {forge_path}
```
Lógica de recuperação: se a pasta existe mas `launch.py` não foi encontrado, a pasta está corrompida (aconhece quando o Colab reseta a sessão). Apaga e clona novamente.

#### Criação dos Symlinks

```python
!rm -rf {forge_path}/models/Stable-diffusion && ln -s "{pasta_base}/Modelos_Base" {forge_path}/models/Stable-diffusion
```
**O que faz:**
1. Remove a pasta padrão `Stable-diffusion` do Forge
2. Cria um symlink apontando para `Modelos_Base` no Drive

**Por quê?** Quando o Forge procura checkpoints, ele olha `models/Stable-diffusion`. Com o symlink, ele encontra os modelos do Drive automaticamente.

```python
!rm -rf {forge_path}/models/text_encoder && ln -s "{pasta_base}/Text_Encoders" {forge_path}/models/text_encoder
```
Symlink para Text Encoders (CLIP, T5). Esta pasta não existe por padrão no Forge — é criada especialmente.

```python
!rm -rf {forge_path}/outputs && ln -s "{pasta_base}/Imagens_Geradas" {forge_path}/outputs
```
Symlink para imagens geradas. Sem isso, as imagens ficariam na memória temporária e seriam perdidas.

### Mapa de Symlinks

| Caminho do Forge | Aponta para (Drive) |
|-----------------|---------------------|
| `models/Stable-diffusion` | `Stable_Diffusion_Dados/Modelos_Base` |
| `models/Lora` | `Stable_Diffusion_Dados/LoRAs` |
| `models/VAE` | `Stable_Diffusion_Dados/VAEs` |
| `models/text_encoder` | `Stable_Diffusion_Dados/Text_Encoders` |
| `outputs` | `Stable_Diffusion_Dados/Imagens_Geradas` |

---

## Célula 3: O Antídoto (Vacinas contra Atualizações do Colab)

**Propósito:** Corrigir incompatibilidades de bibliotecas que o Colab atualiza frequentemente, quebrando o Forge.

### Código Completo

```python
print("🔍 ETAPA 3: APLICAÇÃO DE VACINAS E CORREÇÕES")
print("--------------------------------------------------")

print("➤ Vacina 1: Erro de Instalação do CLIP (OpenAI)")
print("   [+] Ação: Instalando dependências manuais e forçando instalação via GitHub (--no-build-isolation)...")
!python3.10 -m pip install -q ftfy regex tqdm
!python3.10 -m pip install -q https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip --no-build-isolation

print("\n➤ Vacina 2: Erro Matemático do Colab (numpy.dtype size changed)")
print("   [+] Ação: Forçando a desinstalação profunda e reinstalando as versões clássicas (1.x) que o Forge exige...")
!python3.10 -m pip uninstall -y scikit-image numpy scipy
!python3.10 -m pip install "numpy<2.0.0" "scikit-image<0.23.0" "scipy<1.13.0"

print("\n➤ Vacina 3: Ferramentas Avançadas (Inpainting e Face Swap ReActor)")
print("   [+] Ação: Instalando bibliotecas Joblib (para misturar bordas) e Insightface (para mapeamento de rosto)...")
!python3.10 -m pip install -q joblib insightface

print("--------------------------------------------------")
print("✅ ETAPA 3 CONCLUÍDA: Todas as bibliotecas estão perfeitamente alinhadas!")
```

### Explicação Linha a Linha

#### Vacina 1: CLIP (OpenAI)

```python
!python3.10 -m pip install -q ftfy regex tqdm
```
Instala dependências do CLIP:
- `ftfy`: corrige encoding de texto Unicode
- `regex`: expressões regulares avançadas
- `tqdm`: barras de progresso

```python
!python3.10 -m pip install -q https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip --no-build-isolation
```
Instala o CLIP diretamente do GitHub, usando um commit específico. O `--no-build-isolation` é crucial: força a compilação usando as bibliotecas já instaladas, evitando conflitos de versão.

**Por que não `pip install clip`?** A versão do PyPI do CLIP tem problemas de compilação no Colab. A instalação via GitHub com `--no-build-isolation` resolve isso.

#### Vacina 2: Numpy

```python
!python3.10 -m pip uninstall -y scikit-image numpy scipy
```
Remove completamente as versões atuais (que podem ser v2+).

```python
!python3.10 -m pip install "numpy<2.0.0" "scikit-image<0.23.0" "scipy<1.13.0"
```
Instala versões específicas que são compatíveis com o Forge:
- `numpy<2.0.0`: Numpy v1.x (evita erro de C-header `numpy.dtype size changed`)
- `scikit-image<0.23.0`: compatível com Numpy 1.x
- `scipy<1.13.0`: compatível com Numpy 1.x

**O erro original:** O Colab atualiza o Numpy para v2+, que muda o tamanho de estruturas C internas. Bibliotecas como scikit-image foram compiladas para v1.x e quebram com a mudança.

#### Vacina 3: ReActor

```python
!python3.10 -m pip install -q joblib insightface
```
- `joblib`: usado para misturar bordas em inpainting
- `insightface`: biblioteca de reconhecimento facial, necessária para o ReActor (face swap)

---

## Célula 4: Central de Downloads e Arquivos

**Propósito:** Interface gráfica interativa para download, upload e gerenciamento de modelos. Esta é a célula mais complexa do notebook.

> **Nota:** Esta célula é grande (~200 linhas). A documentação completa está em [03-interface-widgets.md](./03-interface-widgets.md).

### Resumo

A Central de Downloads tem 3 abas:

1. **📥 Baixar (Internet):** Adicione URLs de modelos e baixe diretamente para o Drive
2. **📤 Upload (PC Local):** Envie arquivos do seu computador para o Drive
3. **📁 Gerenciar Arquivos:** Visualize, substitua ou apague modelos existentes

### Código Completo

```python
import ipywidgets as widgets
from IPython.display import display, clear_output
import os
import subprocess
import time

pasta_base = '/content/drive/MyDrive/Stable_Diffusion_Dados'
pasta_modelos, pasta_loras, pasta_vaes, pasta_text_encoders = f"{pasta_base}/Modelos_Base", f"{pasta_base}/LoRAs", f"{pasta_base}/VAEs", f"{pasta_base}/Text_Encoders"
caixa_api_key = widgets.Password(description='API Key:', placeholder='Cole sua chave do Civitai aqui(c3aeb29fccd6c6417a7a30b126b91a4d)', layout=widgets.Layout(width='400px'))
api_box = widgets.HBox([caixa_api_key])

lista_arquivos = widgets.VBox([])

def criar_linha_download():
    # Adicionado Text Encoder no Dropdown
    tipo = widgets.Dropdown(options=['Model / Checkpoint', 'LoRA', 'VAE', 'Text Encoder'], value='Model / Checkpoint', layout=widgets.Layout(width='180px'))
    link = widgets.Text(placeholder='Cole o link do download', layout=widgets.Layout(width='300px'))
    nome = widgets.Text(placeholder='ex: modelo.safetensors', layout=widgets.Layout(width='200px'))
    btn_remover = widgets.Button(description='❌', button_style='danger', layout=widgets.Layout(width='40px'))
    linha = widgets.HBox([tipo, link, nome, btn_remover])
    def remover(b): lista_arquivos.children = [c for c in lista_arquivos.children if c != linha]
    btn_remover.on_click(remover)
    return linha

lista_arquivos.children = [criar_linha_download()]
btn_adicionar = widgets.Button(description='➕ Adicionar Arquivo', button_style='info', layout=widgets.Layout(width='200px'))
btn_baixar = widgets.Button(description='⬇️ Baixar Tudo Agora', button_style='success', layout=widgets.Layout(width='200px'))
saida_log = widgets.Output()

def adicionar_linha(b): lista_arquivos.children = list(lista_arquivos.children) + [criar_linha_download()]
btn_adicionar.on_click(adicionar_linha)

def iniciar_download(b):
    with saida_log:
        clear_output()
        print("🚀 Iniciando processamento da fila...\n")
        chave_api = caixa_api_key.value.strip()
        for linha in lista_arquivos.children:
            tipo, url_original, nome = linha.children[0].value, linha.children[1].value.strip(), linha.children[2].value.strip()
            if not url_original or not nome: continue
            url_final = f"{url_original}{'&' if '?' in url_original else '?'}token={chave_api}" if chave_api else url_original

            # Roteamento inteligente de pastas
            if tipo == 'Model / Checkpoint': pasta_destino = pasta_modelos
            elif tipo == 'LoRA': pasta_destino = pasta_loras
            elif tipo == 'VAE': pasta_destino = pasta_vaes
            else: pasta_destino = pasta_text_encoders

            caminho_completo = f"{pasta_destino}/{nome}"
            print(f"⏳ Baixando: {nome}...")
            resultado = subprocess.run(['wget', '-q', '--show-progress', '-O', caminho_completo, url_final])
            if resultado.returncode == 0 and os.path.exists(caminho_completo) and os.path.getsize(caminho_completo) > 50000:
                print(f"✅ SUCESSO!\n")
            else:
                print(f"❌ ERRO. Link quebrado ou sem permissão. Arquivo apagado.\n")
                if os.path.exists(caminho_completo): os.remove(caminho_completo)
        print("🎉 FILA CONCLUÍDA!")
        atualizar_gerenciador()

btn_baixar.on_click(iniciar_download)
box_downloader = widgets.VBox([widgets.HTML("<p>Adicione links para salvar novos arquivos diretamente no Drive:</p>"), lista_arquivos, widgets.HBox([btn_adicionar, btn_baixar]), saida_log])
out_gerenciador = widgets.Output()

def listar_arquivos(pasta):
    if not os.path.exists(pasta): return []
    return [{'nome': f, 'caminho': os.path.join(pasta, f), 'tamanho': os.path.getsize(os.path.join(pasta, f)) / (1024 * 1024)} for f in os.listdir(pasta) if os.path.isfile(os.path.join(pasta, f))]

def atualizar_gerenciador():
    with out_gerenciador:
        clear_output()
        display(widgets.HTML("<p>Visualize, substitua ou apague arquivos que já estão salvos no seu espaço:</p>"))

        # Loop atualizado para ler, atualizar e deletar os Text Encoders
        for titulo, pasta in [("Modelos Base (Checkpoints)", pasta_modelos), ("LoRAs", pasta_loras), ("VAEs", pasta_vaes), ("Text Encoders", pasta_text_encoders)]:
            display(widgets.HTML(f"<h4>{titulo}</h4>"))
            arquivos = listar_arquivos(pasta)
            if not arquivos:
                display(widgets.HTML("<i>Nenhum arquivo encontrado.</i>"))
                continue
            for arq in arquivos:
                lbl_nome = widgets.Label(f"📄 {arq['nome']} ({arq['tamanho']:.1f} MB)", layout=widgets.Layout(width='320px'))
                txt_link_sub = widgets.Text(placeholder='Cole o novo link aqui', layout=widgets.Layout(width='180px'))
                btn_sub = widgets.Button(description='🔄 Substituir', button_style='warning', layout=widgets.Layout(width='100px'))
                btn_del = widgets.Button(description='🗑️ Apagar', button_style='danger', layout=widgets.Layout(width='90px'))
                box_confirmacao = widgets.HBox([])
                linha = widgets.HBox([lbl_nome, txt_link_sub, btn_sub, btn_del, box_confirmacao])

                def criar_evento_apagar(path, box, btn_d, btn_s):
                    def ao_clicar_apagar(b):
                        btn_sim, btn_nao = widgets.Button(description='✅ Confirmar', button_style='success', layout=widgets.Layout(width='100px')), widgets.Button(description='❌ Cancelar', button_style='danger', layout=widgets.Layout(width='90px'))
                        def ao_confirmar(bs): os.remove(path); atualizar_gerenciador()
                        def ao_cancelar(bn): box.children = []; btn_d.disabled = False; btn_s.disabled = False
                        btn_sim.on_click(ao_confirmar); btn_nao.on_click(ao_cancelar)
                        btn_d.disabled, btn_s.disabled = True, True
                        box.children = [widgets.Label("Tem certeza?"), btn_sim, btn_nao]
                    return ao_clicar_apagar
                btn_del.on_click(criar_evento_apagar(arq['caminho'], box_confirmacao, btn_del, btn_sub))

                def criar_evento_substituir(path, txt, nome):
                    def ao_clicar_substituir(b):
                        url = txt.value.strip()
                        if not url: txt.placeholder = "⚠️ Cole um link primeiro!"; return
                        with out_gerenciador:
                            clear_output()
                            print(f"🔄 Iniciando a substituição de '{nome}'...\n")
                            chave = caixa_api_key.value.strip()
                            url_final = f"{url}{'&' if '?' in url else '?'}token={chave}" if chave else url
                            print("🗑️ 1. Apagando a versão antiga..."); os.remove(path)
                            print("⏳ 2. Baixando a nova versão...")
                            resultado = subprocess.run(['wget', '-q', '--show-progress', '-O', path, url_final])
                            if resultado.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 50000: print("\n✅ Substituição concluída com perfeição!")
                            else: print("\n❌ Erro no download.")
                            time.sleep(3); atualizar_gerenciador()
                    return ao_clicar_substituir
                btn_sub.on_click(criar_evento_substituir(arq['caminho'], txt_link_sub, arq['nome']))
                display(linha)

atualizar_gerenciador()
abas = widgets.Tab(children=[box_downloader, out_gerenciador])
abas.set_title(0, '📥 Baixar Novos Arquivos')
abas.set_title(1, '📁 Gerenciar Meus Arquivos')
display(widgets.HTML("<h2>🎛️ Central de Modelos Civitai</h2>"), api_box, abas)
```

> Para análise detalhada de cada widget e callback, veja [03-interface-widgets.md](./03-interface-widgets.md).

---

## Célula 5.5: O Cofre de Extensões (Instalação Automática)

**Propósito:** Instalar extensões do Forge automaticamente via `git clone`.

### Código Completo

```python
import os

# O caminho raiz onde o Forge guarda os plugins
pasta_extensoes = '/content/stable-diffusion-webui-forge/extensions'

# 📋 SUA LISTA DE EXTENSÕES (Basta adicionar novos links do GitHub aqui no futuro)
extensoes = [
    "https://github.com/BlafKing/sd-civitai-browser-plus", # O Assistente Autônomo do Civitai
    "https://github.com/Gourieff/sd-webui-reactor"         # ReActor (Consistência de Rosto e Face Swap)
]

print("🔌 ETAPA 5.5: INSTALADOR AUTOMÁTICO DE EXTENSÕES...")
print("="*70)

# Garante que a pasta existe antes de tentar instalar
if not os.path.exists(pasta_extensoes):
    os.makedirs(pasta_extensoes)

os.chdir(pasta_extensoes)

# Loop inteligente que baixa as extensões (e pula as que já estão lá para não dar erro)
for url in extensoes:
    nome_extensao = url.split('/')[-1]
    caminho_ext = os.path.join(pasta_extensoes, nome_extensao)

    if os.path.exists(caminho_ext):
        print(f"   [+] Extensão já conectada: {nome_extensao}")
    else:
        print(f"   [⬇️] Clonando repositório: {nome_extensao}...")
        os.system(f"git clone -q {url}")

print("="*70)
print("✅ Todas as extensões foram injetadas com sucesso! O motor já pode ser ligado.")
```

### Explicação Linha a Linha

```python
pasta_extensoes = '/content/stable-diffusion-webui-forge/extensions'
```
Caminho padrão onde o Forge busca extensões.

```python
extensoes = [
    "https://github.com/BlafKing/sd-civitai-browser-plus",
    "https://github.com/Gourieff/sd-webui-reactor"
]
```
Lista de repositórios GitHub das extensões. Para adicionar novas extensões, basta incluir a URL aqui.

```python
for url in extensoes:
    nome_extensao = url.split('/')[-1]
    caminho_ext = os.path.join(pasta_extensoes, nome_extensao)

    if os.path.exists(caminho_ext):
        print(f"   [+] Extensão já conectada: {nome_extensao}")
    else:
        print(f"   [⬇️] Clonando repositório: {nome_extensao}...")
        os.system(f"git clone -q {url}")
```
Loop que:
1. Extrai o nome da extensão da URL (último segmento)
2. Verifica se já existe (evita erro de clone duplicado)
3. Se não existe, clona silenciosamente (`-q` = quiet)

---

## Célula 6/5: A Ignição (Boot Adaptativo)

**Propósito:** Autodiagnóstico final, correção automática de problemas e lançamento do Forge com link público.

> **Nota:** Esta é a célula mais longa e complexa. Ela faz verificações de segurança antes de ligar o motor.

### Código Completo

```python
import os
import subprocess
import multiprocessing
import sys

print("🚀 ETAPA 6: CHECKLIST DE PRÉ-IGNIÇÃO E DIAGNÓSTICO...")
print("="*70)

alertas_nao_fatais = []
erros_fatais = []
ferramentas_ativas = ["WebUI Forge (Core)", "Python 3.10 (Forçado)"]

# ==========================================
# 1. AUTODIAGNÓSTICO E CORREÇÕES DE PACOTES
# ==========================================
print("🔍 1. Verificando integridade das dependências vitais...")

# Verificando PIP no Python 3.10
try:
    subprocess.run(["python3.10", "-m", "pip", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("   [+] Instalador PIP: OK")
except subprocess.CalledProcessError:
    print("   [!] Instalador PIP corrompido ou ausente. Aplicando autocorreção silenciosa...")
    os.system("curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10 > /dev/null 2>&1")
    ferramentas_ativas.append("PIP (Recuperado)")

# Verificando CLIP
try:
    import clip
    print("   [+] Interpretador CLIP: OK")
except ImportError:
    print("   [!] CLIP ausente. Reaplicando ferramentas de compilação...")
    os.system("python3.10 -m pip install -q --upgrade pip setuptools wheel")
    os.system("python3.10 -m pip install -q ftfy regex tqdm")
    os.system("python3.10 -m pip install -q https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip --no-build-isolation")
    ferramentas_ativas.append("OpenAI CLIP (Vacinado)")

# ⚠️ A ORDEM DE RESTRIÇÃO DO PIP (A Solução Definitiva)
print("   [!] Aplicando blindagem matemática com Ordem de Restrição Global (PIP_CONSTRAINT)...")
with open('/content/restricao_pip.txt', 'w') as f:
    f.write("numpy<2.0.0\nscikit-image<0.23.0\nscipy<1.13.0\n")
os.environ["PIP_CONSTRAINT"] = "/content/restricao_pip.txt"

os.system("python3.10 -m pip uninstall -y scikit-image numpy scipy > /dev/null 2>&1")
os.system("python3.10 -m pip install -q \"numpy<2.0.0\" \"scikit-image<0.23.0\" \"scipy<1.13.0\" insightface joblib")
ferramentas_ativas.append("Numpy Clássico (Bloqueado por Restrição)")
ferramentas_ativas.append("Insightface (Ativo)")

# ==========================================
# 2. ANÁLISE DE HARDWARE E AVISOS (BOTTLENECKS)
# ==========================================
hardware = os.environ.get('HARDWARE_TYPE', 'UNKNOWN')
gpu_name = "Nenhuma (Renderização por Processador)"
vram_total = 0

if hardware == "TPU":
    erros_fatais.append("Hardware Incompatível: O Google Colab alocou uma TPU. O Forge exige tecnologia CUDA (Nvidia).")
else:
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            ferramentas_ativas.append("PyTorch com Aceleração CUDA")

            if "T4" in gpu_name or "G4" in gpu_name:
                alertas_nao_fatais.append(f"Gargalo de Memória (VRAM): Sua GPU ({gpu_name}) possui apenas {vram_total:.1f}GB. Para usar o modelo FLUX sem travar, baixe EXCLUSIVAMENTE versões compactadas (FP8).")
        else:
            raise ImportError
    except ImportError:
        alertas_nao_fatais.append("Aceleração Gráfica Ausente: Você está rodando no modo CPU. A geração será EXTREMAMENTE LENTA.")

        arquivo_mem = '/content/stable-diffusion-webui-forge/backend/memory_management.py'
        if os.path.exists(arquivo_mem):
            with open(arquivo_mem, 'r') as f: cod = f.read()
            if "DummyProp" not in cod:
                fake_gpu = 'type("DummyProp", (object,), {"total_memory": 32*1024*1024*1024, "major": 8, "minor": 0, "name": "CPU-Hacker-GPU"})()'
                cod = cod.replace("torch.cuda.current_device()", "'cpu'")
                cod = cod.replace("torch.cuda.get_device_properties(device).total_memory", "(32 * 1024 * 1024 * 1024)")
                cod = cod.replace("torch.cuda.get_device_properties(device)", fake_gpu)
                cod = cod.replace('torch.cuda.get_device_properties("cuda")', fake_gpu)
                cod = cod.replace("torch.cuda.mem_get_info(device)", "((32 * 1024 * 1024 * 1024), (32 * 1024 * 1024 * 1024))")
                with open(arquivo_mem, 'w') as f: f.write(cod)

# ==========================================
# 3. RELATÓRIO FINAL DO AMBIENTE
# ==========================================
print("\n" + "="*70)
print("📊 RELATÓRIO DO SISTEMA DO ESTÚDIO")
print("="*70)
print(f"🖥️ Acelerador Gráfico : {gpu_name}")
if vram_total > 0:
    print(f"💾 Memória de Vídeo   : {vram_total:.1f} GB VRAM")
print(f"⚙️ Processador (CPU)  : {multiprocessing.cpu_count()} Núcleos Lógicos alocados")
print(f"🧰 Ferramentas Base   : {', '.join(ferramentas_ativas)}")
print("="*70)

if erros_fatais:
    print("\n❌ ERRO CRÍTICO ENCONTRADO (Ignição Abortada):")
    for erro in erros_fatais:
        print(f"   ► {erro}")
else:
    if alertas_nao_fatais:
        print("\n⚠️ AVISOS DE PERFORMANCE:")
        for aviso in alertas_nao_fatais:
            print(f"   ► {aviso}")

    print("\n🌐 INICIANDO O SERVIDOR...")
    print("   [+] O link público da interface será gerado logo abaixo.")
    print("   [+] Procure pela URL azul terminando em 'gradio.live'. Clique nela para abrir o estúdio!")
    print("-" * 70 + "\n")

    argumentos = os.environ.get('FORGE_ARGS', '--theme dark')
    os.chdir('/content/stable-diffusion-webui-forge')
    os.environ["MPLBACKEND"] = "agg"

    !python3.10 launch.py {argumentos} --share --enable-insecure-extension-access
```

### Explicação por Seção

#### Seção 1: Autodiagnóstico

```python
try:
    subprocess.run(["python3.10", "-m", "pip", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("   [+] Instalador PIP: OK")
except subprocess.CalledProcessError:
    print("   [!] Instalador PIP corrompido ou ausente. Aplicando autocorreção silenciosa...")
    os.system("curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10 > /dev/null 2>&1")
```
Verifica se o PIP funciona no Python 3.10. Se não, reinstala automaticamente.

```python
try:
    import clip
    print("   [+] Interpretador CLIP: OK")
except ImportError:
    print("   [!] CLIP ausente. Reaplicando ferramentas de compilação...")
    os.system("python3.10 -m pip install -q --upgrade pip setuptools wheel")
    os.system("python3.10 -m pip install -q ftfy regex tqdm")
    os.system("python3.10 -m pip install -q https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip --no-build-isolation")
```
Tenta importar o CLIP. Se falhar, reinstala tudo do zero (inclusive setuptools e wheel que são necessários para compilar).

#### PIP_CONSTRAINT: A Blindagem Matemática

```python
with open('/content/restricao_pip.txt', 'w') as f:
    f.write("numpy<2.0.0\nscikit-image<0.23.0\nscipy<1.13.0\n")
os.environ["PIP_CONSTRAINT"] = "/content/restricao_pip.txt"
```
Cria um arquivo de restrições e injeta no PIP via variável de ambiente. Isso impede que **qualquer** instalação futura de pacote atualize o Numpy para v2+.

**Por que é necessário?** Mesmo que a Célula 3 já tenha feito o downgrade, alguma dependência do Forge pode tentar atualizar o Numpy de volta. O PIP_CONSTRAINT é uma proteção global.

#### Seção 2: Análise de Hardware

```python
if hardware == "TPU":
    erros_fatais.append("Hardware Incompatível: O Google Colab alocou uma TPU.")
```
TPU não é compatível com CUDA. Se detectada, o sistema aborta.

```python
if "T4" in gpu_name or "G4" in gpu_name:
    alertas_nao_fatais.append(f"Gargalo de Memória (VRAM): Sua GPU ({gpu_name}) possui apenas {vram_total:.1f}GB...")
```
Se a GPU for T4 (~15 GB VRAM), avisa sobre limitações de memória.

#### Hack de Memória para CPU

```python
arquivo_mem = '/content/stable-diffusion-webui-forge/backend/memory_management.py'
if os.path.exists(arquivo_mem):
    with open(arquivo_mem, 'r') as f: cod = f.read()
    if "DummyProp" not in cod:
        fake_gpu = 'type("DummyProp", (object,), {"total_memory": 32*1024*1024*1024, "major": 8, "minor": 0, "name": "CPU-Hacker-GPU"})()'
        cod = cod.replace("torch.cuda.current_device()", "'cpu'")
        cod = cod.replace("torch.cuda.get_device_properties(device).total_memory", "(32 * 1024 * 1024 * 1024)")
        cod = cod.replace("torch.cuda.get_device_properties(device)", fake_gpu)
        cod = cod.replace('torch.cuda.get_device_properties("cuda")', fake_gpu)
        cod = cod.replace("torch.cuda.mem_get_info(device)", "((32 * 1024 * 1024 * 1024), (32 * 1024 * 1024 * 1024))")
        with open(arquivo_mem, 'w') as f: f.write(cod)
```
**O que faz:** Modifica o arquivo `memory_management.py` do Forge para "enganar" o sistema, fazendo-o pensar que tem 32 GB de VRAM quando está rodando em CPU.

**Por quê?** O Forge verifica a VRAM disponível e se recusa a carregar modelos se achar que não há memória suficiente. Este hack permite que ele tente rodar em CPU (lentamente, mas funciona).

#### Seção 3: Lançamento

```python
argumentos = os.environ.get('FORGE_ARGS', '--theme dark')
```
Recupera os argumentos de otimização definidos (se a Célula de Hardware foi executada).

```python
os.environ["MPLBACKEND"] = "agg"
```
Impede o Colab de tentar desenhar gráficos matplotlib na tela (economiza recursos).

```python
!python3.10 launch.py {argumentos} --share --enable-insecure-extension-access
```
Inicia o Forge com:
- `{argumentos}`: flags de otimização (ex: `--always-offload-from-vram` para T4)
- `--share`: gera link público Gradio
- `--enable-insecure-extension-access`: permite extensões de terceiros

---

## Voltar para o índice

[← Arquitetura](./01-arquitetura.md) | [Interface de Widgets →](./03-interface-widgets.md)
