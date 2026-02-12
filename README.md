# IFRN 2026 - Consulta por Inscricao (Docling)

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

```bash
python parse_ifrn_docling.py
```

Arquivos gerados:
- `data/ifrn_2026_resultado.csv`
- `data/ifrn_2026_resultado.jsonl`

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
