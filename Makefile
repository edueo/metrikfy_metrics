.PHONY: run freeze-deps

run:
	GOOGLE_APPLICATION_CREDENTIALS="/Users/eduardo.alencar/.ssh/splendid-flow-290316-0e656ffda3a1.json" PORT=8088 python3 main.py

freeze-deps:
	pip3 freeze > requirements.txt

testelocal:
	curl "http://localhost:8088" -H "Content-Type:application/json" -H "X-UID:7P7XMLKzHwQIjb9q5SgQDUd9bLm1"

testeprod:
	curl "https://metrics-e24zyhbnkq-uc.a.run.app?accounts=act_1360566347624412&campaigns=23846895715500393,23846093461800393,23846897167180393" -H "Content-Type:application/json" -H "X-UID:7P7XMLKzHwQIjb9q5SgQDUd9bLm1"

