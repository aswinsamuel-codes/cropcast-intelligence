# CropCast — Targeted Literature and Source Review

**Date:** 2026-10-23 · **Milestone:** Phase 2 (pre-EDA) · **Status:** Verified references only

Every reference below was checked against its registry record: Crossref by DOI, the JMLR page, or the OTexts book pages. Statements are labelled **[Published]** when they report a source's finding and **[CropCast]** when they are this project's own reasoning or hypothesis.

## 1. Agricultural commodity price forecasting in India

- **[Published]** Madaan et al. (2019) study onion and potato prices in India. They combine mandi wholesale prices and arrivals with retail prices, and pair price forecasting with an anomaly detection system aimed at trader hoarding. Their anomaly windows are the source of the ICTD-IITD label files used in this project (RES-004).
- **[Published]** Paul, Rana and Saxena (2016) model monthly wholesale onion prices in Delhi markets. ARIMA residuals showed remaining autocorrelation and conditional heteroscedasticity, which led them to (E)GARCH models.
- **[Published]** Shankar et al. (2023) analyse the volatility of onion arrivals and prices with advanced time-series techniques. They report that decomposition-based hybrids outperformed single models on their markets.
- **[CropCast]** These studies are usually monthly or mandi-level. Daily state-aggregate data (this project) has not been benchmarked in them. Published accuracy numbers are therefore **not comparable** to ours, and we make no cross-study accuracy claims.

## 2. Forecasting methods and baselines

- **[Published]** Hyndman and Athanasopoulos (2021, §5.2) present the mean, naïve, seasonal naïve and drift methods as benchmarks that any proposed method should beat.
- **[Published]** Large empirical competitions show that simple and statistical methods are hard to beat. In M4, pure ML methods generally did not outperform statistical benchmarks, while combinations and hybrids did best (Makridakis et al., 2020).
- **[Published]** ARIMA identification relies on unit-root and stationarity testing: ADF (Dickey & Fuller, 1979) and KPSS (Kwiatkowski et al., 1992). Residual adequacy is assessed with the Ljung–Box test (Ljung & Box, 1978).
- **[Published]** Exponential smoothing has a state-space formulation that allows automatic model selection (Hyndman et al., 2002).
- **[Published]** Random forests are ensembles of decision trees grown on bootstrap samples with random feature subsets (Breiman, 2001). Implementations: scikit-learn (Pedregosa et al., 2011) and statsmodels (Seabold & Perktold, 2010).
- **[CropCast]** For one-day-ahead daily prices with strong persistence, the naive forecast is expected to be very competitive. A defensible result may be that no model beats it materially. The protocol is designed to detect that honestly.

## 3. Evaluation under chronological splits

- **[Published]** Out-of-sample evaluation should keep the time order. A rolling forecasting origin, where each forecast uses only earlier observations, is recommended (Tashman, 2000; Hyndman & Athanasopoulos, 2021, §5.10).
- **[Published]** Bergmeir and Benítez (2012) review cross-validation for time-series predictors and the risks of ignoring temporal dependence.
- **[Published]** Scale-dependent errors (MAE, RMSE) cannot be compared across series. MAPE is undefined or unstable near zero, and Hyndman and Koehler (2006) propose the scaled error MASE as a scale-free alternative.
- **[Published]** The Diebold–Mariano test compares forecast accuracy under serially correlated loss differentials (Diebold & Mariano, 1995). The Harvey–Leybourne–Newbold small-sample correction improves its size (Harvey et al., 1997).
- **[Published]** When many hypotheses are tested, the false discovery rate can be controlled with the Benjamini–Hochberg procedure (Benjamini & Hochberg, 1995).

## 4. Anomaly detection and robust statistics

- **[Published]** Chandola et al. (2009) categorise anomaly types (point, contextual, collective) and detection approaches. They stress that the anomaly definition must match the domain.
- **[Published]** The median and the median absolute deviation (MAD) are robust to the outliers being detected, whereas mean ± k·SD rules are distorted by them (Leys et al., 2013; Rousseeuw & Croux, 1993).
- **[CropCast]** With only one state-level series per commodity, "market-relative" is operationalised as relative to the market's own recent behaviour and to its one-step forecast. Peer-market divergence (Req 6.3) cannot be computed (DEC-017).
- **[CropCast]** The ICTD-IITD labels are rule-based flags derived from the same Agmarknet source, at mandi level and over multi-week windows. They are **weak, non-independent references**, not ground truth. Agreement with them is reported descriptively and not as detection accuracy.

## 5. Source documentation (CEDA)

- CEDA's republishing guidelines (`https://ceda.ashoka.edu.in/republish-policy/`, accessed 2026-10-23):
  - Data visualisations may be reproduced with the credit "Centre for Economic Data and Analysis (CEDA), Ashoka University".
  - Use is non-commercial.
  - No logo requirement is stated.
  - The page links a CC BY-ND 4.0 licence while also saying data may be "adapted", so terms for redistributing derived data are ambiguous. **[CropCast]** We therefore commit figures and aggregate statistics, but neither the raw nor the processed data.
