.PHONY: help test check demo clean

PYTHON ?= python3
PYTHONPATH := src

help:
	@echo "make check  Compile modules and run all dependency-free tests"
	@echo "make demo   Validate, compile SQL, and render lineage"
	@echo "make clean  Remove generated artifacts and bytecode"

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests -v

check:
	$(PYTHON) -m compileall -q src tests
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests -v

demo:
	mkdir -p artifacts
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m semantic_metrics --catalog examples/catalog.json validate
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m semantic_metrics --catalog examples/catalog.json compile \
		--metric gross_revenue --dimension country --dimension channel \
		--grain day --start 2026-01-01 --end 2026-02-01 > artifacts/gross_revenue.sql
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m semantic_metrics --catalog examples/catalog.json lineage \
		--format mermaid > artifacts/lineage.mmd

clean:
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; shutil.rmtree('artifacts', ignore_errors=True)"

