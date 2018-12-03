import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from skimage import filters

im = Image.open('/Users/henrypinkard/Desktop/malmo.tif')
img = np.asarray(im)
img = img[:2500, -2500:]

smoothed = filters.gaussian(img, sigma=60).astype(np.float)
plt.figure()
plt.contour(smoothed, origin='image', colors='k')
plt.show()

plt.figure()
plt.hist(np.ravel(img), 100)
