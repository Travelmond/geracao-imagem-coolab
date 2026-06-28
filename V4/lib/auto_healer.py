#!/usr/bin/env python3
"""
AutoHealer Híbrido - Sistema de Cura Automática do Ambiente
Estratégia A+B: Wheels Persistente + Instalação Inteligente

Autor: Travelmond Project
Versão: 4.1.0
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional, Tuple


class Status(Enum):
    HEALTHY = "healthy"
    FIXED = "fixed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class VaccineResult:
    name: str
    status: Status
    message: str
    duration: float
    strategies_tried: int = 0


class LibraryInstaller:
    """Instalador inteligente de bibliotecas com múltiplas estratégias"""
    
    def __init__(self):
        self.python = "/usr/bin/python3.10"
        self.pip = f"{self.python} -m pip"
        self.wheels_dir = Path("/content/drive/MyDrive/Stable_Diffusion_Dados/wheels")
        self.constraints_file = "/content/pip_constraints_sd.txt"
        self.results: List[VaccineResult] = []
        
    def run_command(self, cmd: str, desc: str = "", timeout: int = 300) -> Tuple[bool, str]:
        """Executa comando com timeout e captura de saída"""
        if desc:
            print(f"⏳ {desc}...")
        
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            
            if result.returncode != 0:
                return False, result.stderr
            
            return True, result.stdout
            
        except subprocess.TimeoutExpired:
            return False, f"Timeout após {timeout}s"
        except Exception as e:
            return False, str(e)
    
    def check_import(self, lib_name: str) -> bool:
        """Verifica se biblioteca pode ser importada"""
        ok, _ = self.run_command(
            f"{self.python} -c 'import {lib_name}'", 
            f"Verificando {lib_name}",
            timeout=10
        )
        return ok
    
    def ensure_wheels_dir(self) -> bool:
        """Garante que pasta de wheels existe no Drive"""
        try:
            self.wheels_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"❌ Erro ao criar pasta de wheels: {e}")
            return False
    
    def save_wheel_info(self, lib_name: str, version: str):
        """Salva informações sobre wheel instalado"""
        info_file = self.wheels_dir / f"{lib_name}.json"
        with open(info_file, 'w') as f:
            json.dump({
                "name": lib_name,
                "version": version,
                "installed_at": time.time()
            }, f, indent=2)
    
    def install_with_strategies(self, lib_name: str, strategies: List[str], 
                                import_name: Optional[str] = None) -> bool:
        """Tenta múltiplas estratégias em sequência"""
        if import_name is None:
            import_name = lib_name
        
        # Verifica se já está instalado
        if self.check_import(import_name):
            print(f"✅ {lib_name} já está instalado.")
            return True
        
        strategies_tried = 0
        for i, strategy in enumerate(strategies, 1):
            strategies_tried += 1
            print(f"\n📋 Tentativa {i}/{len(strategies)} para {lib_name}:")
            print(f"   Comando: {strategy[:80]}{'...' if len(strategy) > 80 else ''}")
            
            # Remove PIP_CONSTRAINT temporariamente durante instalação
            cmd = f"unset PIP_CONSTRAINT && {strategy}"
            
            ok, err = self.run_command(cmd, timeout=180)
            
            if ok and self.check_import(import_name):
                print(f"✅ {lib_name} instalado com sucesso!")
                
                # Salva informação do wheel
                self.save_wheel_info(lib_name, "installed")
                
                return True
            
            print(f"⚠️ Falha: {err[:100] if err else 'Erro desconhecido'}")
            time.sleep(2)
        
        print(f"❌ Todas as {len(strategies)} tentativas falharam para {lib_name}")
        return False
    
    # ==================== ESTRATÉGIAS POR BIBLIOTECA ====================
    
    def install_clip(self) -> bool:
        """CLIP (OpenAI) - 4 estratégias"""
        strategies = [
            # 1. Wheel local salvo
            f"test -f {self.wheels_dir}/clip*.whl && {self.pip} install --no-deps {self.wheels_dir}/clip*.whl",
            
            # 2. GitHub com --no-build-isolation (evita erro de setuptools)
            f"{self.pip} install --no-build-isolation 'https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip'",
            
            # 3. GitHub com setuptools<70 pré-instalado
            f"{self.pip} install 'setuptools<70' --quiet && {self.pip} install --no-build-isolation ftfy regex tqdm && {self.pip} install --no-build-isolation 'https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip'",
            
            # 4. Versão oficial do PyPI (fallback)
            f"{self.pip} install clip-by-openai"
        ]
        
        return self.install_with_strategies("CLIP", strategies, "clip")
    
    def install_bitsandbytes(self) -> bool:
        """bitsandbytes - 4 estratégias"""
        strategies = [
            # 1. Wheel local
            f"test -f {self.wheels_dir}/bitsandbytes*.whl && {self.pip} install --no-deps {self.wheels_dir}/bitsandbytes*.whl",
            
            # 2. Versão específica testada (0.43.3)
            f"{self.pip} install bitsandbytes==0.43.3",
            
            # 3. Range de versões compatíveis
            f"{self.pip} install 'bitsandbytes>=0.41.0,<0.44.0'",
            
            # 4. Última versão disponível
            f"{self.pip} install bitsandbytes"
        ]
        
        return self.install_with_strategies("bitsandbytes", strategies)
    
    def install_onnxruntime(self) -> bool:
        """ONNX Runtime - 4 estratégias"""
        strategies = [
            # 1. Wheel local GPU
            f"test -f {self.wheels_dir}/onnxruntime_gpu*.whl && {self.pip} install --no-deps {self.wheels_dir}/onnxruntime_gpu*.whl",
            
            # 2. GPU versão específica para CUDA 12
            f"{self.pip} install onnxruntime-gpu==1.17.1 --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/",
            
            # 3. GPU genérico (pip escolhe versão)
            f"{self.pip} install onnxruntime-gpu",
            
            # 4. CPU fallback (funciona mas mais lento)
            f"{self.pip} install onnxruntime"
        ]
        
        return self.install_with_strategies("onnxruntime", strategies, "onnxruntime")
    
    def install_insightface(self) -> bool:
        """InsightFace - 3 estratégias"""
        strategies = [
            # 1. Wheel local
            f"test -f {self.wheels_dir}/insightface*.whl && {self.pip} install --no-deps {self.wheels_dir}/insightface*.whl",
            
            # 2. Versão específica compatível com NumPy 2.x
            f"{self.pip} install insightface==0.7.3 onnx==1.16.1 albumentations==1.4.3",
            
            # 3. Versão mais recente
            f"{self.pip} install insightface onnx"
        ]
        
        return self.install_with_strategies("insightface", strategies)
    
    def install_numpy_safe(self) -> bool:
        """NumPy - Mantém versão <2.1.0"""
        if self.check_import("numpy"):
            # Verifica versão
            ok, out = self.run_command(f"{self.python} -c 'import numpy; print(numpy.__version__)'")
            if ok:
                version = out.strip()
                major, minor = map(int, version.split('.')[:2])
                if major < 2 or (major == 2 and minor < 1):
                    print(f"✅ NumPy {version} — compatível.")
                    return True
        
        print("📦 Instalando NumPy <2.1.0...")
        ok, _ = self.run_command(f"{self.pip} install 'numpy<2.1.0' --quiet")
        return ok and self.check_import("numpy")
    
    # ==================== RELATÓRIO E UTILITÁRIOS ====================
    
    def setup_pip_constraints(self):
        """Configura arquivo de constraints do PIP"""
        content = """numpy<2.1.0
