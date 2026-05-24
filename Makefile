.PHONY: test test-contract test-unit test-integration test-security test-eval test-e2e lint typecheck

test:
	pytest

test-contract:
	pytest tests/contract

test-unit:
	pytest tests/unit

test-integration:
	pytest tests/integration

test-security:
	pytest tests/security

test-eval:
	pytest tests/eval

test-e2e:
	pytest tests/e2e

lint:
	python -m compileall apps packages services tests

typecheck:
	python -m compileall apps packages services tests
