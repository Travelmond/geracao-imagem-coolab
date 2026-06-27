"""
Bridge entre o sistema de cache e o Forge/A1111 WebUI.

Gerencia symlinks dos diretórios de modelos e outputs,
permitindo que o Forge acesse modelos do cache e sincronize
outputs com o Google Drive.
"""

import os
import shutil
from pathlib import Path
from typing import Callable, Dict, Optional


class ForgeBridge:
    """Pontes de integração entre o cache de modelos e o Forge WebUI."""

    SYMLINK_MAP = {
        "Stable-diffusion": "checkpoints",
        "Lora": "loras",
        "VAE": "vaes",
        "text_encoder": "text_encoders",
    }

    def __init__(
        self,
        forge_path: str,
        cache_path: str,
        drive_path: str,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Inicializa o bridge com os caminhos principais.

        Args:
            forge_path: Caminho base da instalação do Forge.
            cache_path: Caminho do diretório de cache de modelos.
            drive_path: Caminho do Google Drive montado.
            log_callback: Função opcional para receber mensagens de log.
        """
        self.forge_path = Path(forge_path)
        self.cache_path = Path(cache_path)
        self.drive_path = Path(drive_path)
        self.log = log_callback or (lambda msg: None)
        self.outputs_temp = Path("/content/outputs_temp")
        self.outputs_drive = self.drive_path / "Imagens_Geradas"

    def setup_symlinks(self) -> None:
        """
        Cria symlinks dos diretórios de modelos do Forge para o cache.

        Para cada diretório de modelo, remove o existente (arquivo, diretório
        ou symlink) e cria um novo symlink apontando para o cache correspondente.
        """
        models_dir = self.forge_path / "models"

        for forge_subdir, cache_subdir in self.SYMLINK_MAP.items():
            link_path = models_dir / forge_subdir
            target_path = self.cache_path / cache_subdir

            self._remove_path(link_path)
            target_path.mkdir(parents=True, exist_ok=True)
            os.symlink(target_path, link_path)
            self.log(f"Symlink criado: {link_path} -> {target_path}")

        self.setup_outputs_directory()

    def _remove_path(self, path: Path) -> None:
        """
        Remove um caminho do filesystem, seja symlink, arquivo ou diretório.

        Args:
            path: Caminho a ser removido.
        """
        if path.is_symlink():
            os.remove(path)
            self.log(f"Symlink removido: {path}")
        elif path.is_dir():
            shutil.rmtree(path)
            self.log(f"Diretório removido: {path}")
        elif path.is_file():
            os.remove(path)
            self.log(f"Arquivo removido: {path}")

    def verify_symlinks(self) -> Dict[str, bool]:
        """
        Verifica se todos os symlinks estão válidos.

        Returns:
            Dicionário com nome do symlink e se está válido (True/False).
        """
        models_dir = self.forge_path / "models"
        results = {}

        for forge_subdir, cache_subdir in self.SYMLINK_MAP.items():
            link_path = models_dir / forge_subdir
            target_path = self.cache_path / cache_subdir
            is_valid = (
                link_path.is_symlink()
                and os.readlink(str(link_path)) == str(target_path)
                and target_path.exists()
            )
            results[forge_subdir] = is_valid

        outputs_link = self.forge_path / "outputs"
        results["outputs"] = (
            outputs_link.is_symlink()
            and os.readlink(str(outputs_link)) == str(self.outputs_temp)
            and self.outputs_temp.exists()
        )

        return results

    def refresh_models(self) -> None:
        """
        Recarrega a lista de modelos no Forge.

        Tenta chamar shared.refresh_checkpoints() para atualizar
        a lista de modelos disponíveis na interface do Forge.
        """
        try:
            from modules import shared

            shared.refresh_checkpoints()
            self.log("Lista de modelos do Forge atualizada com sucesso.")
        except ImportError:
            self.log("Aviso: módulo 'shared' não disponível. Forge não carregado?")
        except Exception as e:
            self.log(f"Erro ao atualizar modelos do Forge: {e}")

    def get_current_model(self) -> str:
        """
        Retorna o nome do modelo atualmente carregado no Forge.

        Returns:
            Nome do modelo ou string vazia se não disponível.
        """
        try:
            from modules import shared

            if hasattr(shared, "sd_model") and shared.sd_model is not None:
                if hasattr(shared.sd_model, "sd_checkpoint_info"):
                    info = shared.sd_model.sd_checkpoint_info
                    if hasattr(info, "model_name"):
                        return info.model_name
                    if hasattr(info, "filename"):
                        return Path(info.filename).name
            return ""
        except ImportError:
            self.log("Aviso: módulo 'shared' não disponível.")
            return ""
        except Exception as e:
            self.log(f"Erro ao obter modelo atual: {e}")
            return ""

    def get_forge_vram_info(self) -> Optional[Dict[str, float]]:
        """
        Retorna informações de VRAM do backend do Forge.

        Tenta acessar backend.memory_management para obter dados
        de memória da GPU.

        Returns:
            Dicionário com total_mb, free_mb e used_mb, ou None se indisponível.
        """
        try:
            from backend import memory_management

            total = memory_management.total_vram
            free = memory_management.get_free_vram()
            used = total - free

            return {
                "total_mb": round(total, 2),
                "free_mb": round(free, 2),
                "used_mb": round(used, 2),
            }
        except ImportError:
            self.log("Aviso: backend.memory_management não disponível.")
            return None
        except Exception as e:
            self.log(f"Erro ao obter info de VRAM: {e}")
            return None

    def setup_outputs_directory(self) -> None:
        """
        Cria o diretório de outputs temporário e configura o symlink.

        O diretório /content/outputs_temp fica no disco local para
        velocidade, e o Forge/outputs aponta para ele.
        """
        self.outputs_temp.mkdir(parents=True, exist_ok=True)
        outputs_link = self.forge_path / "outputs"

        self._remove_path(outputs_link)
        os.symlink(self.outputs_temp, outputs_link)
        self.log(f"Outputs configurado: {outputs_link} -> {self.outputs_temp}")

    def backup_outputs_to_drive(self) -> None:
        """
        Copia o conteúdo dos outputs temporários para o Google Drive.

        Sincroniza todos os arquivos de /content/outputs_temp para
        Drive/Imagens_Geradas, criando o destino se necessário.
        """
        if not self.outputs_temp.exists():
            self.log("Aviso: diretório de outputs temporário não existe.")
            return

        self.outputs_drive.mkdir(parents=True, exist_ok=True)

        copied = 0
        for item in self.outputs_temp.iterdir():
            dest = self.outputs_drive / item.name
            if item.is_file():
                shutil.copy2(str(item), str(dest))
                copied += 1
            elif item.is_dir():
                if dest.exists():
                    shutil.rmtree(str(dest))
                shutil.copytree(str(item), str(dest))
                copied += 1

        self.log(f"Backup concluído: {copied} itens copiados para {self.outputs_drive}")
