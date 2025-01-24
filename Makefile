install:
	uv sync

dev:
	uv run flask --debug --app page_analyzer:app run

PORT ?= 8000
start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

build:
	./build.sh

PORT ?= 8000
render-start:
	source .venv/bin/activate && gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app