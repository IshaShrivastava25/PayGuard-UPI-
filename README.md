# PayGuard-UPI-
PayGuard — a full-stack, explainable anomaly-detection system for UPI fraud.
# PayGuard

Anomaly-based fraud detection for UPI-style transactions, with per-transaction explanations.

PayGuard scores a transaction, flags it for analyst review (it never auto-blocks), and shows which factors pushed the score up or down using SHAP. Five models are compared on the same data: three supervised (Logistic Regression, Random Forest, XGBoost) and two unsupervised (Isolation Forest, One-Class SVM).

> **Data note:** real UPI data is confidential. This project uses the public PaySim simulator, reshaped to a UPI-style schema, with extra synthetic fraud patterns injected. All results are on synthetic data and may not carry over to real traffic.

## Status

- [x] Data exploration, UPI schema adaptation, and synthetic fraud injection
- [x] Behavioral feature engineering and imbalance-handling experiments
- [x] Five-model comparison
- [x] SHAP explainability
- [x] FastAPI prediction API
- [x] PostgreSQL persistence for users and predictions
- [x] JWT authentication and protected prediction endpoints
- [x] Prediction history with pagination and label filtering
- [x] Individual prediction retrieval with user-level access checks
- [ ] React dashboard
- [ ] Docker, CI, and deployment

## Headline result

Champion model: **XGBoost trained on SMOTE-resampled data**, evaluated on a held-out test set of 16,000 transactions (45 fraud cases).

| Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|
| 0.72 | 0.80 | 0.758 | 0.984 |

The full per-model table is in `models/best_model_per_type.csv`, and every model/variant is in `models/all_models_all_variants.csv`.

## Repository layout

```
notebooks/   numbered pipeline, run in order (01 -> 06) + evaluation.py helper
backend/     FastAPI scoring service
models/      result tables and charts; inference_bundle.pkl (the deployed model)
data/        local only, not committed (regenerate with notebooks 01-03)
```

## Reproduce the pipeline

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# dataset (needs a Kaggle API token in ~/.kaggle/kaggle.json)
kaggle datasets download -d ealaxi/paysim1 -p data --unzip

jupyter notebook
```

Run the notebooks in `notebooks/` in this order:

| Notebook | Purpose |
|---|---|
| `01_data_exploration` | load PaySim, check class balance, take an 80k stratified sample |
| `02_schema_adaptation_and_fraud_injection` | UPI-style fields, timestamps, injected fraud patterns |
| `03_feature_engineering_and_preprocessing` | features, split, scaling, SMOTE / undersampling / class weights |
| `04a` to `04e` | Logistic Regression, Random Forest, XGBoost, Isolation Forest, One-Class SVM |
| `05_final_model_comparison` | consolidated tables, charts, champion selection |
| `06_shap_explainability` | SHAP explainer and `models/inference_bundle.pkl` |

## Run the API

```powershell
cd backend
pip install fastapi "uvicorn[standard]"
python tests/parity_check.py        # must print PARITY OK
uvicorn app.main:app --reload       # docs at http://127.0.0.1:8000/docs
```

`models/inference_bundle.pkl` is committed so the API runs without retraining. Use the same package versions as `requirements.txt`, since the pickle depends on the scikit-learn and XGBoost versions it was saved with.

## Known limitations

- **Synthetic data.** Injected fraud patterns are an approximation of real behavior.
- **Sparse sender history.** Every sender appears once in the 80k sample, so the history-based features (`sender_txn_count_so_far`, `sender_avg_amount_so_far`, `is_new_receiver`) are constant and carry no signal.
- **`hour_of_day` dominates.** It is the top SHAP feature while `is_off_hours` is near zero, which suggests the model leans on PaySim's daily activity pattern rather than the injected off-hours rule.
- **Small test fraud count.** With 45 fraud cases, F1 differences of about 0.01 to 0.02 between the top models are within noise. The ROC-AUC gap is the more reliable comparison.
- **SHAP units.** Contributions are in log-odds, not probabilities.
- **One-Class SVM** is trained on a 6,000-row random subsample because RBF kernels scale poorly.


## Tech Stack

- **Language:** Python
- **API:** FastAPI
- **Database:** PostgreSQL
- **Authentication:** JWT
- **Password security:** bcrypt
- **Machine learning:** scikit-learn, XGBoost, imbalanced-learn
- **Explainability:** SHAP
- **Data processing:** pandas, NumPy

Planned: React dashboard, Docker, CI/CD, and deployment.

## Credits

PaySim: E. A. Lopez-Rojas, A. Elmir and S. Axelsson, "PaySim: A financial mobile money simulator for fraud detection", EMSS 2016. Dataset on Kaggle (`ealaxi/paysim1`, CC-BY-SA-4.0); it is not redistributed in this repository.
