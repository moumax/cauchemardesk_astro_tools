from photutils.detection import DAOStarFinder
from astropy.stats import sigma_clipped_stats
import numpy as np

def detect_stars(data, fwhm=3.0, threshold_sigma=5.0):
    data = np.nan_to_num(data)
    mean, median, std = sigma_clipped_stats(data, sigma=3.0)
    daofind = DAOStarFinder(fwhm=fwhm, threshold=threshold_sigma*std)
    sources = daofind(data - median)
    if sources is not None and len(sources) > 0:
        roundness1 = np.mean(sources['roundness1'])
        roundness2 = np.mean(sources['roundness2'])
        return len(sources), roundness1, roundness2
    else:
        return 0, None, None