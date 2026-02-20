@echo off
cd /d "C:\Users\USER\Desktop\Claude Development\Claude economic-data-collector"
start http://localhost:8501
streamlit run dashboard.py
