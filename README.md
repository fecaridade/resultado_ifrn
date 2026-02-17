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

## Observacao tecnica

O `DocumentConverter` padrao do docling tenta baixar modelos remotos.
Este projeto usa o backend local `DoclingParseV4DocumentBackend` para funcionar
offline e manter a extração em ambiente com rede restrita.
