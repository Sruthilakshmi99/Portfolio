# Cloud API for Risk and Profitability Analysis in Trading Strategies  
(Multicloud Implementation - GAE + AWS Lambda + AWS EC2)

---

## Project Overview

This project implements a Cloud-Native API system for performing risk analysis and profitability checks of trading strategies based on financial data.

The API detects trading signals (like Three White Soldiers & Three Black Crows) from stock price history and runs Monte Carlo simulations to calculate the Value at Risk (VaR) and potential Profit/Loss.

The architecture dynamically allocates computational resources between AWS Lambda and AWS EC2 based on user input while Google App Engine (GAE) serves as the API frontend handling all user interactions and displaying final results.

---

## Input Composition (User Parameters for Analysis)

Users need to provide the following inputs to the `/analyse` endpoint:

| Parameter | Meaning | Example Value |
|-----------|---------|----------------|
| h         | Length of price history to calculate mean and standard deviation | 101 |
| d         | Number of Monte Carlo shots (data points to generate per signal) | 10000 |
| t         | Type of signal to analyze - `buy` or `sell` | buy / sell |
| p         | Days after signal to check Profit or Loss | 7 |

---


GAE makes the decision to route computation either to Lambda or EC2 based on user-specified scale parameters (r - number of parallel executions).

---
