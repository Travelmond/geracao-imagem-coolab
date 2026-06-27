#!/bin/bash
# colab-simulator.sh — Simula o ambiente do Google Colab localmente
#!/bin/bash
echo "🖥️ Simulando ambiente Google Colab (Deepin 25)"
echo "═══════════════════════════════════════════════"
echo ""
echo "🔧 Hardware:"
if [ -e /dev/nvidia0 ]; then
    echo "  GPU: NVIDIA GPU (CUDA 12.1)"
    echo "  VRAM: Detectada (/dev/nvidia0)"
else
    echo "  GPU: CPU"
    echo "  VRAM: N/A"
fi
echo "  RAM: $(free -h | awk '/Mem/{print $2}')"
echo "  Disco: $(df -h /content | tail -1 | awk '{print $2}')"
echo ""
echo "📂 Estrutura:"
ls -la /content/
echo ""
echo "🚀 Para iniciar o Forge:"
echo "  cd /content/stable-diffusion-webui-forge"
echo "  python3.10 launch.py --share --port 7860"
echo ""
echo "💡 Acesse: http://localhost:7860"
