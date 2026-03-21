.PHONY: css-build css-prod css-dev css-status

css-build:
	python3 scripts/css_tools.py build

css-prod:
	python3 scripts/css_tools.py build
	python3 scripts/css_tools.py mode prod

css-dev:
	python3 scripts/css_tools.py mode dev

css-status:
	python3 scripts/css_tools.py status
