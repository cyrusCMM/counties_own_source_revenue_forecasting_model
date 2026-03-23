\# County Own-Source Revenue Forecasting Model  

\### A Data-Driven Framework for Subnational Fiscal Planning



\---



\## 1. Motivation



County revenue forecasting has traditionally assumed a stable relationship between economic activity (GCP) and Own-Source Revenue (OSR).  



This assumption is weak.



Across counties, revenue performance reflects:

\- administrative capacity  

\- compliance structures  

\- sector composition  

\- enforcement intensity  



—not just economic growth.



This work addresses that gap by building a \*\*county-specific, data-driven forecasting system\*\*.



\---



\## 2. Analytical Approach



The framework combines:

\- \*\*Machine learning (unsupervised clustering)\*\* → to identify structural similarities across counties  

\- \*\*Econometric modelling\*\* → to estimate and compare alternative revenue models  

\- \*\*Model selection logic\*\* → to assign the best-performing model per county  



Three competing models are evaluated:



1\. \*\*Trend-only model\*\*  

&#x20;  → captures administrative and structural momentum  



2\. \*\*Trend + elasticity model\*\*  

&#x20;  → links OSR to economic activity (GCP)  



3\. \*\*Trend + growth-adjusted model\*\*  

&#x20;  → captures short-run co-movement without imposing unstable long-run elasticity  



Model choice is based on:

\- forecast accuracy (MAPE)  

\- economic plausibility  

\- stability of parameters  



\---



\## 3. Structural Heterogeneity (Machine Learning Insight)



!\[Cluster Profiles](county\_cluster\_profiles.png)



Counties are grouped into \*\*three structural clusters\*\*.



Key patterns:

\- \*\*Cluster 1\*\*: Moderate capacity, relatively stable systems  

\- \*\*Cluster 2\*\*: High extraction, high dispersion (aggressive but volatile)  

\- \*\*Cluster 3\*\*: Low but stable revenue systems  



\*\*Implication:\*\*  

Counties do not behave uniformly. A single forecasting model is inappropriate.



\---



\## 4. Weak Economic Linkages



!\[Co-movement](county\_gcp\_vs\_osr\_dashboard.png)



Across counties:

\- OSR and GCP often move independently  

\- Timing and direction frequently diverge  



\*\*Implication:\*\*  

Economic growth alone is not a reliable predictor of revenue.



\---



\## 5. Decoupling: Linkage vs Extraction



!\[Linkage vs Extraction](county\_linkage\_vs\_extraction.png)



This is the central diagnostic.



Findings:

\- Some counties exhibit \*\*high revenue extraction with weak or negative economic linkage\*\*

\- Others show \*\*strong economic growth but limited revenue response\*\*



\*\*Interpretation:\*\*

\- Revenue performance is often \*\*policy-driven, not growth-driven\*\*

\- Administrative systems can override economic fundamentals



\---



\## 6. Effective Tax Rate Behaviour



!\[Effective Rate](effective\_rate\_diagnostics.png)



\- Large differences in effective tax rates across clusters  

\- High-revenue counties are also the most volatile  



\*\*Implication:\*\*

\- Revenue gains may be \*\*unsustainable if driven by unstable extraction mechanisms\*\*



\---



\## 7. Instability of Elasticities



!\[Elasticity Diagnostics](point\_elasticity\_diagnostics.png)



Elasticity estimates show:

\- extreme volatility  

\- negative values in some periods  

\- lack of consistency across counties  



\*\*Implication:\*\*

\- Traditional elasticity-based forecasting is unreliable  

\- Imposing a fixed elasticity risks large forecast errors  



\---



\## 8. What the Model Does Differently



Instead of forcing one structure, the model:



\- \*\*adapts to county reality\*\*

\- selects the best model per county

\- prioritizes forecast performance over theoretical convenience  



Outcome:



| Model Type | Counties |

|------------|---------|

| Trend-only | Majority |

| Elasticity-based | Limited |

| Growth-adjusted | Select cases |



\---



\## 9. Policy Implications



1\. \*\*Revenue is not a passive outcome of growth\*\*  

&#x20;  → It must be actively managed  



2\. \*\*Administrative capacity matters as much as economic base\*\*  

&#x20;  → Investment in systems and enforcement is critical  



3\. \*\*Uniform targets are misleading\*\*  

&#x20;  → County-specific strategies are required  



4\. \*\*Over-reliance on elasticity models is risky\*\*  

&#x20;  → Forecasting frameworks must allow structural flexibility  



\---



\## 10. Operational Use



This model is already deployable:



\- Automated model selection (`model\_selection.py`)  

\- Forecast engine (`model.py`)  

\- Interactive dashboard (`app.py`)  



Workflow:



```bash

python model\_selection.py

streamlit run app.py

