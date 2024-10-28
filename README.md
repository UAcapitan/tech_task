# Documentation

## Running
- Before running, set API key to ai.py
- Set requirements using this command in console

`pip install fastapi pydantic passlib[bcrypt] python-jose cohere pytest requests`

- And then type this command in console to run API

`uvicorn main:app --reload`

## Running tests
- To run test, you need to type this command in console

`pytest test.py`

## Files of project
- main.py (API code)
- ai.py (file with function to interact with API AI)
- test.py (tests for 7 tasks in tech task)