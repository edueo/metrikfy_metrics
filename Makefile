.PHONY: run freeze-deps

run:
	GOOGLE_APPLICATION_CREDENTIALS="/Users/eduardo.alencar/.ssh/splendid-flow-290316-0e656ffda3a1.json" PORT=8088 python3 main.py

freeze-deps:
	pip3 freeze > requirements.txt
