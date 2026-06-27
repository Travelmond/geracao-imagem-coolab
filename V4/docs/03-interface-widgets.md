# Interface de Widgets (Central de Modelos)

Documentação completa da interface interativa construída com `ipywidgets` na Célula 4 do notebook. Esta é a "Central de Modelos Civitai" — o painel de controle para gerenciar todos os modelos de IA.

---

## Visão Geral da Interface

```
┌──────────────────────────────────────────────────────────────────┐
│                 🎛️ Central de Modelos Civitai                    │
├──────────────────────────────────────────────────────────────────┤
│  API Key: [••••••••••••••••••••]                                 │
├──────────────────────────────────────────────────────────────────┤
│  [📥 Baixar Novos Arquivos] [📁 Gerenciar Meus Arquivos]        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  (Conteúdo da aba selecionada)                                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Widgets

### Widget Raiz: `Tab` (Abas)

```python
abas = widgets.Tab(children=[box_downloader, out_gerenciador])
abas.set_title(0, '📥 Baixar Novos Arquivos')
abas.set_title(1, '📁 Gerenciar Meus Arquivos')
```

| Aba | Conteúdo | Propósito |
|-----|----------|-----------|
| 📥 Baixar Novos Arquivos | `box_downloader` (VBox) | Download de modelos via URL |
| 📁 Gerenciar Meus Arquivos | `out_gerenciador` (Output) | CRUD de modelos existentes |

---

## Componentes Globais

### API Key

```python
caixa_api_key = widgets.Password(
    description='API Key:',
    placeholder='Cole sua chave do Civitai aqui',
    layout=widgets.Layout(width='400px')
)
api_box = widgets.HBox([caixa_api_key])
```

- **Tipo:** `Password` (texto oculto)
- **Propósito:** Chave de autenticação do Civitai para downloads protegidos
- **Opcional:** Funciona sem ela para links diretos (HuggingFace, etc.)
- **Uso:** É injetada na URL como `?token=SUA_CHAVE` ou `&token=SUA_CHAVE`

---

## Aba 1: 📥 Baixar Novos Arquivos

### Estrutura Visual

```
┌──────────────────────────────────────────────────────────────────┐
│  Adicione links para salvar novos arquivos diretamente no Drive: │
├──────────────────────────────────────────────────────────────────┤
│  [Dropdown: Model/Checkpoint ▼] [Link do download        ]      │
│  [Nome do arquivo        ] [❌]                                  │
├──────────────────────────────────────────────────────────────────┤
│  [➕ Adicionar Arquivo]  [⬇️ Baixar Tudo Agora]                  │
├──────────────────────────────────────────────────────────────────┤
│  (Log de saída: progresso, sucesso, erros)                       │
└──────────────────────────────────────────────────────────────────┘
```

### Componentes

#### `lista_arquivos` — VBox Dinâmica

```python
lista_arquivos = widgets.VBox([])
```
Container vertical que armazena todas as linhas de download. Começa vazio e é preenchido dinamicamente.

#### `criar_linha_download()` — Linha de Download

```python
def criar_linha_download():
    tipo = widgets.Dropdown(
        options=['Model / Checkpoint', 'LoRA', 'VAE', 'Text Encoder'],
        value='Model / Checkpoint',
        layout=widgets.Layout(width='180px')
    )
    link = widgets.Text(
        placeholder='Cole o link do download',
        layout=widgets.Layout(width='300px')
    )
    nome = widgets.Text(
        placeholder='ex: modelo.safetensors',
        layout=widgets.Layout(width='200px')
    )
    btn_remover = widgets.Button(
        description='❌',
        button_style='danger',
        layout=widgets.Layout(width='40px')
    )
    linha = widgets.HBox([tipo, link, nome, btn_remover])
    def remover(b): lista_arquivos.children = [c for c in lista_arquivos.children if c != linha]
    btn_remover.on_click(remover)
    return linha
```

**Componentes da linha:**

| Widget | Tipo | Propósito |
|--------|------|-----------|
| `tipo` | Dropdown | Define para qual pasta o modelo será salvo |
| `link` | Text | URL do download (Civitai, HuggingFace, etc.) |
| `nome` | Text | Nome do arquivo (ex: `modelo.safetensors`) |
| `btn_remover` | Button | Remove esta linha da fila |

**Dropdown de tipos e roteamento:**

| Opção Selecionada | Pasta de Destino |
|-------------------|------------------|
| Model / Checkpoint | `Modelos_Base` |
| LoRA | `LoRAs` |
| VAE | `VAEs` |
| Text Encoder | `Text_Encoders` |

#### `btn_adicionar` — Botão Adicionar

```python
btn_adicionar = widgets.Button(
    description='➕ Adicionar Arquivo',
    button_style='info',
    layout=widgets.Layout(width='200px')
)
```

**Callback:**
```python
def adicionar_linha(b):
    lista_arquivos.children = list(lista_arquivos.children) + [criar_linha_download()]
