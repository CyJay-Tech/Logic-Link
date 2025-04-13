#!/bin/bash
# Ativa o ambiente virtual e executa o app

if [ ! -d "venv" ]; then
  echo "Ambiente virtual não encontrado. Execute: python3 -m venv venv && source venv/bin/activate && pip install PyQt5"
  exit 1
fi

source venv/bin/activate
python -m src.main