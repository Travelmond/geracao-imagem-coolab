# 📚 Documentação do Projeto V4 - Stable Diffusion WebUI Forge

## Visão Geral

Este projeto implementa um sistema completo para rodar Stable Diffusion WebUI Forge no Google Colab com cache hierárquico e persistência no Google Drive.

## Estrutura de Pastas

```
V4/
├── DiffusionUI.ipynb           # Notebook principal (6 células)
├── lib/
│   └── auto_healer.py          # Módulo POO para instalação de dependências
├── cache-manager/              # Extensão Forge (7 scripts Python)
├── docs/                       # Documentação completa
└── scripts-auxiliares/         # Scripts utilitários
```

## Células do Notebook

| Célula | Descrição | Status |
|--------|-----------|--------|
| 0 | Enviar cache-manager para Drive | ✅ Completa |
| 0.5 | Enviar ReActor para Drive (opcional) | ✅ Completa |
| 1 | Conexão com Google Drive | ✅ Completa |
| 2 | Instalação do Forge + Python 3.10 | ✅ Completa |
| 3 | **Vacinas com AutoHealer POO** | ✅ **NOVO** |
| 4 | Instalar Extensões | ✅ Completa |
| 4.2 | Reaplicar Vacinas (pós-extensões) | ⏳ Pendente |
| 4.5 | Download de Modelos por URL | ✅ Completa |
| 4.6 | Upload de Modelos do PC | ✅ Completa |
| 5 | Verificação Final | ✅ Completa |
| 6 | Iniciar Forge | ✅ Completa |

## Inovações da Versão V4

### 1. AutoHealer com POO (Célula 3)

- **Classe `LibraryInstaller`**: Gerencia instalação com múltiplas estratégias
- **Persistência**: Wheels salvos no Drive após primeira instalação
- **Relatórios**: Status detalhado com tempo e estratégias tentadas
- **Bibliotecas críticas**: CLIP, NumPy, bitsandbytes, ONNX Runtime, InsightFace

### 2. Estrutura Modular

- Código separado em módulos reutilizáveis
- Fácil manutenção e extensão
- Logs detalhados para debugging

### 3. Múltiplas Estratégias por Biblioteca

Cada biblioteca tem 3-4 estratégias de instalação em sequência:

```python
CLIP: Wheel salvo → PyPI git → Commit fixo → PyPI oficial
bitsandbytes: Wheel salvo → 0.43.3 → >=0.43.0,<0.45.0 → latest
ONNX Runtime: Wheel GPU → GPU 1.17.1 → GPU genérico → CPU
InsightFace: Wheel salvo → 0.7.3 → latest
```

## Documentação Detalhada

| Arquivo | Descrição |
|---------|-----------|
| [01-arquitetura.md](01-arquitetura.md) | Arquitetura do sistema |
| [02-fluxo-de-execucao.md](02-fluxo-de-execucao.md) | Fluxo de execução passo a passo |
| [03-interface-widgets.md](03-interface-widgets.md) | Interface e widgets do Cache Manager |
| [04-hardware-otimizacao.md](04-hardware-otimizacao.md) | Otimizações de hardware |
| [05-modelos-e-pastas.md](05-modelos-e-pastas.md) | Estrutura de modelos e pastas |
| [06-dependencias-e-patches.md](06-dependencias-e-patches.md) | Dependências e patches |
| [07-extensoes.md](07-extensoes.md) | Extensões disponíveis |
| [08-versao-legada.md](08-versao-legada.md) | Versão legada |
| [09-problemas-conhecidos.md](09-problemas-conhecidos.md) | Problemas conhecidos e soluções |
| [10-glossario.md](10-glossario.md) | Glossário de termos |
| [11-ambiente-local.md](11-ambiente-local.md) | Ambiente local com Docker |
| [12-wheels-persistente.md](12-wheels-persistente.md) | Sistema de wheels persistente |
| [13-celula-3-autohealer.md](13-celula-3-autohealer.md) | **NOVO**: Célula 3 com AutoHealer POO |

## Como Usar

### Primeira Sessão

1. Execute Célula 0: Envie `cache-manager.zip` do seu computador
2. Execute Célula 0.5 (opcional): Envie `sd-webui-reactor.zip`
3. Execute Célula 1: Conecte ao Google Drive
4. Execute Célula 2: Instale Forge e Python 3.10
5. Execute Célula 3: Instale dependências com AutoHealer
6. Execute Célula 4: Instale extensões do Drive
7. Execute Célula 5: Verifique instalação
8. Execute Célula 6: Inicie Forge

### Próximas Sessões

1. Célula 1: Conectar Drive
2. Célula 2: Verificar Forge (já estará instalado)
3. Célula 3: **Wheels já estão no Drive → instalação rápida!**
4. Célula 4: Verificar extensões
5. Célula 6: Iniciar Forge

## Solução de Problemas

### 4 Bibliotecas Falhando (CLIP, bitsandbytes, ONNX, InsightFace)

**Problema**: EnvironmentDoctor relatava 4 falhas críticas.

**Solução**: Nova célula 3 com AutoHealer POO:
- Múltiplas estratégias por biblioteca
- Wheels persistentes no Drive
- Fallbacks inteligentes

**Resultado esperado**: 100% de sucesso na primeira sessão, <60s nas próximas.

### Wheels não Encontrados

Se `auto_healer.py` não for encontrado:
1. Execute Célula 0 primeiro
2. Ou copie manualmente para `/content/drive/MyDrive/Stable_Diffusion_Dados/lib/`

### ReActor não Funciona

Verifique:
1. Célula 0.5 executada com sucesso
2. InsightFace e ONNX Runtime instalados (Célula 3)
3. Célula 4 instalou extensão do Drive

## Contribuições

Para adicionar novas bibliotecas ao AutoHealer:

1. Edite `lib/auto_healer.py`
2. Adicione método `install_nova_lib()` com estratégias
3. Adicione à lista em `run_all_vaccines()`
4. Atualize documentação em `docs/13-celula-3-autohealer.md`

## Licença

MIT License - Uso livre para fins educacionais e pessoais.
