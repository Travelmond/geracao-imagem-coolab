"""
clip_installer.py — Instalador Robusto do OpenAI CLIP
=====================================================

Instala o CLIP com múltiplas estratégias de fallback:
1. Wheel pré-compilado local (se disponível no Drive)
2. GitHub commit fixo com --no-build-isolation
3. GitHub commit fixo com setuptools<70
4. open-clip-torch como alternativa

Uso:
    from lib.clip_installer import CLIPInstaller
    installer = CLIPInstaller(python_cmd="python3.10")
    success, message = installer.install()
"""

import os
import subprocess
import sys
from typing import Tuple, Optional

# Importar version_pins
try:
    from . import version_pins
except ImportError:
    _lib_dir = os.path.dirname(os.path.abspath(__file__))
    if _lib_dir not in sys.path:
        sys.path.insert(0, _lib_dir)
    import version_pins


class CLIPInstaller:
    """Instalador multi-estratégia para OpenAI CLIP."""

    def __init__(
        self,
        python_cmd: str = "python3.10",
        wheel_search_paths: Optional[list] = None,
        timeout: int = 300,
        debug: bool = False,
    ):
        self.python_cmd = python_cmd
        self.timeout = timeout
        self.debug = debug
        self.wheel_search_paths = wheel_search_paths or [
            "/content/drive/MyDrive/Stable_Diffusion_Dados/wheels",
            "/content/wheels",
            os.path.join(os.path.dirname(__file__), "..", "wheels"),
        ]
        self._log_buffer: list[str] = []

    def _log(self, msg: str) -> None:
        """Log interno."""
        self._log_buffer.append(msg)
        if self.debug:
            print(f"  [CLIP] {msg}")

    def _run(self, cmd: list[str], timeout: Optional[int] = None) -> Tuple[bool, str, str]:
        """Executa comando e retorna (sucesso, stdout, stderr)."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Timeout expirado"
        except FileNotFoundError:
            return False, "", f"Comando não encontrado: {cmd[0]}"
        except Exception as e:
            return False, "", str(e)

    def is_installed(self) -> bool:
        """Verifica se o CLIP está instalado e funcional."""
        ok, stdout, _ = self._run(
            [self.python_cmd, "-c", "import clip; print('OK')"],
            timeout=30,
        )
        return ok and "OK" in stdout

    def install(self) -> Tuple[bool, str]:
        """
        Tenta instalar o CLIP usando múltiplas estratégias.
        Retorna (sucesso, mensagem).
        """
        if self.is_installed():
            return True, "✅ CLIP já está instalado e funcional"

        # Estratégia 1: Wheel local
        self._log("Tentando wheel pré-compilado local...")
        success, msg = self._try_local_wheel()
        if success:
            return True, f"✅ CLIP instalado via wheel local: {msg}"

        # Garantir dependências antes das próximas tentativas
        self._install_deps()

        # Estratégia 2: GitHub com --no-build-isolation
        self._log("Tentando GitHub com --no-build-isolation...")
        success, msg = self._try_github_no_isolation()
        if success:
            return True, f"✅ CLIP instalado via GitHub (no-build-isolation)"

        # Estratégia 3: GitHub com setuptools<70
        self._log("Tentando com setuptools<70...")
        success, msg = self._try_github_with_setuptools_pin()
        if success:
            return True, f"✅ CLIP instalado via GitHub (setuptools pinado)"

        # Estratégia 4: open-clip-torch (alternativa)
        self._log("Tentando open-clip-torch como alternativa...")
        success, msg = self._try_open_clip()
        if success:
            return True, f"⚠️ open-clip-torch instalado como alternativa ao CLIP"

        # Todas as estratégias falharam
        log_text = "\n".join(self._log_buffer)
        return False, f"❌ CLIP: todas as 4 estratégias falharam.\nLog:\n{log_text}"

    def _install_deps(self) -> None:
        """Instala dependências do CLIP."""
        deps = version_pins.CLIP_DEPS
        cmd = [self.python_cmd, "-m", "pip", "install", "-q"] + deps
        self._run(cmd)
        self._log(f"Dependências instaladas: {deps}")

    def _try_local_wheel(self) -> Tuple[bool, str]:
        """Tenta instalar de um wheel .whl local."""
        for search_path in self.wheel_search_paths:
            if not os.path.isdir(search_path):
                continue
            for filename in os.listdir(search_path):
                if filename.startswith("clip") and filename.endswith(".whl"):
                    wheel_path = os.path.join(search_path, filename)
                    self._log(f"Wheel encontrado: {wheel_path}")
                    ok, _, stderr = self._run(
                        [self.python_cmd, "-m", "pip", "install", wheel_path]
                    )
                    if ok and self.is_installed():
                        return True, wheel_path
                    self._log(f"Wheel falhou: {stderr[:200]}")
        return False, "Nenhum wheel encontrado"

    def _try_github_no_isolation(self) -> Tuple[bool, str]:
        """Instala via GitHub com --no-build-isolation."""
        url = version_pins.CLIP_GITHUB_URL
        ok, _, stderr = self._run([
            self.python_cmd, "-m", "pip", "install", "-q",
            url, "--no-build-isolation",
        ])
        if ok and self.is_installed():
            return True, "OK"
        self._log(f"GitHub no-isolation falhou: {stderr[:300]}")
        return False, stderr[:200]

    def _try_github_with_setuptools_pin(self) -> Tuple[bool, str]:
        """Pina setuptools<70 e tenta novamente."""
        # Pinar setuptools
        pin = version_pins.SETUPTOOLS_PIN
        self._run([
            self.python_cmd, "-m", "pip", "install", "-q",
            f"setuptools{pin}",
        ])
        # Tentar instalar CLIP normalmente (sem --no-build-isolation)
        url = version_pins.CLIP_GITHUB_URL
        ok, _, stderr = self._run([
            self.python_cmd, "-m", "pip", "install", "-q", url,
        ])
        if ok and self.is_installed():
            return True, "OK"
        # Tentar com --no-build-isolation também
        ok, _, stderr = self._run([
            self.python_cmd, "-m", "pip", "install", "-q",
            url, "--no-build-isolation",
        ])
        if ok and self.is_installed():
            return True, "OK (com --no-build-isolation)"
        self._log(f"GitHub com setuptools pin falhou: {stderr[:300]}")
        return False, stderr[:200]

    def _try_open_clip(self) -> Tuple[bool, str]:
        """Instala open-clip-torch como alternativa."""
        ok, _, stderr = self._run([
            self.python_cmd, "-m", "pip", "install", "-q", "open-clip-torch",
        ])
        if ok:
            # Verificar se importa (namespace diferente)
            check_ok, _, _ = self._run(
                [self.python_cmd, "-c", "import open_clip; print('OK')"],
                timeout=30,
            )
            if check_ok:
                return True, "open-clip-torch"
        self._log(f"open-clip-torch falhou: {stderr[:200]}")
        return False, stderr[:200]

    def get_log(self) -> str:
        """Retorna o log completo das tentativas."""
        return "\n".join(self._log_buffer)


if __name__ == "__main__":
    print("🔍 Testando instalação do CLIP...")
    installer = CLIPInstaller(debug=True)
    success, message = installer.install()
    print(f"\nResultado: {message}")
