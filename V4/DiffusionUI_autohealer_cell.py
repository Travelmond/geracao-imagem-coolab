"""
AutoHealer — Sistema de Diagnóstico e Cura Automática com POO
Para Stable Diffusion WebUI Forge no Google Colab

Este módulo implementa Programação Orientada a Objetos para:
- Diagnosticar dependências críticas
- Aplicar "vacinas" (correções) em sequência
- Usar múltiplas estratégias por biblioteca
- Persistir wheels no Google Drive
- Relatar falhas e sucessos detalhadamente
"""

import os
import sys
import subprocess
import time
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging


# ============================================================================
# ENUMS E CLASSES DE DADOS
# ============================================================================

class Status(Enum):
    """Status de uma vacina após execução."""
    HEALTHY = "healthy"      # Já estava instalado
    FIXED = "fixed"          # Corrigido com sucesso
    FAILED = "failed"        # Todas estratégias falharam
    SKIPPED = "skipped"      # Pulado por condição


@dataclass
class VaccineResult:
    """Resultado da aplicação de uma vacina."""
    name: str
    status: Status
    message: str
    duration: float
    strategies_tried: List[str] = field(default_factory=list)
    error_details: Optional[str] = None


@dataclass
class VaccineConfig:
    """Configuração de uma vacina."""
    name: str
    import_name: str
    description: str
    critical: bool = True
    check_func: Optional[Callable] = None


# ============================================================================
# CLASSE PRINCIPAL: LibraryInstaller
# ============================================================================

