#!/bin/bash
export APP_PORT=${APP_PORT:-8501}
streamlit run app.py --server.port "$APP_PORT" --server.headless true
