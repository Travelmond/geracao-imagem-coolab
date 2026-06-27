# Dockerfile — Simulador do Google Colab com GPU
# Base: CUDA 12.1 + Ubuntu 22.04 (mesmo SO do Colab)
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON=python3.10

# Python 3.10 + ferramentas essenciais
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-venv python3.10-dev python3.10-distutils \
    git wget curl vim zip unzip \
    && rm -rf /var/lib/apt/lists/*

# PIP para Python 3.10
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
# setuptools + wheel (necessário para compilar CLIP)
RUN python3.10 -m pip install setuptools wheel

# Simular estrutura de diretórios do Colab
RUN mkdir -p /content/drive/MyDrive/Stable_Diffusion_Dados/{Modelos_Base,LoRAs,VAEs,Text_Encoders,Imagens_Geradas,logs} \
             /content/cache/{checkpoints,loras,vaes,text_encoders} \
             /content/outputs_temp

WORKDIR /content

# Script de simulação do Colab
COPY colab-simulator.sh /usr/local/bin/colab-sim
RUN chmod +x /usr/local/bin/colab-sim

CMD ["/bin/bash"]
