.PHONY: check vim-docs schema-docs docs containers

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

containers:
	@echo "Building CI container..."
	cd tests/ci && \
	  ./rebuild && \
	  docker push puremourning/vimspector:test-$(shell uname -m)
	@echo "Building Manual container..."
	cd tests/manual && \
	  ./rebuild && \
	  docker push puremourning/vimspector:manual-$(shell uname -m)
