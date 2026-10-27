import numpy as np
OLD = [0.0, 0.4, 4.4, 5.0, 11.2, 14.1, 18.6, 21.3, 25.8, 33.3, 39.2, 43.0, 47.0, 49.8]
NEW = [0.0, 0.3, 4.59, 5.53, 10.21, 13.17, 18.20, 20.67, 25.48, 32.18, 36.38, 40.20, 45.47, 47.95]
NEWDUR = 47.95
def fw(t): return float(np.interp(t, OLD, NEW))
def bw(t): return float(np.interp(t, NEW, OLD))
