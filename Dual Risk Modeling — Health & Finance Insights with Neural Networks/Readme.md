# 🧠 Project Title: Dual Risk Modeling — Health & Finance Insights with Neural Networks

This project applies a full data science pipeline — from preprocessing and visualization to deep learning-based prediction — across two real-world risk modeling scenarios:

1. **Stroke Risk Prediction** (Healthcare)
2. **Loan Approval Prediction** (Finance)

It integrates **exploratory data analysis (EDA)**, **multi-layer perceptron (MLP) models**, and **visual storytelling** using Python.

---

## 🎯 Objective

- Analyze and visualize real-world tabular data from health and finance.
- Train neural network classifiers (MLPs) to predict:
  - Stroke occurrence (binary classification)
  - Loan approval/default status (binary classification)

---

## 🧬 Datasets

### 🏥 Healthcare Dataset: Stroke Prediction
- **File:** `healthcare-dataset-stroke-data.csv`
- **Target:** `stroke`
- **Key Features:** Age, Gender, BMI, Glucose Level, Heart Disease, Smoking Status

### 💸 Financial Dataset: Loan Approval
- **File:** `loan_data.csv`
- **Target:** `Loan_Status`
- **Key Features:** Applicant Income, Loan Amount, Credit Score, Term, Marital Status

---

## 🧼 Data Preprocessing

### ✅ Common Preprocessing:
- **Missing Values:** Imputed (mean/mode) for `bmi`, loan features.
- **Encoding:** LabelEncoder + One-hot encoding for categorical data.
- **Scaling:** MinMaxScaler for normalized numeric input to neural networks.

### 🔧 Feature Engineering:
- **Stroke Dataset:**
  - `age_category`, risk indicators based on glucose/BMI
- **Loan Dataset:**
  - `fico_cat`, `DTI` (Debt-to-Income Ratio), and log transformations

---

## 📊 Exploratory Data Analysis (EDA)

### Stroke Dataset:
- Countplots for categorical variables
- Histograms of numeric variables

#### 📉 Stroke Prediction Histogram  
![Stroke Prediction Histogram](./images/stroke%20prediction%20histogram.png)

- **Correlation Heatmap:**

![Stroke Correlation Heatmap](./Dual Risk Modeling — Health & Finance Insights with Neural Networks/images/corelation heatmap - loan dataset.png).

---

### Loan Dataset:
- Bar charts and box plots for income, loan status, and fico score
- **Correlation Heatmap:**

![Loan Correlation Heatmap](./images/corelation%20heatmap%20-%20loan%20dataset.png)

---

## 🤖 Model Architecture: Multi-Layer Perceptron (MLP)

### 🔧 Design:
- **Input:** Feature vectors after encoding
- **Hidden Layers:** 2 layers with ReLU
- **Output:** Sigmoid (binary)
- **Loss:** Binary CrossEntropy
- **Optimizer:** Adam

---

### 🧪 Training & Evaluation:
- Split into train/test
- Tracked:
  - Accuracy over epochs
  - Loss
  - Confusion matrix (optional)

---

## 📈 Evaluation Summary

| Metric                | Stroke Model | Loan Model |
|----------------------|--------------|------------|
| Accuracy              | ✓            | ✓          |
| Loss (Binary CE)      | ✓            | ✓          |
| Feature Engineering   | Extensive    | Extensive  |
| Visual Correlations   | ✔ Heatmap    | ✔ Heatmap  |

---

## 🛠️ Technologies Used

- Python
- Pandas, NumPy
- Seaborn, Matplotlib
- Scikit-learn
- PyTorch


