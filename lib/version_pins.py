"""
version_pins.py — Central de Controle de Versões
=================================================

Todas as versões fixadas para compatibilidade no Google Colab.
Cada vacina do EnvironmentDoctor consulta este arquivo.

IMPORTANTE: Se o Colab mudar alguma versão padrão que quebre algo,
atualize APENAS este arquivo. Todo o resto se ajusta automaticamente.

Última atualização: 2026-06-27
Ambiente alvo: Google Colab (Python 3.12 padrão, instalamos 3.10)
"""

# ══════════════════════════════════════════════════════════════
# VERSÃO DO PYTHON
# ══════════════════════════════════════════════════════════════
# Forge requer Python 3.10.6. Colab default é 3.12.13 (desde 2026).
# Instalamos 3.10 via apt e usamos exclusivamente para o Forge.
PYTHON_TARGET = "3.10"
PYTHON_CMD = "python3.10"

# ══════════════════════════════════════════════════════════════
# VERSÕES FIXADAS (PIP)
# ══════════════════════════════════════════════════════════════

# --- Core: NumPy e dependentes ---
# NumPy 2.1+ quebra scikit-image, scipy, insightface (C-header mismatch).
# NumPy 2.0.x é aceito por PyTorch moderno e compatível com a maioria.
NUMPY_PIN = "<2.1.0"
SCIKIT_IMAGE_PIN = "<0.23.0"
SCIPY_PIN = "<2.0.0"

# --- CLIP (OpenAI) ---
# Instalado via GitHub (commit fixo) ou wheel pré-compilado.
# Dependências: ftfy, regex, tqdm
CLIP_GITHUB_COMMIT = "d50d76daa670286dd6cacf3bcd80b5e4823fc8e1"
CLIP_GITHUB_URL = (
    f"https://github.com/openai/CLIP/archive/"
    f"{CLIP_GITHUB_COMMIT}.zip"
)
CLIP_DEPS = ["ftfy", "regex", "tqdm"]
# setuptools<70 necessário para build do CLIP sem --no-build-isolation
SETUPTOOLS_PIN = "<70"

# --- bitsandbytes ---
# Versão compatível com CUDA 12.x e PyTorch 2.10
BITSANDBYTES_PIN = "==0.43.3"

# --- ReActor (Face Swap) ---
# Versões exatas do requirements.txt do ReActor
INSIGHTFACE_PIN = "==0.7.3"
ONNX_PIN = "==1.16.1"
ONNXRUNTIME_GPU_PIN = "==1.17.1"
ALBUMENTATIONS_PIN = "==1.4.3"
OPENCV_PIN = ">=4.7.0.72"

# --- Auxiliares ---
JOBLIB_PIN = ""  # Qualquer versão
OPENCV_HEADLESS_PIN = ""  # Pré-requisito do insightface

# ══════════════════════════════════════════════════════════════
# PIP_CONSTRAINT — Blindagem Global
# ══════════════════════════════════════════════════════════════
# Conteúdo do arquivo de restrições PIP.
# Impede que QUALQUER `pip install` atualize estas libs além dos limites.
PIP_CONSTRAINT_CONTENT = f"""\
numpy{NUMPY_PIN}
scikit-image{SCIKIT_IMAGE_PIN}
scipy{SCIPY_PIN}
"""

# ══════════════════════════════════════════════════════════════
# ONNXRUNTIME — Seleção por CUDA
# ══════════════════════════════════════════════════════════════
# O onnxruntime-gpu precisa de index URL específico por versão de CUDA.
ONNXRUNTIME_CUDA12_INDEX = (
    "https://aiinfra.pkgs.visualstudio.com/PublicPackages/"
    "_packaging/onnxruntime-cuda-12/pypi/simple/"
)
ONNXRUNTIME_CUDA11_INDEX = (
    "https://aiinfra.pkgs.visualstudio.com/PublicPackages/"
    "_packaging/onnxruntime-cuda-11/pypi/simple"
)

# ══════════════════════════════════════════════════════════════
# FORGE
# ══════════════════════════════════════════════════════════════
FORGE_REPO_URL = "https://github.com/lllyasviel/stable-diffusion-webui-forge.git"
FORGE_LAUNCH_FILE = "launch.py"

