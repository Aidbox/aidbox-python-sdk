.PHONY: test
test:
	pytest --cov=app

.PHONY: testcov
testcov:
	pytest --cov=app && (echo "building coverage html, view at './htmlcov/index.html'"; coverage html)
