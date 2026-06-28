# Célula 3: Vacinas e Dependências (com AutoHealer POO)

Esta célula usa Programação Orientada a Objetos para instalar dependências críticas.

```python
import os, sys

print('💉 ETAPA 3: VACINAS E DEPENDÊNCIAS (AUTOHEALER COM POO)')
print('═' * 60)

# Copia módulo auto_healer.py do Drive se existir
drive_lib = '/content/drive/MyDrive/Stable_Diffusion_Dados/lib/auto_healer.py'
local_lib = '/workspace/V4/lib/auto_healer.py'

# Tenta importar do Drive primeiro (versão persistente)
if os.path.exists(drive_lib):
    print(f'📦 Carregando auto_healer.py do Drive...')
    !cp {drive_lib} /tmp/auto_healer.py
elif os.path.exists(local_lib):
    print(f'📦 Carregando auto_healer.py local...')
    !cp {local_lib} /tmp/auto_healer.py
else:
    print('❌ auto_healer.py não encontrado!')
    print('   Execute a Célula 0 primeiro para enviar cache-manager.')
    raise FileNotFoundError('auto_healer.py necessário')

# Adiciona ao path e importa
sys.path.insert(0, '/tmp')
from auto_healer import LibraryInstaller, setup_pip_constraint, print_summary

# Configura PIP_CONSTRAINT
print('\n🔒 Configurando PIP_CONSTRAINT...')
constraint_file = setup_pip_constraint()
print(f'   ✅ PIP_CONSTRAINT = {constraint_file}')
print('   📋 Regras: numpy<2.1.0, scipy<1.14.0, setuptools<70.0.0')

# Cria instalador com POO
installer = LibraryInstaller(
    python_bin='python3.10',
    wheels_dir='/content/drive/MyDrive/Stable_Diffusion_Dados/wheels',
    timeout=300
)

# Executa todas as vacinas
print('\n💉 Aplicando vacinas...')
print('─' * 50)
results = installer.run_all_vaccines()

# Imprime relatório
print('\n' + installer.generate_report())

# Imprime resumo final
print_summary(installer)

# Verifica falhas críticas
failed_count = sum(1 for r in results if r.status.name == 'FAILED')
if failed_count > 0:
    print(f'\n⚠️ ALERTA: {failed_count} biblioteca(s) falharam.')
    print('   O Forge pode tentar instalar versões internas.')
    print('   Você pode executar esta célula novamente.')
else:
    print('\n✅ ETAPA 3 CONCLUÍDA COM SUCESSO!')
```

## Como Funciona

### Estrutura POO

A classe `LibraryInstaller` implementa:

1. **Múltiplas estratégias por biblioteca** - Cada biblioteca tem 3-4 estratégias de instalação
2. **Persistência de wheels** - Wheels são salvos no Drive após primeira instalação
3. **Verificação prévia** - Checa se já está instalado antes de tentar instalar
4. **Relatório detalhado** - Mostra tempo, estratégias tentadas e status

### Bibliotecas Tratadas

| Biblioteca | Estratégias | Fallback |
|------------|-------------|----------|
| CLIP | Wheel salvo → PyPI git → Commit fixo → PyPI oficial | Usa CLIP interno do Forge |
| NumPy | Versão <2.1.0 | - |
| bitsandbytes | Wheel salvo → 0.43.3 → >=0.43.0,<0.45.0 → latest | Usa versão interna do Forge |
| ONNX Runtime | Wheel GPU salvo → GPU 1.17.1 → GPU genérico → CPU | Face swap pode não funcionar |
| InsightFace | Wheel salvo → 0.7.3 → latest | ReActor pode não funcionar |

### Vantagens da Abordagem POO

- ✅ **Código reutilizável** - Módulo pode ser usado em outras células
- ✅ **Fácil manutenção** - Adicionar nova estratégia é só adicionar à lista
- ✅ **Relatórios consistentes** - Mesmo formato para todas bibliotecas
- ✅ **Extensível** - Fácil adicionar novas bibliotecas
- ✅ **Debug facilitado** - Logs detalhados por estratégia

### Próximos Passos

Após executar esta célula:
1. Verifique se todas bibliotecas estão ✅
2. Se alguma ❌ falhou, execute novamente (pode ser transient error)
3. Prossiga para Célula 4: Instalar Extensões
