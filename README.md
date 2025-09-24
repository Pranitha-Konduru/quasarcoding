# QUASAR GUI Development Intern – Coding Assignment

## Overview
This repository contains my solution to the QUASAR GUI Development Intern coding screener.  
It loads the provided EEG/ECG CSV and displays an interactive, scrollable, zoomable plot of all EEG and ECG channels.

Create and activate a virtual environment:

python3 -m venv venv
source venv/bin/activate   

Install dependencies:

pip install pandas numpy plotly


Generate the interactive plot:

python plot_eeg_ecg.py \
    --input "EEG and ECG data_02_raw.csv" \
    --output quasar_eeg_ecg.html


Open quasar_eeg_ecg.html in a browser to explore the data.

