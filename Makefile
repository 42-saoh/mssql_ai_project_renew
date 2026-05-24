.PHONY: test test-contract test-unit test-integration test-security test-eval test-e2e lint typecheck

test:
	python -m pytest

test-contract:
	python -m pytest tests/contract

test-unit:
	python -m pytest tests/unit

test-integration:
	python -m pytest tests/integration

test-security:
	python -m pytest tests/security

test-eval:
	python -m pytest tests/eval

test-e2e:
	python -m pytest tests/e2e

lint:
	python -m compileall apps packages services tests

typecheck:
	python -m compileall apps packages services tests
