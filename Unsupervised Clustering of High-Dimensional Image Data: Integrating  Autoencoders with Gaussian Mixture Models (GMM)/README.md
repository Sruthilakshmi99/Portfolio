# Unsupervised Clustering of High-Dimensional Image Data: Integrating Autoencoders with Gaussian Mixture Models (GMM)

## Project Overview
This project presents a novel and scalable approach for clustering high-dimensional image data using a combination of ResNet-18 based Autoencoders and Gaussian Mixture Models (GMM). The primary objective is to handle complex image datasets by compressing them into meaningful latent space representations and applying GMM for effective clustering.

This method is particularly useful for tasks involving large-scale image data like:
- Medical Imaging
- Robotics
- Satellite Image Analysis
- Anomaly Detection

This project was developed as part of the MSc Data Science Dissertation:

> *"Unsupervised Clustering of High-Dimensional Image Data: Integrating Autoencoders with Gaussian Mixture Models"*

---

---

## Dataset

Dataset used: [CIFake Dataset - Real and AI Generated Images](https://www.kaggle.com/datasets/birdy654/cifake-real-and-ai-generated-synthetic-images)

Dataset contains:
- Real Images (natural photos)
- Simulated (AI-generated) Images

---

## Architecture Overview

### High-Level Architecture Flow

This architecture integrates two main components:

1. **ResNet-18 Based Autoencoder**  
   - Encoder compresses high-dimensional images to a lower-dimensional latent space.
   - Decoder reconstructs images to validate feature retention.

2. **Gaussian Mixture Model (GMM) for Clustering**  
   - GMM clusters the encoded latent representations based on probabilistic modeling.
   - Allows flexible modeling of complex data distributions beyond spherical clusters.

> ![Architecture Diagram](images/architecture.png)

---

### Autoencoder Architecture Diagram
> ![ResNet18 Autoencoder Architecture](images/Resnet18%20autoencoder%20architecture.png)

---

## Data Samples

### Real Images Sample
> ![Samples of Real Images](images/Samples%20of%20Real%20images.png)

### Fake/Simulated Images Sample
> ![Samples of Fake Images](images/Samples%20of%20fake%20images.png)

---

## Model Evaluation and Results

The proposed Autoencoder-GMM architecture was evaluated against the traditional K-Means clustering method.

### Key Findings:

- Autoencoder-GMM outperformed K-Means in clustering accuracy and interpretability.
- GMM provided flexibility in handling complex cluster shapes.
- Significant reduction in reconstruction loss, demonstrating high-quality feature retention.

---

### Training Loss Over Epochs
> ![Comparison of Original and Reconstructed Images](images/Comparison%20of%20original%20and%20reconstructed%20images.png)

---

### Latent Space Representation
> ![Original vs Encoded Images](images/Original%20and%20Encoded%20images.png)

---

### GMM Clustering Results on Real Data
> ![Real Data and GMM Cluster Means](images/Real%20Data%20points%20and%20gmm%20means.png)

---

### Scatter Plot of Real Data Clusters
> ![Scatter Plot of Real Data](images/Scatter%20plot%20for%20real%20data.png)

---

## Results Summary

This approach successfully clustered both real and simulated images, with robust performance on unseen data.

### Achievements:

- Significant dimensionality reduction while preserving critical features.
- Effective clustering of real and simulated images in latent space.
- Better handling of complex cluster structures than K-Means.
- Robust generalization to unseen images.

---

## Evaluation Metrics Used:

- Bayesian Information Criterion (BIC)
- Akaike Information Criterion (AIC)
- Kullback-Leibler Divergence (KL Divergence)
- Reconstruction Loss (MSE)
- Visual Cluster Evaluation using t-SNE projections

---

## Comparison with K-Means Clustering

| Metric               | ResNet18 Autoencoder + GMM | Traditional K-Means |
|---------------------|-----------------------------|---------------------|
| Dimensionality Reduction | Yes (Latent Space) | No |
| Cluster Shape Handling   | Complex, Flexible Clusters | Spherical Clusters Only |
| Evaluation Scores (BIC, AIC) | Lower (Better Fit) | Higher (Poorer Fit) |
| Reconstruction Loss       | Low (Better Feature Retention) | Not Applicable |
| Interpretability          | High (Latent Space Visualization) | Low |
| Generalization to New Data | Robust | Limited |

---

## Technologies Used

- Python
- PyTorch
- Scikit-learn
- Matplotlib
- ResNet18 Autoencoder
- Gaussian Mixture Model (GMM)
- t-SNE for Dimensionality Reduction

---



