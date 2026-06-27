# Glossário de Termos Técnicos

Termos e conceitos utilizados neste projeto e no ecossistema de geração de imagens por IA.

---

## Modelos e Arquivos

### Checkpoint (Modelo Base)
O arquivo principal que contém os "pesos" treinados da rede neural. É o "cérebro" da IA que sabe gerar imagens. Sem ele, nada funciona.

- **Formato:** `.safetensors` (seguro, sem código executável) ou `.ckpt` (legado, menos seguro)
- **Tamanho:** Geralmente entre 2 GB e 25 GB
- **Exemplos no projeto:** `Nova 3DCG XL.safetensors`, `FLUX.safetensors`, `waiIllustriousSDXL_v160.safetensors`

### LoRA (Low-Rank Adaptation)
Um "modificador" pequeno que altera o comportamento do checkpoint base. Pense como um "filtro" ou "estilo" aplicado sobre o modelo principal.

- **Formato:** `.safetensors`
- **Tamanho:** Geralmente entre 10 MB e 500 MB
- **Uso:** Estilos artísticos, personagens específicos, roupas, poses
- **Exemplos no projeto:** `BimboFLUX.safetensors`, `Supergirl PowerGirl DC (IL)..safetensors`

### VAE (Variational Autoencoder)
Responsável por **decodificar** a imagem gerada de formato comprimido para pixels visíveis. Afeta a qualidade de cores e detalhes finos.

- **Formato:** `.safetensors` ou `.vae.safetensors`
- **Tamanho:** Geralmente entre 300 MB e 400 MB
- **Exemplos no projeto:** `FLUX_VAE(ae).safetensors`, `sdxl vae.safetensors`, `kl f8 anime2.vae.safetensors`

### Text Encoder (Codificador de Texto)
Converte o prompt (texto descritivo) em números que a IA entende. É a "ponte" entre linguagem humana e matemática da IA.

- **Formato:** `.safetensors`
- **Tamanho:** Pode chegar a 9 GB (versão FP16 do T5)
- **Tipos principais:**
  - **CLIP:** Usado por modelos SD 1.5 e SDXL
  - **T5:** Usado pelo modelo FLUX (mais potente)
- **Exemplos no projeto:** `clip_l.safetensors`, `t5xxl_fp8.safetensors`, `t5xxl_fp16.safetensors`

### safetensors
Formato de arquivo desenvolvido pela HuggingFace para armazenar tensores (pesos de modelos) de forma segura. Diferente do `.ckpt`, não permite execução de código arbitrário, evitando ataques.

---

## Tecnologias e Ferramentas

### Stable Diffusion
Algoritmo de geração de imagens por difusão. A base tecnológica que permite criar imagens a partir de texto.

### WebUI Forge
Interface web para Stable Diffusion criada por lllyasviel. É uma versão otimizada do Automatic1111, com melhor gestão de memória VRAM. É o software que este projeto instala e executa.