scipy<1.14.0
opencv-python-headless<=4.10.0.84
shapely<2.1.0
        """
        
        with open(self.constraints_file, 'w') as f:
            f.write(content.strip())
        
        os.environ['PIP_CONSTRAINT'] = self.constraints_file
        print(f"🛡️ PIP_CONSTRAINT definido: {self.constraints_file}")
    
    def create_lock_file(self):
        """Cria arquivo de lock indicando ambiente pronto"""
        lock_path = "/content/env_ready.lock"
        with open(lock_path, 'w') as f:
            json.dump({
                "ready": True,
                "timestamp": time.time(),
                "results": [asdict(r) for r in self.results]
            }, f, indent=2)
        
        print(f"🔒 Lock file criado: {lock_path}")
    
    def generate_report(self):
        """Gera relatório final"""
        print("\n" + "="*60)
        print("📊 RELATÓRIO DO AUTOHEALER")
        print("="*60)
        
        total = len(self.results)
        healthy = sum(1 for r in self.results if r.status == Status.HEALTHY)
        fixed = sum(1 for r in self.results if r.status == Status.FIXED)
        failed = sum(1 for r in self.results if r.status == Status.FAILED)
        
        for result in self.results:
            icon = "✅" if result.status == Status.HEALTHY else \
                   "🔧" if result.status == Status.FIXED else \
                   "❌" if result.status == Status.FAILED else "⏭️"
            
            print(f"{icon} {result.name:30} [{result.status.value:8}] {result.duration:5.1f}s")
        
        print("-"*60)
        print(f"Total: {total} | ✅ {healthy} | 🔧 {fixed} | ❌ {failed}")
        print("="*60)
        
        if failed > 0:
            print(f"\n⚠️ {failed} biblioteca(s) falharam. Verifique o log acima.")
            print("O Forge pode iniciar, mas algumas funcionalidades estarão limitadas.")
        else:
            print("\n🎉 Todas as bibliotecas críticas estão funcionais!")
    
    # ==================== EXECUÇÃO PRINCIPAL ====================
    
    def heal_all(self):
        """Executa diagnóstico e cura completa"""
        start_time = time.time()
        
        print("🚀 INICIANDO AUTOHEALER HÍBRIDO v4.1.0")
        print("="*60)
        
        # Garante pasta de wheels
        self.ensure_wheels_dir()
        
        # Configura constraints
        self.setup_pip_constraints()
        
        # Bibliotecas críticas
        critical_libs = [
            ("NumPy", self.install_numpy_safe),
            ("CLIP (OpenAI)", self.install_clip),
            ("bitsandbytes", self.install_bitsandbytes),
            ("ONNX Runtime", self.install_onnxruntime),
            ("InsightFace", self.install_insightface),
        ]
        
        for name, func in critical_libs:
            lib_start = time.time()
            
            try:
                success = func()
                duration = time.time() - lib_start
                
                if success:
                    status = Status.FIXED
                    message = "Instalado com sucesso"
                else:
                    status = Status.FAILED
                    message = "Todas as estratégias falharam"
                
            except Exception as e:
                success = False
                duration = time.time() - lib_start
                status = Status.FAILED
                message = f"Exceção: {str(e)}"
            
            self.results.append(VaccineResult(
                name=name,
                status=status,
                message=message,
                duration=duration
            ))
        
        # Cria lock file
        self.create_lock_file()
        
        # Gera relatório
        self.generate_report()
        
        total_duration = time.time() - start_time
        print(f"\n⏱️ Tempo total: {total_duration:.1f}s")
        
        return all(r.status != Status.FAILED for r in self.results)


# ==================== PONTO DE ENTRADA ====================

if __name__ == "__main__":
    installer = LibraryInstaller()
    success = installer.heal_all()
    sys.exit(0 if success else 1)