- CEDA's Agri Market methodology README (`https://agmarknet.ceda.ashoka.edu.in/README.html`, linked from CEDA's site) returned HTTP 404 on 2026-10-23, and the API documentation page renders no methodology text. **The state-level aggregation method is therefore undocumented for this project**, and ISS-002 cannot be resolved from source documentation.

## References

- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300. https://doi.org/10.1111/j.2517-6161.1995.tb02031.x
- Bergmeir, C., & Benítez, J. M. (2012). On the use of cross-validation for time series predictor evaluation. *Information Sciences*, 191, 192–213. https://doi.org/10.1016/j.ins.2011.12.028
- Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5–32. https://doi.org/10.1023/A:1010933404324
- Chandola, V., Banerjee, A., & Kumar, V. (2009). Anomaly detection: A survey. *ACM Computing Surveys*, 41(3), 1–58. https://doi.org/10.1145/1541880.1541882
- Dickey, D. A., & Fuller, W. A. (1979). Distribution of the estimators for autoregressive time series with a unit root. *Journal of the American Statistical Association*, 74(366a), 427–431. https://doi.org/10.1080/01621459.1979.10482531
- Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics*, 13(3), 253–263. https://doi.org/10.1080/07350015.1995.10524599
- Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction mean squared errors. *International Journal of Forecasting*, 13(2), 281–291. https://doi.org/10.1016/S0169-2070(96)00719-4
- Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and practice* (3rd ed.). OTexts. https://otexts.com/fpp3/
- Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting*, 22(4), 679–688. https://doi.org/10.1016/j.ijforecast.2006.03.001
- Hyndman, R. J., Koehler, A. B., Snyder, R. D., & Grose, S. (2002). A state space framework for automatic forecasting using exponential smoothing methods. *International Journal of Forecasting*, 18(3), 439–454. https://doi.org/10.1016/S0169-2070(01)00110-8
- Kwiatkowski, D., Phillips, P. C. B., Schmidt, P., & Shin, Y. (1992). Testing the null hypothesis of stationarity against the alternative of a unit root. *Journal of Econometrics*, 54(1–3), 159–178. https://doi.org/10.1016/0304-4076(92)90104-Y
- Leys, C., Ley, C., Klein, O., Bernard, P., & Licata, L. (2013). Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median. *Journal of Experimental Social Psychology*, 49(4), 764–766. https://doi.org/10.1016/j.jesp.2013.03.013
- Ljung, G. M., & Box, G. E. P. (1978). On a measure of lack of fit in time series models. *Biometrika*, 65(2), 297–303. https://doi.org/10.1093/biomet/65.2.297
- Madaan, L., Sharma, A., Khandelwal, P., Goel, S., Singla, P., & Seth, A. (2019). Price forecasting & anomaly detection for agricultural commodities in India. In *Proceedings of the 2nd ACM SIGCAS Conference on Computing and Sustainable Societies (COMPASS '19)* (pp. 52–64). https://doi.org/10.1145/3314344.3332488
- Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2020). The M4 Competition: 100,000 time series and 61 forecasting methods. *International Journal of Forecasting*, 36(1), 54–74. https://doi.org/10.1016/j.ijforecast.2019.04.014
- Paul, R. K., Rana, S., & Saxena, R. (2016). Effectiveness of price forecasting techniques for capturing asymmetric volatility for onion in selected markets of Delhi. *The Indian Journal of Agricultural Sciences*, 86(3), 303–309. https://doi.org/10.56093/ijas.v86i3.56843
- Pedregosa, F., Varoquaux, G., Gramfort, A., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html
- Rousseeuw, P. J., & Croux, C. (1993). Alternatives to the median absolute deviation. *Journal of the American Statistical Association*, 88(424), 1273–1283. https://doi.org/10.1080/01621459.1993.10476408
- Seabold, S., & Perktold, J. (2010). Statsmodels: Econometric and statistical modeling with Python. In *Proceedings of the 9th Python in Science Conference* (pp. 92–96). https://doi.org/10.25080/Majora-92bf1922-011
- Shankar, S. V., Chandel, A., Gupta, R. K., Sharma, S., Chand, H., Kumar, R., Mishra, N., & Ananthakrishnan, S. (2023). Exploring the dynamics of arrivals and prices volatility in onion (*Allium cepa*) using advanced time series techniques. *Frontiers in Sustainable Food Systems*, 7, 1208898. https://doi.org/10.3389/fsufs.2023.1208898
- Tashman, L. J. (2000). Out-of-sample tests of forecasting accuracy: An analysis and review. *International Journal of Forecasting*, 16(4), 437–450. https://doi.org/10.1016/S0169-2070(00)00065-0