# ══════════════════════════════════════════════════════════════
# CAMINHOS PADRÃO
# ══════════════════════════════════════════════════════════════
DEFAULT_DRIVE_PATH = "/content/drive/MyDrive/Stable_Diffusion_Dados"
DEFAULT_CACHE_PATH = "/content/cache"
DEFAULT_FORGE_PATH = "/content/stable-diffusion-webui-forge"
DEFAULT_OUTPUTS_TEMP = "/content/outputs_temp"

# Pastas do Drive
DRIVE_FOLDERS = [
    "Modelos_Base", "LoRAs", "VAEs", "Text_Encoders",
    "Imagens_Geradas", "logs"
]

# Cache local (efêmero)
CACHE_SUBDIRS = ["checkpoints", "loras", "vaes", "text_encoders"]

# Mapeamento tipo → pasta
MODEL_TYPE_TO_DRIVE_FOLDER = {
    "checkpoint": "Modelos_Base",
    "lora": "LoRAs",
    "vae": "VAEs",
    "text_encoder": "Text_Encoders",
}

MODEL_TYPE_TO_CACHE_FOLDER = {
    "checkpoint": "checkpoints",
    "lora": "loras",
    "vae": "vaes",
    "text_encoder": "text_encoders",
}

# Symlinks: nome no Forge → subpasta do cache
FORGE_SYMLINK_MAP = {
    "Stable-diffusion": "checkpoints",
    "Lora": "loras",
    "VAE": "vaes",
    "text_encoder": "text_encoders",
}

# ══════════════════════════════════════════════════════════════
# THRESHOLDS DE MEMÓRIA (padrão)
# ══════════════════════════════════════════════════════════════
DEFAULT_VRAM_THRESHOLD = 85   # % — acima disso, auto-evict
DEFAULT_RAM_THRESHOLD = 75    # % — acima disso, auto-evict
DEFAULT_DISK_THRESHOLD = 90   # % — acima disso, aviso

# ══════════════════════════════════════════════════════════════
# HARDWARE — Perfis de GPU
# ══════════════════════════════════════════════════════════════
GPU_PROFILES = {
    "GPU_LUXO": {
        "match": ["H100", "A100"],
        "args": "--theme dark --cuda-malloc --cuda-stream",
        "description": "Desempenho Extremo (40-80 GB VRAM)",
    },
    "GPU_MEDIA": {
        "match": ["L4"],
        "args": "--theme dark",
        "description": "Custo-Benefício (24 GB VRAM)",
    },
    "GPU_ECONOMICA": {
        "match": ["T4", "G4"],
        "args": "--theme dark --always-offload-from-vram",
        "description": "Economia de Memória (15 GB VRAM)",
    },
    "CPU_TURBO": {
        "match": [],
        "args": (
            "--theme dark --use-cpu all --skip-torch-cuda-test "
            "--no-half --precision full"
        ),
        "description": "Modo CPU (Muito lento)",
    },
}

# ══════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════

def get_all_pins_as_requirements() -> list[str]:
    """Retorna lista de requirements no formato pip install."""
    pins = [
        f"numpy{NUMPY_PIN}",
        f"scikit-image{SCIKIT_IMAGE_PIN}",
        f"scipy{SCIPY_PIN}",
        f"bitsandbytes{BITSANDBYTES_PIN}",
        f"insightface{INSIGHTFACE_PIN}",
        f"onnx{ONNX_PIN}",
        f"onnxruntime-gpu{ONNXRUNTIME_GPU_PIN}",
        f"albumentations{ALBUMENTATIONS_PIN}",
    ]
    return [p for p in pins if not p.endswith("==") and not p.endswith("<") and not p.endswith(">")]


def get_pip_constraint_path(base_path: str = "/tmp") -> str:
    """Gera o arquivo de constraint e retorna o caminho."""
    import os
    path = os.path.join(base_path, "pip_constraints_sd.txt")
    with open(path, "w") as f:
        f.write(PIP_CONSTRAINT_CONTENT)
    return path
