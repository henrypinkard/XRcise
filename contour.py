import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from skimage import filters

im = Image.open('/Users/henrypinkard/Desktop/malmocrop.tif')
img = np.asarray(im)
smoothed = img

smoothed = filters.gaussian(img, sigma=40).astype(np.float)
plt.figure()
plt.contour(smoothed, origin='image', levels=30)
plt.show()

plt.figure()
plt.hist(np.ravel(img), 100)
pass