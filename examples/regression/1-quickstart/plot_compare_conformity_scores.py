"""
===========================================================
Estimating prediction intervals of Gamma distributed target
===========================================================
This example uses :class:`mapie.regression.MapieRegressor` to estimate
prediction intervals associated with Gamma distributed target.
The limit of the absolute residual conformity score is illustrated.

We use here the OpenML house_prices dataset:
https://www.openml.org/search?type=data&sort=runs&id=42165&status=active.

The data is modelled by a Random Forest model
:class:`sklearn.ensemble.RandomForestRegressor` with a fix parameter set.
The confidence intervals are determined by means of the MAPIE regressor
:class:`mapie.regression.MapieRegressor` considering two conformity scores:
:class:`mapie.conformity_scores.AbsoluteConformityScore` which
considers the absolute residuals as the conformity scores and
:class:`mapie.conformity_scores.GammaConformityScore` which
considers the residuals divided by the predicted means as conformity scores.
We consider the standard CV+ resampling method.

We would like to emphasize one main limitation with this example.
With the default conformity score, the confidence intervals
are approximately equal over the range of house prices which may
be inapporpriate when the price range is wide. The Gamma conformity score
overcomes this issue by considering confidence intervals with width
proportional to the predicted mean. For low prices, the Gamma confidence
intervals are narrower than the default ones, conversely to high prices
for which the conficence intervals are higher but visually more relevant.
The empirical coverage is similar between the two conformity scores.
"""
import matplotlib.pyplot as plt
import numpy as np

from sklearn.datasets import fetch_openml
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from mapie.conformity_scores import GammaConformityScore
from mapie.metrics import regression_coverage_score
from mapie.regression import MapieRegressor

np.random.seed(0)

# Parameters
features = [
    "MSSubClass",
    "LotArea",
    "OverallQual",
    "OverallCond",
    "GarageArea",
]
alpha = 0.05
rf_kwargs = {"n_estimators": 10, "random_state": 0}

##############################################################################
# 1. Load dataset with a target following approximativeley a Gamma distribution
# --------------------------------------------------------------------------
#
# We start by loading a dataset with a target following approximately
# a Gamma distribution. The GammaConformityScore is relevant in such cases.
# Two sub dataset are extracted: the training and test ones.

X, y = fetch_openml(name="house_prices", return_X_y=True)

X_train, X_test, y_train, y_test = train_test_split(
    X[features], y, test_size=0.2
)

##############################################################################
# 2. Train model with two conformity scores
# --------------------------------------------------------------------------
#
# Two models are trained with two different conformity score:
# - AbsoluteConformityScore (default conformity score) relevant for target
#   positive as well as negative. The confidence interval widths are in this
#   case approximately the same over the range of prediction.
# - GammaConformityScore relevant for target following roughly a Gamma
#   distribution. The confidence interval widths scale with the predicted
#   value.

# Train model with AbsoluteConformityScore
mapie = MapieRegressor(RandomForestRegressor(**rf_kwargs))
mapie.fit(X_train, y_train)
y_pred_absconfscore, y_pis_absconfscore = mapie.predict(X_test, alpha=[alpha])
yerr_absconfscore = np.concatenate(
    [
        np.expand_dims(y_pred_absconfscore, 0) - y_pis_absconfscore[:, 0, 0].T,
        y_pis_absconfscore[:, 1, 0].T - np.expand_dims(y_pred_absconfscore, 0),
    ],
    axis=0,
)
conf_int_width_absconfscore = (
    y_pis_absconfscore[:, 1, 0] - y_pis_absconfscore[:, 0, 0]
)
coverage_absconfscore = regression_coverage_score(
    y_test, y_pis_absconfscore[:, 0, 0], y_pis_absconfscore[:, 1, 0]
)

# Train model with GammaConformityScore
mapie = MapieRegressor(
    RandomForestRegressor(**rf_kwargs), conformity_score=GammaConformityScore()
)
mapie.fit(X_train, y_train)
y_pred_gammaconfscore, y_pis_gammaconfscore = mapie.predict(
    X_test, alpha=[alpha]
)
yerr_gammaconfscore = np.concatenate(
    [
        np.expand_dims(y_pred_gammaconfscore, 0)
        - y_pis_gammaconfscore[:, 0, 0].T,
        y_pis_gammaconfscore[:, 1, 0].T
        - np.expand_dims(y_pred_gammaconfscore, 0),
    ],
    axis=0,
)
conf_int_width_gammaconfscore = (
    y_pis_gammaconfscore[:, 1, 0] - y_pis_gammaconfscore[:, 0, 0]
)
coverage_gammaconfscore = regression_coverage_score(
    y_test, y_pis_gammaconfscore[:, 0, 0], y_pis_gammaconfscore[:, 1, 0]
)

##############################################################################
# 3. Compare the confidence intervals
# --------------------------------------------------------------------------
#
# Once the models have been trained, we now compare the confidence intervals
# obtained from the two conformity scores. We can see that the
# AbsoluteConformityScore generates confidence interval with almost the same
# width for all the predicted values. Converly, the GammaConformityScore
# yields confidence interval with width scaling with the predicted values.
#
# The choice of the conformity score depends on the problem we face.

fig, axs = plt.subplots(2, 2, figsize=(16, 16))

axs[0, 0].errorbar(
    y_test,
    y_pred_absconfscore,
    yerr=yerr_absconfscore,
    alpha=0.5,
    linestyle="None",
)
axs[0, 0].scatter(y_test, y_pred_absconfscore, s=1, color="black")
axs[0, 0].plot(
    [0, max(max(y_test), max(y_pred_absconfscore))],
    [0, max(max(y_test), max(y_pred_absconfscore))],
    "-r",
)
axs[0, 0].set_xlabel("actual price [$]")
axs[0, 0].set_ylabel("pred price [$]")
axs[0, 0].grid()
axs[0, 0].set_title(
    f"AbsoluteResidualScore - coverage={coverage_absconfscore:.0%}"
)

axs[0, 1].errorbar(
    y_test,
    y_pred_gammaconfscore,
    yerr=yerr_gammaconfscore,
    alpha=0.5,
    linestyle="None",
)
axs[0, 1].scatter(y_test, y_pred_gammaconfscore, s=1, color="black")
axs[0, 1].plot(
    [0, max(max(y_test), max(y_pred_gammaconfscore))],
    [0, max(max(y_test), max(y_pred_gammaconfscore))],
    "-r",
)
axs[0, 1].set_xlabel("actual price [$]")
axs[0, 1].set_ylabel("pred price [$]")
axs[0, 1].grid()
axs[0, 1].set_title(
    f"GammaResidualScore - coverage={coverage_gammaconfscore:.0%}"
)
fig.suptitle(
    f"Predicted values with the confidence intervals of level {alpha}"
)

xmin, xmax = axs[0, 0].get_xlim()
ymin, ymax = axs[0, 0].get_ylim()
axs[1, 0].scatter(y_test, conf_int_width_absconfscore, marker="+")
axs[1, 0].set_xlabel("actual price [$]")
axs[1, 0].set_ylabel("confidence interval width [$]")
axs[1, 0].grid()
axs[1, 0].set_xlim([xmin, xmax])
axs[1, 0].set_ylim([ymin, ymax])

axs[1, 1].scatter(y_test, conf_int_width_gammaconfscore, marker="+")
axs[1, 1].set_xlabel("actual price [$]")
axs[1, 1].set_ylabel("confidence interval width [$]")
axs[1, 1].grid()
axs[1, 1].set_xlim([xmin, xmax])
axs[1, 1].set_ylim([ymin, ymax])

plt.show()
