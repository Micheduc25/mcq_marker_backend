# import the necessary packages
from .transform import four_point_transform
from skimage.filters import threshold_local
import cv2
import imutils
import os


def scanSheet(image, sheet_name):

	# load the image and compute the ratio of the old height
	# to the new height, clone it, and resize it

	ratio = image.shape[0] / 500.0
	orig = image.copy()
	image = imutils.resize(image, height=500)

	# convert the image to grayscale, blur it, and find edges
	# in the image
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (5, 5), 0)
	edged = cv2.Canny(gray, 20, 90)

	# "STEP 1: Edge Detection"

	# find the contours in the edged image, keeping only the
	# largest ones, and initialize the screen contour
	cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

	# loop over the contours
	for c in cnts:
		# approximate the contour
		peri = cv2.arcLength(c, True)
		approx = cv2.approxPolyDP(c, 0.02 * peri, True)

		# if our approximated contour has four points, then we
		# can assume that we have found our screen
		if len(approx) == 4:
			screenCnt = approx
			break

	# "STEP 2: Find contours of paper"

	cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 2)

	# apply the four point transform to obtain a top-down
	# view of the original image
	warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)

	# convert the warped image to grayscale, then threshold it
	# to give it that 'black and white' paper effect
	warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
	T = threshold_local(warped, 107, offset=4, method="mean")
	warped = (warped > T).astype("uint8") * 255

	abs_path = os.path.abspath('.')
	# we save the image with the sheetname and count
	cv2.imwrite(f"{os.path.join(abs_path, sheet_name + '.jpg')}", warped)

	# print(warped)

	# show the original and scanned images
	# "STEP 3: Apply perspective transform"
	# cv2.imshow("Original", imutils.resize(orig, height=650))
	# cv2.imshow("Scanned", imutils.resize(warped, height=650))
	# cv2.waitKey(0)

	return warped