class LibraryInstaller:
    """
    Instalador de bibliotecas com múltiplas estratégias e persistência.
    
    Atributos:
        python_bin (str): Caminho para o interpretador Python
        wheels_dir (str): Diretório para salvar wheels no Drive
        timeout (int): Timeout máximo para comandos pip
        results (Dict): Resultados das instalações
    """
    
    def __init__(self, python_bin: str = 'python3.10', 
                 wheels_dir: str = '/content/drive/MyDrive/Stable_Diffusion_Dados/wheels',
                 timeout: int = 300):
        self.python = python_bin
        self.wheels_dir = wheels_dir
        self.timeout = timeout
        self.results: Dict[str, VaccineResult] = {}
        
        # Cria diretório de wheels
        os.makedirs(wheels_dir, exist_ok=True)
        
        # Configura logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        self.logger = logging.getLogger('LibraryInstaller')
    
    def run_command(self, command: str, timeout: Optional[int] = None, 
                    quiet: bool = True, shell: bool = True) -> Tuple[int, str, str]:
        """
        Executa comando shell com timeout e captura de output.
        
        Args:
            command: Comando a executar
            timeout: Timeout em segundos (usa default se None)
            quiet: Reduz output se True
            shell: Usa shell se True
            
        Returns:
            Tuple (return_code, stdout, stderr)
        """
        if timeout is None:
            timeout = self.timeout
            
        try:
            prefix = ""
            if quiet and not shell:
                prefix = "2>/dev/null "
            
            full_cmd = f"{prefix}{command}" if quiet else command
            
            result = subprocess.run(
                full_cmd,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return -1, "", f"Timeout após {timeout}s"
        except Exception as e:
            return -1, "", str(e)
    
    def check_import(self, import_name: str) -> Tuple[bool, str]:
        """
        Verifica se biblioteca pode ser importada.
        
        Args:
            import_name: Nome do módulo para importar
            
        Returns:
            Tuple (success, version_or_error)
        """
        code = f"import {import_name}; print(getattr({import_name}, '__version__', 'N/A'))"
        rc, stdout, stderr = self.run_command(
            f"{self.python} -c '{code}'",
            timeout=30,
            quiet=False
        )
        
        if rc == 0 and stdout.strip():
            return True, stdout.strip()
        return False, stderr.strip() or "Import failed"
    
    def download_wheel(self, package: str, version: Optional[str] = None,
                       extra_index: Optional[str] = None) -> bool:
        """
        Baixa wheel para diretório persistente.
        
        Args:
            package: Nome do pacote
            version: Versão específica (ex: "==0.43.3")
            extra_index: URL extra para pip
            
        Returns:
            True se sucesso, False se falhou
        """
        version_str = version if version else ""
        extra_url = f"--extra-index-url {extra_index}" if extra_index else ""
        
        cmd = (f"{self.python} -m pip download {package}{version_str} "
               f"--no-deps -d {self.wheels_dir} {extra_url} --quiet 2>/dev/null")
        
        rc, _, _ = self.run_command(cmd, timeout=120)
        return rc == 0
    
    def install_with_strategies(self, import_name: str, strategies: List[Dict],
                                save_wheel: bool = True) -> VaccineResult:
        """
        Tenta instalar biblioteca com múltiplas estratégias em sequência.
        
        Args:
            import_name: Nome do módulo para verificar instalação
            strategies: Lista de estratégias, cada uma com:
                - name: Nome descritivo
                - command: Comando pip
                - post_check: Função opcional pós-instalação
            save_wheel: Se deve salvar wheel após sucesso
            
        Returns:
            VaccineResult com status e detalhes
        """
        start_time = time.time()
        strategies_tried = []
        
        # Verifica se já está instalado
        already_installed, version = self.check_import(import_name)
        if already_installed:
            return VaccineResult(
                name=import_name,
                status=Status.HEALTHY,
                message=f"Já instalado (v{version})",
                duration=time.time() - start_time,
                strategies_tried=["check_only"]
            )
        
        # Tenta cada estratégia
        for i, strat in enumerate(strategies, 1):
            strat_name = strat.get('name', f'Estratégia {i}')
            command = strat.get('command', '')
            post_check = strat.get('post_check', None)
            
            strategies_tried.append(strat_name)
            self.logger.debug(f"Tentando {strat_name}: {command[:80]}...")
            
            # Instala pré-dependências se especificado
            pre_deps = strat.get('pre_deps', [])
            for dep in pre_deps:
                self.run_command(f"{self.python} -m pip install {dep} --quiet", timeout=60)
            
            # Executa comando principal
            rc, stdout, stderr = self.run_command(command, timeout=180, quiet=False)
            
            if rc == 0:
                # Verifica pós-instalação
                if post_check:
                    try:
                        if not post_check():
                            continue  # Estratégia falhou no post-check
                    except Exception:
                        continue
                
                # Verifica importação final
                success, version = self.check_import(import_name)
                if success:
                    # Salva wheel se solicitado
                    if save_wheel:
                        pkg_name = strat.get('wheel_package', import_name)
                        pkg_version = strat.get('wheel_version', '')
                        extra_index = strat.get('extra_index', None)
                        self.download_wheel(pkg_name, pkg_version, extra_index)
                    
                    return VaccineResult(
                        name=import_name,
                        status=Status.FIXED,
                        message=f"Corrigido com {strat_name} (v{version})",
                        duration=time.time() - start_time,
                        strategies_tried=strategies_tried
                    )
        
        # Todas estratégias falharam
        return VaccineResult(
            name=import_name,
            status=Status.FAILED,
            message="Todas estratégias falharam",
            duration=time.time() - start_time,
            strategies_tried=strategies_tried,
            error_details=f"Falhou após {len(strategies_tried)} tentativas"
        )
    
    # ========================================================================
    # ESTRATÉGIAS ESPECÍFICAS POR BIBLIOTECA
    # ========================================================================
    
    def install_clip(self) -> VaccineResult:
        """Instala CLIP (OpenAI) com 4 estratégias."""
        strategies = [
            {
                'name': 'Wheel salvo no Drive',
                'command': f"{self.python} -m pip install {self.wheels_dir}/clip*.whl --quiet",
                'wheel_package': 'clip'
            },
            {
                'name': 'PyPI (git+https)',
                'command': (f"{self.python} -m pip install ftfy regex tqdm --quiet && "
                           f"{self.python} -m pip install git+https://github.com/openai/CLIP.git "
                           f"--quiet --no-build-isolation"),
                'pre_deps': ['setuptools<70'],
                'wheel_package': 'clip'
            },
            {
                'name': 'Commit fixo GitHub',
                'command': (f"{self.python} -m pip install ftfy regex tqdm --quiet && "
                           f"{self.python} -m pip install "
                           f"'https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip' "
                           f"--no-build-isolation --quiet"),
                'pre_deps': ['setuptools<70'],
                'wheel_package': 'clip'
            },
            {
                'name': 'Versão PyPI oficial',
                'command': f"{self.python} -m pip install clip --quiet",
                'wheel_package': 'clip'
            }
        ]
        return self.install_with_strategies('clip', strategies)
    
    def install_bitsandbytes(self) -> VaccineResult:
        """Instala bitsandbytes com 4 estratégias."""
        strategies = [
            {
                'name': 'Wheel salvo no Drive',
                'command': f"{self.python} -m pip install {self.wheels_dir}/bitsandbytes*.whl --quiet",
                'wheel_package': 'bitsandbytes',
                'wheel_version': '==0.43.3'
            },
            {
                'name': 'Versão 0.43.3 (CUDA 12)',
                'command': f"{self.python} -m pip install 'bitsandbytes==0.43.3' --quiet",
                'wheel_package': 'bitsandbytes',
                'wheel_version': '==0.43.3'
            },
            {
                'name': 'Última versão compatível',
                'command': f"{self.python} -m pip install 'bitsandbytes>=0.43.0,<0.45.0' --quiet",
                'wheel_package': 'bitsandbytes'
            },
            {
                'name': 'Versão mais recente',
                'command': f"{self.python} -m pip install bitsandbytes --quiet",
                'wheel_package': 'bitsandbytes'
            }
        ]
        return self.install_with_strategies('bitsandbytes', strategies)
    
    def install_onnxruntime(self) -> VaccineResult:
        """Instala ONNX Runtime com 4 estratégias."""
        strategies = [
            {
                'name': 'Wheel GPU salvo',
                'command': f"{self.python} -m pip install {self.wheels_dir}/onnxruntime_gpu*.whl --quiet",
                'wheel_package': 'onnxruntime-gpu',
                'wheel_version': '==1.17.1',
                'extra_index': 'https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/'
            },
            {
                'name': 'GPU CUDA 12 (1.17.1)',
                'command': (f"{self.python} -m pip install onnxruntime-gpu==1.17.1 "
                           f"--extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/ "
                           f"--quiet"),
                'wheel_package': 'onnxruntime-gpu',
                'wheel_version': '==1.17.1',
                'extra_index': 'https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/'
            },
            {
                'name': 'GPU versão genérica',
                'command': f"{self.python} -m pip install onnxruntime-gpu --quiet",
                'wheel_package': 'onnxruntime-gpu'
            },
            {
                'name': 'CPU fallback',
                'command': f"{self.python} -m pip install onnxruntime --quiet",
                'wheel_package': 'onnxruntime'
            }
        ]
        return self.install_with_strategies('onnxruntime', strategies)
    
    def install_insightface(self) -> VaccineResult:
        """Instala InsightFace com 3 estratégias."""
        strategies = [
            {
                'name': 'Wheel salvo',
                'command': f"{self.python} -m pip install {self.wheels_dir}/insightface*.whl --quiet",
                'pre_deps': ['opencv-python-headless', 'albumentations'],
                'wheel_package': 'insightface',
                'wheel_version': '==0.7.3'
            },
            {
                'name': 'Versão 0.7.3 (compatível)',
                'command': (f"{self.python} -m pip install opencv-python-headless albumentations --quiet && "
                           f"{self.python} -m pip install 'insightface==0.7.3' --quiet"),
                'pre_deps': ['numpy<2.1.0', 'onnx==1.16.1'],
                'wheel_package': 'insightface',
                'wheel_version': '==0.7.3'
            },
            {
                'name': 'Versão mais recente',
                'command': (f"{self.python} -m pip install opencv-python-headless albumentations --quiet && "
                           f"{self.python} -m pip install insightface --quiet"),
                'pre_deps': ['numpy<2.1.0'],
                'wheel_package': 'insightface'
            }
        ]
        return self.install_with_strategies('insightface', strategies)
    
    def install_numpy_safe(self) -> VaccineResult:
        """Instala NumPy com versão segura (<2.1.0)."""
        start_time = time.time()
        
        # Verifica se já está na versão correta
        success, version = self.check_import('numpy')
        if success:
            if version.startswith('2.0.') or version.startswith('1.'):
                return VaccineResult(
                    name='numpy',
                    status=Status.HEALTHY,
                    message=f"NumPy {version} (compatível)",
                    duration=time.time() - start_time
                )
        
        # Instala versão segura
        cmd = f"{self.python} -m pip install 'numpy<2.1.0' --quiet"
        rc, _, _ = self.run_command(cmd, timeout=120)
        
        if rc == 0:
            success, version = self.check_import('numpy')
            if success:
                return VaccineResult(
                    name='numpy',
                    status=Status.FIXED,
                    message=f"NumPy {version} instalado",
                    duration=time.time() - start_time
                )
        
        return VaccineResult(
            name='numpy',
            status=Status.FAILED,
            message="Falha ao instalar NumPy seguro",
            duration=time.time() - start_time
        )
    
    # ========================================================================
    # SISTEMA DE VACINAS
    # ========================================================================
    
    def run_all_vaccines(self) -> List[VaccineResult]:
        """
        Executa todas as vacinas em sequência.
        
        Returns:
            Lista de VaccineResult para cada vacina
        """
        vaccines = [
            ('CLIP (OpenAI)', self.install_clip),
            ('NumPy Safe', self.install_numpy_safe),
            ('bitsandbytes', self.install_bitsandbytes),
            ('ONNX Runtime', self.install_onnxruntime),
            ('InsightFace', self.install_insightface),
        ]
        
        results = []
        for name, func in vaccines:
            self.logger.info(f"Aplicando vacina: {name}")
            result = func()
            self.results[name] = result
            results.append(result)
            
            # Log do resultado
            status_icon = {
                Status.HEALTHY: '✅',
                Status.FIXED: '🔧',
                Status.FAILED: '❌',
                Status.SKIPPED: '⏭️'
            }
            icon = status_icon.get(result.status, '❓')
            self.logger.info(f"{icon} {name}: {result.status.value} ({result.duration:.1f}s)")
        
        return results
    
    def generate_report(self) -> str:
        """
        Gera relatório formatado dos resultados.
        
        Returns:
            String formatada com relatório
        """
        lines = [
            "╔══════════════════════════════════════════════════╗",
            "║     🏥 Relatório do LibraryInstaller 🏥          ║",
            "╚══════════════════════════════════════════════════╝",
            ""
        ]
        
        total = len(self.results)
        healthy = sum(1 for r in self.results.values() if r.status == Status.HEALTHY)
        fixed = sum(1 for r in self.results.values() if r.status == Status.FIXED)
        failed = sum(1 for r in self.results.values() if r.status == Status.FAILED)
        
        for name, result in self.results.items():
            status_icon = {
                Status.HEALTHY: '✅',
                Status.FIXED: '🔧',
                Status.FAILED: '❌',
                Status.SKIPPED: '⏭️'
            }
            icon = status_icon.get(result.status, '❓')
            
            lines.append(f"  {icon} {name:25s} [{result.status.value.upper()}]")
            lines.append(f"     └─ {result.message}")
            lines.append(f"        ⏱ {result.duration:.1f}s")
            if result.strategies_tried:
                lines.append(f"        Estratégias: {', '.join(result.strategies_tried)}")
            lines.append("")
        
        lines.append("─" * 50)
        lines.append(f"  📊 Total: {total} vacinas")
        lines.append(f"  ✅ Saudáveis: {healthy}")
        lines.append(f"  🔧 Corrigidas: {fixed}")
        lines.append(f"  ❌ Falhas: {failed}")
        
        if failed > 0:
            lines.append(f"  🚨 {failed} falha(s) crítica(s) detectada(s).")
        
        return "\n".join(lines)


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def setup_pip_constraint(constraint_file: str = '/content/pip_constraints_sd.txt'):
    """Configura PIP_CONSTRAINT para blindagem de versões."""
    with open(constraint_file, 'w') as f:
        f.write('numpy<2.1.0\n')
        f.write('scipy<1.14.0\n')
        f.write('setuptools<70.0.0\n')
    
    os.environ['PIP_CONSTRAINT'] = constraint_file
    return constraint_file


def print_summary(installer: LibraryInstaller):
    """Imprime resumo formatado das instalações."""
    print("\n" + "=" * 60)
    print("📊 RESUMO DA INSTALAÇÃO:")
    print("=" * 60)
    
    libs = [
        ('CLIP', 'clip'),
        ('NumPy', 'numpy'),
        ('bitsandbytes', 'bitsandbytes'),
        ('ONNX Runtime', 'onnxruntime'),
        ('InsightFace', 'insightface'),
    ]
    
    for name, import_name in libs:
        try:
            mod = __import__(import_name)
            ver = getattr(mod, '__version__', 'N/A')
            print(f"   ✅ {name:20s} v{ver}")
        except ImportError:
            print(f"   ❌ {name:20s} NÃO disponível")
    
    print(f"\n💾 Wheels salvos em: {installer.wheels_dir}")
    print("   (Serão reutilizados na próxima sessão!)")


# ============================================================================
# MAIN (para testes)
# ============================================================================

if __name__ == '__main__':
    print("🧪 Testando LibraryInstaller...")
    
    installer = LibraryInstaller()
    results = installer.run_all_vaccines()
    
    print("\n" + installer.generate_report())
    print_summary(installer)