btn_adicionar.on_click(adicionar_linha)
```
Adiciona uma nova linha vazia à `lista_arquivos`.

#### `btn_baixar` — Botão Baixar Tudo

```python
btn_baixar = widgets.Button(
    description='⬇️ Baixar Tudo Agora',
    button_style='success',
    layout=widgets.Layout(width='200px')
)
```

**Callback — `iniciar_download`:**

```python
def iniciar_download(b):
    with saida_log:
        clear_output()
        print("🚀 Iniciando processamento da fila...\n")
        chave_api = caixa_api_key.value.strip()
        for linha in lista_arquivos.children:
            tipo, url_original, nome = linha.children[0].value, linha.children[1].value.strip(), linha.children[2].value.strip()
            if not url_original or not nome: continue
            url_final = f"{url_original}{'&' if '?' in url_original else '?'}token={chave_api}" if chave_api else url_original

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
```

**Fluxo do download:**

1. Itera sobre todas as linhas da fila
2. Para cada linha: extrai tipo, URL e nome
3. Se a API Key estiver preenchida, injeta `?token=CHAVE` na URL
4. Roteia para a pasta correta baseado no tipo
5. Executa `wget` para download
6. Verifica se o download foi bem-sucedido (exit code 0 + arquivo > 50 KB)
7. Se falhou, apaga o arquivo parcial

#### `saida_log` — Output de Log

```python
saida_log = widgets.Output()
```
Widget de saída onde o progresso dos downloads é exibido.

---

## Aba 2: 📁 Gerenciar Meus Arquivos

### Estrutura Visual

```
┌──────────────────────────────────────────────────────────────────┐
│  Visualize, substitua ou apague arquivos que já estão salvos:    │
├──────────────────────────────────────────────────────────────────┤
│  Modelos Base (Checkpoints)                                      │
│  📄 Nova 3DCG XL.safetensors (6617.1 MB) [Link novo] [🔄] [🗑️] │
│  📄 FLUX.safetensors (22700.2 MB)         [Link novo] [🔄] [🗑️] │
│                                                                  │
│  LoRAs                                                           │
│  📄 BimboFLUX.safetensors (164.0 MB)     [Link novo] [🔄] [🗑️] │
│                                                                  │
│  VAEs                                                            │
│  📄 FLUX_VAE(ae).safetensors (319.8 MB)  [Link novo] [🔄] [🗑️] │
│                                                                  │
│  Text Encoders                                                   │
│  📄 clip_l.safetensors (234.7 MB)        [Link novo] [🔄] [🗑️] │
│  📄 t5xxl_fp16.safetensors (9334.4 MB)   [Link novo] [🔄] [🗑️] │
└──────────────────────────────────────────────────────────────────┘
```

### Funções Auxiliares

#### `listar_arquivos(pasta)`

```python
def listar_arquivos(pasta):
    if not os.path.exists(pasta): return []
    return [
        {
            'nome': f,
            'caminho': os.path.join(pasta, f),
            'tamanho': os.path.getsize(os.path.join(pasta, f)) / (1024 * 1024)
        }
        for f in os.listdir(pasta)
        if os.path.isfile(os.path.join(pasta, f))
    ]
```

**Retorna:** Lista de dicionários com:
- `nome`: nome do arquivo
- `caminho`: caminho completo no Drive
- `tamanho`: tamanho em MB

#### `atualizar_gerenciador()`

```python
def atualizar_gerenciador():
    with out_gerenciador:
        clear_output()
        display(widgets.HTML("<p>Visualize, substitua ou apague arquivos...</p>"))
        for titulo, pasta in [
            ("Modelos Base (Checkpoints)", pasta_modelos),
            ("LoRAs", pasta_loras),
            ("VAEs", pasta_vaes),
            ("Text Encoders", pasta_text_encoders)
        ]:
            display(widgets.HTML(f"<h4>{titulo}</h4>"))
            arquivos = listar_arquivos(pasta)
            if not arquivos:
                display(widgets.HTML("<i>Nenhum arquivo encontrado.</i>"))
                continue
            for arq in arquivos:
                # ... cria widgets para cada arquivo ...
