#!/bin/bash
cd /home/maomao/Gits/todo-app
/home/maomao/Gits/todo-app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
