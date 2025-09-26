.PHONY: help db_list db_apply db_init db_seed test_tool

help:
	@echo "Comandos disponíveis:"
	@echo "  make db_list    - Lista os arquivos .sql detectados (ordem de execução)"
	@echo "  make db_init    - Aplica o schema inicial e o seed de status"
	@echo "  make db_apply   - Aplica todos os arquivos .sql do diretório sql/"
	@echo "  make db_seed    - Reaplica apenas o seed de status"
	@echo "  make test_tool  - Roda os testes de ferramentas (arquivo único)"
	@echo "  make test_tool_verbose - Roda os testes mostrando prints (pytest -s)"

# ---- Banco de Dados (migracoes simples via scripts/migrate.py) ----
db_list:
	python scripts/migrate.py --dir sql --list

db_apply:
	python scripts/migrate.py --dir sql

db_init:
	python scripts/migrate.py --dir sql --files 00_drop_crm_tables.sql 01_crm_schema.sql 02_seed_status_lead.sql

db_seed:
	python scripts/migrate.py --dir sql --files 02_seed_status_lead.sql

test_tool:
	python -m pytest -q tests/test_tools_m1a.py

test_tool_verbose:
	python -m pytest -s -q tests/test_tools_m1a.py
