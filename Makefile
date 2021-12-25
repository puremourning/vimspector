.PHONY: check vim-docs schema-docs docs

check:
	@echo "Running flake8..."
	flake8 python3/ *.py
	@echo "Running vint..."
	vint autoload/ compiler/ plugin/ tests/ syntax/

vim-docs: README.md
	$(CURDIR)/update-vim-docs

schema-docs: docs/*.md docs/schema/*.json
	$(CURDIR)/update-schema-docs

docs: vim-docs schema-docs
