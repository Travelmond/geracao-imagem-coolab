#!/bin/bash
# Script para baixar wheels pré-compilados das 4 bibliotecas problemáticas
# Execute este script uma vez no seu computador ou no Colab para salvar os wheels no Drive

set -e

WHEELS_DIR="$1"
if [ -z "$WHEELS_DIR" ]; then
    WHEELS_DIR="/content/drive/MyDrive/Stable_Diffusion_Dados/wheels"
fi

echo "📦 Baixando wheels para: $WHEELS_DIR"
mkdir -p "$WHEELS_DIR"

PYTHON="python3.10"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "1. CLIP (OpenAI) — embeddings de texto/imagem"
echo "───────────────────────────────────────────────────────"
$PYTHON -m pip download \
    --no-deps \
    --no-binary :all: \
    --no-cache-dir \
    git+https://github.com/openai/CLIP.git \
    -d "$WHEELS_DIR" 2>/dev/null || {
    echo "⚠️ CLIP falhou ao baixar do GitHub, tentando PyPI..."
    $PYTHON -m pip download --no-deps clip -d "$WHEELS_DIR" 2>/dev/null || echo "❌ CLIP não disponível como wheel"
}

echo ""
echo "═══════════════════════════════════════════════════════"
echo "2. bitsandbytes — quantização 4/8-bit"
echo "───────────────────────────────────────────────────────"
$PYTHON -m pip download --no-deps 'bitsandbytes==0.43.3' -d "$WHEELS_DIR" 2>/dev/null || {
    echo "⚠️ bitsandbytes 0.43.3 não encontrado, tentando versão mais recente..."
    $PYTHON -m pip download --no-deps bitsandbytes -d "$WHEELS_DIR" 2>/dev/null || echo "❌ bitsandbytes não disponível"
}

echo ""
echo "═══════════════════════════════════════════════════════"
echo "3. onnxruntime-gpu — acelerador CUDA para face swap"
echo "───────────────────────────────────────────────────────"
$PYTHON -m pip download --no-deps \
    --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/ \
    'onnxruntime-gpu==1.17.1' \
    -d "$WHEELS_DIR" 2>/dev/null || {
    echo "⚠️ onnxruntime-gpu não encontrado, tentando versão CPU..."
    $PYTHON -m pip download --no-deps onnxruntime -d "$WHEELS_DIR" 2>/dev/null || echo "❌ onnxruntime não disponível"
}

echo ""
echo "═══════════════════════════════════════════════════════"
echo "4. insightface — detecção facial"
echo "───────────────────────────────────────────────────────"
$PYTHON -m pip download --no-deps 'insightface==0.7.3' -d "$WHEELS_DIR" 2>/dev/null || {
    echo "⚠️ insightface 0.7.3 não encontrado, tentando versão mais recente..."
    $PYTHON -m pip download --no-deps insightface -d "$WHEELS_DIR" 2>/dev/null || echo "❌ insightface não disponível"
}

echo ""
echo "═══════════════════════════════════════════════════════"
echo "📊 Wheels baixados em: $WHEELS_DIR"
echo "───────────────────────────────────────────────────────"
ls -lh "$WHEELS_DIR"/*.whl 2>/dev/null || echo "Nenhum wheel encontrado"
echo ""
echo "✅ Script concluído!"
echo "   Na próxima sessão do Colab, a Célula 3 usará estes wheels."
