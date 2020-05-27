
from model_of_care import model_of_care
from outcomes_for_moc import outcomes_for_moc
import numpy as np

di_mild = np.array([[[1,1],[1,2],[1,2],[1,1]]])
di_sev = np.array([[[1,2],[1,1],[1,2],[1,2]]])
risk = np.array([[0],[2],[2],[0]])
frac_sev = np.array([[0.1]])
ppe_stop = np.array([[0.6]])

moc = model_of_care('cohort','high','ACT')[0]
print(outcomes_for_moc(moc, di_mild, di_sev, risk, frac_sev, ppe_stop))
