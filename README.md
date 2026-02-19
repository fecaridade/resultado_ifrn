# IFRN - Consulta por Inscricao (Docling)

Sistema simples de terminal para:
- extrair dados do PDF com `docling`
- consultar por inscricao

## 1) Preparar ambiente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Extrair dados do PDF

Padrão (arquivo 2026):

```bash
python parse_ifrn_docling.py
```

Arquivo específico (ex.: 2025):

```bash
python parse_ifrn_docling.py \
  --pdf Resultado_Final_Retificado_-_IFRN_Cursos_Técnicos_de_Nível_Médio_na_Forma_Inte_ssh7Dgc.pdf \
  --csv-out data/ifrn_2025_resultado.csv \
  --jsonl-out data/ifrn_2025_resultado.jsonl
```

Arquivos gerados (conforme parâmetros):
- `data/*.csv`
- `data/*.jsonl`

## 3) Consultar por inscricao

Consulta direta:

```bash
python ifrn_cli.py --inscricao 1194554-8
```

Modo interativo:

```bash
python ifrn_cli.py
```

### 4) Filtrar registros por lista de nomes

```bash
python ifrn_cli.py --filter_by_name nomes --csv data/resultado.csv
```

`nomes` é um arquivo com nomes de aprovados. Um nome por linha. Comumente, pode ser uma relação de uma turma.
Para analises de turmas isso é mais assertivo que filtrar as pessoas aprovadas, pois nem todas
dessas realmente se matriculam, além de que pessoas que aparecem nesse resultado como "Em espera" podem ter sido chamados depois.

Caso um nome no arquivo de `nomes` não seja encontrado, o processamento é interrompido e você
deverá fazer a correção. É comum que nomes estejam diferentes por erro de digitação.

Caso um nome apareça mais de uma vez, será exibido a primeira ocorrência. É comum que um mesmo
candidato apareça em uma de uma lista (Geral, Baixa Renda...). As classificações são diferentes, mas as notas são iguais. Observar se não é um homônimo de outra turma.


## Observação técnica

O `DocumentConverter` padrao do docling tenta baixar modelos remotos.
Este projeto usa o backend local `DoclingParseV4DocumentBackend` para funcionar
offline e manter a extração em ambiente com rede restrita.
