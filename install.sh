#!/bin/bash
# pre-requisite: python poetry 1.4.2
cd app/ai-investmate-be
poetry install
cd ../..
cd app/ai-investmate-streamlit
poetry install
cd ../..
cd app/ai-investmate-worker
poetry install