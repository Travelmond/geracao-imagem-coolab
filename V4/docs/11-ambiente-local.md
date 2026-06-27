# Ambiente Local — Docker (Deepin 25)

Guia completo para rodar o projeto localmente usando Docker, simulando o ambiente do Google Colab sem gastar créditos.

---

## Pré-requisitos

### 1. Instalar Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose
```

### 2. Adicionar usuário ao grupo docker

```bash
sudo usermod -aG docker $USER
```

**⚠️ Importante:** Faça logout e login novamente para a mudança生效.

### 3. Instalar NVIDIA Container Toolkit (para GPU)

```bash
# Adicionar repositório NVIDIA
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Instalar
sudo apt update
sudo apt install -y nvidia-container-toolkit

# Configurar Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 4. Verificar instalação

```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

Se aparecer a tabela da GPU, está funcionando.

---

## Rodar o Projeto

### 1. Navegar para a pasta docker

```bash
cd /home/fabiano/Documents/Codigo/geracao-imagem-coolab/V4/docker
```

### 2. Criar volume persistente (simula o Google Drive)

```bash
mkdir -p drive-data/{Modelos_Base,LoRAs,VAEs,Text_Encoders,Imagens_Geradas,logs}
```

### 3. Construir e iniciar

```bash
docker-compose up -d --build
```

### 4. Entrar no container

```bash
docker-compose exec colab-sim bash
```

### 5. Rodar o simulador

```bash
colab-sim
```

### 6. Instalar e rodar o Forge (dentro do container)

```bash
cd /content
git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git
cd stable-diffusion-webui-forge
python3.10 launch.py --share --port 7860
```

### 7. Acessar no navegador

```
http://localhost:7860
```

---

## Armazenamento

### Automático (recomendado)

O Docker usa todo o espaço disponível no disco do Deepin. Os modelos ficam no volume `./drive-data` que é seu disco real.

### Manual (limitar espaço)

Se quiser limitar o consumo do Docker:

```bash
# Editar /etc/docker/daemon.json
sudo nano /etc/docker/daemon.json

# Adicionar:
{
  "storage-opts": ["overlay2.size=100G"]
}

# Reiniciar Docker
sudo systemctl restart docker
```

---

## Comandos Úteis

```bash
# Parar container
docker-compose down

# Ver logs
docker-compose logs -f

# Verificar GPU no container
docker-compose exec colab-sim nvidia-smi

# Limpar imagens não usadas
docker system prune -a

# Ver espaço usado pelo Docker
docker system df
```

---

## Troubleshooting

### Erro: "could not select device driver"

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Erro: "permission denied"

```bash
sudo usermod -aG docker $USER
# Logout e login novamente
```

### Erro: "CUDA not available"

Verifique se o NVIDIA Container Toolkit está instalado:

```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## Voltar para o índice

[← Problemas Conhecidos](./09-problemas-conhecidos.md) | [← README](./README.md)
