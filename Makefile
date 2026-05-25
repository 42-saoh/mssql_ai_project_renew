PYTHON ?= python

.PHONY: test test-contract test-unit test-integration test-security test-eval test-e2e lint typecheck

test:
	$(PYTHON) -m pytest

test-contract:
	$(PYTHON) -m pytest tests/contract

test-unit:
	$(PYTHON) -m pytest tests/unit

test-integration:
	$(PYTHON) -m pytest tests/integration

test-security:
	$(PYTHON) -m pytest tests/security

test-eval:
	$(PYTHON) -m pytest tests/eval

test-e2e:
	$(PYTHON) -m pytest tests/e2e

lint:
	$(PYTHON) -m compileall apps packages services tests

typecheck:
	$(PYTHON) -m compileall apps packages services tests
