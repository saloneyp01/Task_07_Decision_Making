# Task_07_Decision_Making
#### This repository contains the deliverables for Research Task 7: Ethical Implications of Decision Making, part of the research at Syracuse University. The task converts an LLM generated narrative about SU Women’s Lacrosse into a reproducible, auditable decision report for human stakeholders.
## Contents
- **Stakeholder_Report.pdf** – Main decision report with recommendations, ethics, and process notes  
- **Transcripts** – LLM prompt–response transcripts   
- **Data** – Cleaned CSV files (`wlax.csv`, derived summaries like `player_summary.csv`, `defense_index.csv` + more)  
- **Code** – Python scripts for cleaning, per game metrics, DCI calculation 
- **Visualizations** – LLM-labeled charts (PPG contributors, DCI)  

## Methods Summary
- Stats from official SU women’s lacrosse box scores (wlax.csv)
- Cleaned headers, extracted GP, converted stats to numeric.
- Computed totals and per game averages (G, A, PPG, GB_pg, CT_pg, TO_pg)
- Cross verified LLM recommendations against recomputed stats.

---

## Ethical Notes
- **Transparency:** All LLM generated outputs are labeled and verified against recomputed stats  
- **Fairness:** Role/usage bias and small sample bias acknowledged; no high stakes decisions without further validation  
- **Privacy:** Only public performance stats used  
