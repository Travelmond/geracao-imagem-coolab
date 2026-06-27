# 📓 Histórico de Erros e Soluções (Troubleshooting)

Este documento registra os principais problemas encontrados durante a refatoração do projeto para a Versão 3, bem como as decisões de arquitetura e correções aplicadas para superá-los.

---

## 1. Falhas no Auto-Healing (EnvironmentDoctor)

### 1.1 O Colapso das Compilações (Wheel Build Failures)
**Sintoma:** No Google Colab, a Etapa 3 (Diagnóstico) reportava falhas críticas (`subprocess-exited-with-error`) ao tentar instalar pacotes como `CLIP`, `bitsandbytes`, `onnxruntime` e `insightface`.
**Log:** `DEPRECATION: Setting PIP_CONSTRAINT will not affect build constraints in the future... Getting requirements to build wheel did not run successfully.`
**Causa:** A vacina `PIP_CONSTRAINT` (que impede que o Numpy exceda a versão 2.0) estava sendo executada como a 3ª vacina. O instalador do PIP isola o ambiente para compilar bibliotecas a partir do código fonte (build_wheel). Quando ele tentava construir pacotes que precisavam do Numpy mais recente temporariamente, a barreira do `PIP_CONSTRAINT` travava a compilação, matando o processo inteiro.
**Solução Aplicada em `auto_healer.py`:**
- A ordem de execução foi alterada. A vacina `PIPConstraintVaccine` foi movida para ser a **11ª etapa (penúltima)**.
- Adicionou-se uma rotina de limpeza `os.environ.pop("PIP_CONSTRAINT", None)` no método `__init__` do `EnvironmentDoctor` para garantir que, caso o usuário rodasse o script duas vezes, a restrição fantasma na RAM fosse deletada antes de começar as novas compilações.

### 1.2 Assinatura de Classe Inválida no Notebook
**Sintoma:** `TypeError: EnvironmentDoctor.__init__() got an unexpected keyword argument 'python_cmd'`
**Causa:** A chamada original no notebook instanciou o doutor passando parâmetros explícitos: `EnvironmentDoctor(python_cmd='...', drive_path='...', etc)`. Contudo, a classe foi refatorada por um subagente para ser totalmente autônoma e ler os caminhos globais diretamente do `lib/version_pins.py`, deixando de aceitar argumentos.
**Solução:** Foi aplicado um patch direto no JSON do arquivo `DiffusionUI_v3.ipynb`, substituindo a inicialização manual por um simples `doctor = EnvironmentDoctor()`.

---

## 2. Problemas no Tratamento de Arquivos do Notebook

### 2.1 Erro de Edição JSON `.ipynb`
**Sintoma:** Falha ao usar a ferramenta interna da IA (`multi_replace_file_content`) para editar o arquivo Jupyter. Erro: `you may not edit files with the extension .ipynb`.
**Causa:** Extensões Jupyter são grandes arquivos JSON, extremamente fáceis de corromper com ferramentas de substituição baseadas em regex que operam linha a linha.
**Solução:** Substituímos a abordagem e começamos a criar scripts temporários (`scratch/patch_nb.py`) que abrem o arquivo como um dicionário real de Python (`json.load`), fazem a manipulação no objeto `cells`, e em seguida salvam novamente de maneira sintaticamente correta (`json.dump`).

### 2.2 Tokens Inesperados no Bash (Quotes Escaping)
**Sintoma:** Ao injetar o script rico de IU via linha de comando (`python3 -c 'import json...'`), a execução falhou com: `bash: -c: linha 22: erro de sintaxe próximo ao token inesperado '('`.
**Causa:** O script de IU tinha muitas aspas simples e duplas complexas, o que levou a uma quebra de escape de strings no motor de terminal do Linux (Bash).
**Solução:** A execução arbitrária via bash foi evitada. Todo código de automação complexa foi movido para arquivos `.py` intermediários temporários antes de serem executados.

---

## 3. Desafios de Sincronização e Caching do Usuário

### 3.1 Falta de Sincronização com o Drive Colab
**Sintoma:** O arquivo `auto_healer.py` foi corrigido localmente, mas o Colab continuava reportando falhas na `PIP Constraint` sendo rodada no passo 3.
**Causa:** A arquitetura do Colab v3 puxa a pasta `/lib` através da cópia recursiva do Google Drive (`shutil.copytree(lib_src, lib_dst)`). Como as modificações de salvamento ocorreram localmente na máquina do desenvolvedor e o usuário não refez o upload para o seu próprio Google Drive, o Colab continuou puxando a versão prévia que possuía o bug na ordem das vacinas.
**Solução:** Reforço do fluxo de implantação. É estritamente necessário orientar o usuário a substituir (via upload manual ou sync tool) qualquer arquivo da `lib` alterado localmente antes de reexecutar as células na Nuvem.
