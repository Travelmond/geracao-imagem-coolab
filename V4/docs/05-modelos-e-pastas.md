# Modelos e Estrutura de Pastas

Tipos de modelos utilizados, estrutura de armazenamento no Google Drive e como os symlinks conectam tudo.

---

## Tipos de Modelos

### 1. Checkpoints (Modelos Base)

O "cérebro" principal da IA. Sem ele, nada funciona.

| Modelo | Tamanho | Tipo | Observação |
|--------|---------|------|-----------|
| `Nova 3DCG XL.safetensors` | 6.6 GB | SDXL | Modelo principal usado no projeto |
| `FLUX.safetensors` | 22.7 GB | FLUX | Modelo de alta qualidade, precisa FP8 na T4 |
| `waiIllustriousSDXL_v160.safetensors` | ~7 GB | SDXL | Estilo ilustração/anime |

### 2. LoRAs (Modificadores de Estilo)

Pequenos modelos que alteram o estilo, personagens ou características específicas.

| LoRA | Tamanho | Função |
|------|---------|--------|
| `BimboFLUX.safetensors` | 164 MB | Estilo específico |
| `Big Boobs FLUX.safetensors` | 18.4 MB | Modificador corporal |
| `Pokies.safetensors` | 18.4 MB | Modificador de vestuário |
| `Bombshell XL - big busty boobs - FLUX.safetensors` | 146.2 MB | Estilo combinado |
| `Satin mini dress.safetensors` | 18.4 MB | Vestuário específico |
| `Fantasy Wizard & Witches.safetensors` | 85.6 MB | Temática fantasia |
| `Hands XL + SD 1.5 + F1D + Pony + Illustrious + zit.safetensors` | 327.9 MB | Correção de mãos |
| `Supergirl PowerGirl DC (IL)..safetensors` | 162.7 MB | Personagem específico |

### 3. VAEs (Decodificadores)

Responsáveis por converter a imagem gerada de formato comprimido para pixels visíveis.

| VAE | Tamanho | Compatibilidade |
|-----|---------|-----------------|
| `FLUX_VAE(ae).safetensors` | 319.8 MB | FLUX |
| `sdxl vae.safetensors` | 319.1 MB | SDXL |
| `kl f8 anime2.vae.safetensors` | 385.8 MB | SDXL (estilo anime) |

### 4. Text Encoders (Codificadores de Texto)

Convertem o prompt (texto) em vetores numéricos que a IA entende.

| Text Encoder | Tamanho | Tipo | Compatibilidade |
|-------------|---------|------|-----------------|
| `clip_l.safetensors` | 234.7 MB | CLIP | SD 1.5, SDXL |
| `t5xxl_fp8.safetensors` | 4.7 GB | T5 (FP8) | FLUX (recomendado para T4) |
| `t5xxl_fp16.safetensors` | 9.3 GB | T5 (FP16) | FLUX (precisa A100) |

---

## Estrutura de Pastas no Google Drive

```
/content/drive/MyDrive/
└── Stable_Diffusion_Dados/
    ├── Modelos_Base/          ← Checkpoints (2-25 GB cada)
    │   ├── Nova 3DCG XL.safetensors
    │   ├── FLUX.safetensors
    │   └── waiIllustriousSDXL_v160.safetensors
    │
    ├── LoRAs/                 ← Modificadores de estilo (10-500 MB cada)
    │   ├── BimboFLUX.safetensors
    │   ├── Big Boobs FLUX.safetensors
    │   └── ...
    │
    ├── VAEs/                  ← Decodificadores (300-400 MB cada)
    │   ├── FLUX_VAE(ae).safetensors
    │   ├── sdxl vae.safetensors
    │   └── kl f8 anime2.vae.safetensors
    │
    ├── Text_Encoders/         ← Codificadores de texto (200 MB - 9 GB)
    │   ├── clip_l.safetensors
    │   ├── t5xxl_fp8.safetensors
    │   └── t5xxl_fp16.safetensors
    │
    └── Imagens_Geradas/       ← Output das imagens criadas
        └── (imagens salvas pelo Forge)
```

---

## Symlinks (Conexão Forge ↔ Drive)

Os symlinks são a "cola" que conecta o Forge (memória temporária) ao Drive (persistente).

### Mapa Completo

| Caminho no Forge (temporário) | Aponta para (Drive) |
|------------------------------|---------------------|
| `/content/stable-diffusion-webui-forge/models/Stable-diffusion` | `Stable_Diffusion_Dados/Modelos_Base` |
| `/content/stable-diffusion-webui-forge/models/Lora` | `Stable_Diffusion_Dados/LoRAs` |
| `/content/stable-diffusion-webui-forge/models/VAE` | `Stable_Diffusion_Dados/VAEs` |
| `/content/stable-diffusion-webui-forge/models/text_encoder` | `Stable_Diffusion_Dados/Text_Encoders` |
| `/content/stable-diffusion-webui-forge/outputs` | `Stable_Diffusion_Dados/Imagens_Geradas` |

### Como Funcionam

```bash
# Remove a pasta padrão do Forge
rm -rf /content/stable-diffusion-webui-forge/models/Stable-diffusion

# Cria symlink apontando para o Drive
ln -s /content/drive/MyDrive/Stable_Diffusion_Dados/Modelos_Base \
      /content/stable-diffusion-webui-forge/models/Stable-diffusion
```

**Resultado:** Quando o Forge procura modelos em `models/Stable-diffusion`, ele encontra os arquivos do Drive automaticamente, como se estivessem na pasta local.

### Por Que Usar symlinks?

1. **Persistência:** Modelos ficam salvos no Drive entre sessões do Colab
2. **Economia de espaço:** Não duplica arquivos (a VRAM é o recurso mais escasso)
3. **Transparência:** O Forge não precisa de modificações — ele "vê" os modelos onde espera
4. **Imagens salvas:** As imagens geradas vão direto para o Drive (não se perdem)

---

## Extensores de Arquivo

| Extensão | Formato | Segurança | Uso |
|----------|---------|-----------|-----|
| `.safetensors` | Safetensors | Seguro (sem código executável) | Padrão atual |
| `.ckpt` | Checkpoint | Inseguro (pode conter código) | Legado |
| `.pt` | PyTorch | Variável | Alguns modelos específicos |
| `.pth` | PyTorch | Variável | Pesos de treinamento |

**Recomendação:** Use sempre `.safetensors` quando disponível.

---

## Voltar para o índice

[← Hardware e Otimização](./04-hardware-otimizacao.md) | [Dependências e Patches →](./06-dependencias-e-patches.md)