```

**O que faz:** Percorre todas as 4 pastas, lista os arquivos e cria widgets interativos para cada um.

### Componentes por Arquivo

Para cada arquivo encontrado, são criados:

```python
lbl_nome = widgets.Label(f"📄 {arq['nome']} ({arq['tamanho']:.1f} MB)")
txt_link_sub = widgets.Text(placeholder='Cole o novo link aqui')
btn_sub = widgets.Button(description='🔄 Substituir', button_style='warning')
btn_del = widgets.Button(description='🗑️ Apagar', button_style='danger')
box_confirmacao = widgets.HBox([])
```

| Widget | Tipo | Propósito |
|--------|------|-----------|
| `lbl_nome` | Label | Exibe nome e tamanho do arquivo |
| `txt_link_sub` | Text | Campo para colar URL de substituição |
| `btn_sub` | Button | Inicia processo de substituição |
| `btn_del` | Button | Inicia processo de exclusão |
| `box_confirmacao` | HBox | Container para botões de confirmação |

---

## Callbacks e Eventos

### Callback: Apagar Arquivo

```python
def criar_evento_apagar(path, box, btn_d, btn_s):
    def ao_clicar_apagar(b):
        btn_sim = widgets.Button(description='✅ Confirmar', button_style='success')
        btn_nao = widgets.Button(description='❌ Cancelar', button_style='danger')

        def ao_confirmar(bs):
            os.remove(path)
            atualizar_gerenciador()

        def ao_cancelar(bn):
            box.children = []
            btn_d.disabled = False
            btn_s.disabled = False

        btn_sim.on_click(ao_confirmar)
        btn_nao.on_click(ao_cancelar)
        btn_d.disabled, btn_s.disabled = True, True
        box.children = [widgets.Label("Tem certeza?"), btn_sim, btn_nao]

    return ao_clicar_apagar
```

**Fluxo:**

```
Usuário clica [🗑️ Apagar]
       ↓
Botões [🔄] e [🗑️] ficam desabilitados
       ↓
Aparece: "Tem certeza?" [✅ Confirmar] [❌ Cancelar]
       ↓
[✅] → os.remove(path) → atualiza lista
[❌] → limpa confirmação → reabilita botões
```

### Callback: Substituir Arquivo

```python
def criar_evento_substituir(path, txt, nome):
    def ao_clicar_substituir(b):
        url = txt.value.strip()
        if not url:
            txt.placeholder = "⚠️ Cole um link primeiro!"
            return
        with out_gerenciador:
            clear_output()
            print(f"🔄 Iniciando a substituição de '{nome}'...\n")
            chave = caixa_api_key.value.strip()
            url_final = f"{url}{'&' if '?' in url else '?'}token={chave}" if chave else url
            print("🗑️ 1. Apagando a versão antiga...")
            os.remove(path)
            print("⏳ 2. Baixando a nova versão...")
            resultado = subprocess.run(['wget', '-q', '--show-progress', '-O', path, url_final])
            if resultado.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 50000:
                print("\n✅ Substituição concluída com perfeição!")
            else:
                print("\n❌ Erro no download.")
            time.sleep(3)
            atualizar_gerenciador()
    return ao_clicar_substituir
```

**Fluxo:**

```
Usuário cola URL no campo e clica [🔄 Substituir]
       ↓
Verifica se URL não está vazia
       ↓
1. Apaga o arquivo antigo (os.remove)
       ↓
2. Baixa o novo arquivo (wget)
       ↓
3. Verifica se download foi bem-sucedido
       ↓
4. Atualiza a lista de arquivos
```

---

## Variáveis de Estado

| Variável | Tipo | Propósito |
|----------|------|-----------|
| `lista_arquivos` | VBox | Armazena as linhas de download da Aba 1 |
| `caixa_api_key` | Password | API Key do Civitai (global, usada por ambas as abas) |
| `saida_log` | Output | Log de progresso da Aba 1 |
| `out_gerenciador` | Output | Container da Aba 2 |
| `pasta_modelos` | string | Caminho para `Modelos_Base` no Drive |
| `pasta_loras` | string | Caminho para `LoRAs` no Drive |
| `pasta_vaes` | string | Caminho para `VAEs` no Drive |
| `pasta_text_encoders` | string | Caminho para `Text_Encoders` no Drive |

---

## Diferenças entre Versões

| Aspecto | Versão Legada | Versão Melhorada |
|---------|--------------|------------------|
| Abas | 3 (Download, Upload, Gerenciar) | 2 (Download, Gerenciar) |
| Upload Nativo | Sim (aba separada) | Não |
| API Key | Opcional (sem placeholder de exemplo) | Placeholder mostra exemplo de chave |
| Civitai Detection | Verifica `if "civitai" in url` | Sempre injeta token se chave existe |
| Text Encoders | Gerenciamento incluído | Gerenciamento incluído |

---

## Voltar para o índice

[← Fluxo de Execução](./02-fluxo-de-execucao.md) | [Hardware e Otimização →](./04-hardware-otimizacao.md)