- **Repositório:** [github.com/lllyasviel/stable-diffusion-webui-forge](https://github.com/lllyasviel/stable-diffusion-webui-forge)

### Gradio
Framework Python que cria interfaces web interativas. O Forge usa Gradio para renderizar a interface do usuário no navegador.

- **Link público:** Gerado via `--share`, termina em `.gradio.live`
- **Validade:** 72 horas (renovável)

### Google Colab
Plataforma de notebooks Jupyter do Google que fornece GPUs gratuitas (T4, L4) e pagas (A100, H100).

### ipywidgets
Biblioteca Python para criar elementos interativos (botões, dropdowns, campos de texto) dentro de notebooks Jupyter. Usada neste projeto para a "Central de Modelos".

### symlinks (Symbolic Links)
Atalhos do sistema operacional que apontam de uma pasta para outra. Neste projeto, usados para que o Forge leia/escreva arquivos diretamente no Google Drive, em vez da memória temporária do Colab.

```bash
# Exemplo: a pasta "Stable-diffusion" do Forge aponta para "Modelos_Base" no Drive
ln -s /content/drive/MyDrive/Stable_Diffusion_Dados/Modelos_Base /content/stable-diffusion-webui-forge/models/Stable-diffusion
```

---

## Conceitos de IA

### Prompt
Texto descritivo que diz à IA o que gerar. Exemplo: `a beautiful landscape, mountains, sunset, 8k, detailed`.

### Negative Prompt
Texto que diz à IA o que **evitar**. Exemplo: `blurry, low quality, deformed hands`.

### Difusão (Diffusion)
Processo de geração de imagem: a IA começa com ruído aleatório e vai "refinando" passo a passo até formar a imagem descrita no prompt.

### Steps (Passos)
Número de iterações de refinamento da difusão. Mais steps = mais detalhes, mas mais lento. Valores típicos: 20-50.

### CFG Scale (Classifier-Free Guidance)
Controla o quão fiel a IA é ao prompt. Valores altos = mais fiel, mas pode gerar artefatos. Valores típicos: 5-15.

### Sampler
Algoritmo matemático que controla como a difusão acontece. Exemplos: Euler a, DPM++ 2M Karras, UniPC.

### Seed
Número aleatório que determina o ponto de partida da geração. Mesmo seed + mesmo prompt = mesma imagem.

---

## Precisão Numérica

### FP32 (Float 32 bits)
Precisão total. Usa o dobro de VRAM comparado ao FP16. Necessário quando a GPU não suporta FP16.

### FP16 (Float 16 bits)
Metade da precisão, metade da VRAM. Padrão para GPUs modernas com suporte a half-precision.

### FP8 (Float 8 bits)
Compressão ainda maior. Essencial para GPUs com pouca VRAM (como a T4 com 15 GB) rodarem modelos grandes como FLUX.

---

## Hardware

### GPU (Graphics Processing Unit)
Placa de vídeo usada para acelerar a geração de imagens. Quanto mais VRAM, maior o modelo que cabe.

### VRAM (Video RAM)
Memória da placa de vídeo. É o recurso mais limitante. A T4 tem ~15 GB, a A100 tem ~40-80 GB.

### CUDA
Framework da NVIDIA que permite usar a GPU para cálculos paralelos. O PyTorch usa CUDA para acelerar a IA.

### TPU (Tensor Processing Unit)
Processador especializado do Google para IA. **Não é compatível** com o Forge (exige CUDA/NVIDIA).

### Offload
Técnica de mover partes do modelo da VRAM para a RAM quando a VRAM não é suficiente. Mais lento, mas evita erro de memória.

---

## Extensões

### CivitAI Browser+
Extensão do Forge que permite navegar e baixar modelos diretamente do site Civitai pela interface do Forge.

### ReActor
Extensão para troca de rostos (face swap) e consistência de personagens. Usa Insightface para detecção facial.

### Insightface
Biblioteca de mapeamento facial usada pelo ReActor para detectar e trocar rostos em imagens.

### ControlNet
Extensão que permite guiar a geração com imagens de referência (pose, bordas, profundidade).

---

## API e Downloads

### Civitai
Plataforma de compartilhamento de modelos de IA. Requer API Key para downloads autenticados.

### API Key (Token)
Chave de autenticação do Civitai. Neste projeto, injetada na URL como parâmetro `?token=SUA_CHAVE`.

### wget
Ferramenta de linha de comando para downloads. Usada neste projeto para baixar modelos via URL.

### PIP_CONSTRAINT
Variável de ambiente que força o PIP a respeitar restrições de versão. Usada para impedir que o Numpy seja atualizado para v2+.

---

## Termos do Forge

### Launch.py
Script principal que inicializa o WebUI Forge. Aceita argumentos de linha de comando para configurar o comportamento.

### `--share`
Argumento que gera um link público Gradio para acessar a interface de qualquer lugar.

### `--always-offload-from-vram`
Força o Forge a liberar VRAM após cada geração. Essencial para GPUs com pouca memória (T4).

### `--cuda-malloc` e `--cuda-stream`
Otimizações de memória CUDA para GPUs de alto desempenho (A100, H100).

### `--no-half`
Impede o uso de FP16, forçando FP32. Necessário quando a GPU não suporta half-precision (modo CPU).

### `--precision full`
Força precisão FP32 completa. Usado no modo CPU.

---

## Voltar para o índice

[← README](./README.md)
