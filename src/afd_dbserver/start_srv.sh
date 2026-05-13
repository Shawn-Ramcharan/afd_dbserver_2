#!/bin/bash
source /home/shawn.ramcharan/Documents/development_projects/afd_dbserver2/env/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8008 --reload

