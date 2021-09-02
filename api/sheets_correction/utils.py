# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 17:49:02 2021

@author: Ndjock Michel
"""
import cv2
import numpy as np

# returns all corner points of a contour
def getCornerPoints(cont, epsilon=0.02):
    peri = cv2.arcLength(cont, True)  # second param determines if we find only for closed contours
    approx = cv2.approxPolyDP(cont, epsilon*peri, True)  # finds the number of corner points in for each contour
    return approx


# returns all rectangular contours in a list of contours

def rectContours(contours):
    rectCon = []  # list which will store all rectangular contours
    for ct in contours:
        area = cv2.contourArea(ct)
        # print(area)
        
        if area > 50:
            approx = getCornerPoints(ct)
            # print("Corner points", len(approx))
            
            # if our contour has four corner points we add it to the rectangles list
            if len(approx == 4):
                rectCon.append(ct)
    
    # we now sort the rectangles list so that the contour with the biggest area is at the start of the list
    rectCon = sorted(rectCon, key=cv2.contourArea, reverse=True)
    
    return rectCon


# reorder function reorders the points of the contours from smallest to biggest.
# point closer to origin(0,0) is first point, and point further from origin is last point.

def reorder(points):
    # we reshape our points so as to get a 4 by 2 array i.e 4 points with two co-ordinates each
    points = points.reshape((4, 2))

    # we create a new array in which we will put the reordered points
    pointsNew = np.zeros((4, 1, 2), np.int32)
    pointsSum = points.sum(1)
    pointsDiff = np.diff(points, axis=1)

    # first point is point with smallest sum of co-ordinates
    # last point is point with biggest sum of co-ordinates
    pointsNew[0] = points[np.argmin(pointsSum)]  # [0,0]
    pointsNew[3] = points[np.argmax(pointsSum)]  # [w,h]

    # second point is point with smallest difference of co-ordinates
    # third point is point with biggest difference of co-ordinates
    pointsNew[1] = points[np.argmin(pointsDiff)]  # [w,0]
    pointsNew[2] = points[np.argmax(pointsDiff)]  # [0, h]

    # print("big rectangle points are {}".format(points))
    # print("ordered points are {}".format(pointsNew))

    return pointsNew


# function splits the sheet body into individual boxes which contain a bubble each

def splitBoxes(img, rows=5, cols=5):
    imrows = np.vsplit(img, rows)  # split the image into a given number of rows
    boxes = []

    for row in imrows:
        imcols = np.hsplit(row, cols)  # split each row into individual columns (cells)

        for box in imcols:
            boxes.append(box)  # send each box to our boxes array

    # cv2.imshow("first row", imrows[1])

    return boxes


def showAnswers(img, markedIndexes, grading, answers, bodyRows, bodyCols):
    sectionWidth = int(img.shape[1]/bodyRows)
    sectionHeight = int(img.shape[0]/bodyCols)
    radius = 30

    for i in range(0, bodyRows):
        givenAns = markedIndexes[i]
        # we get the center of the marked answer so that we can draw a circle around it
        cX = (givenAns*sectionWidth) + sectionWidth//2
        cY = (i*sectionHeight) + sectionHeight//2

        # if answer is correct we draw green circle else we draw red circle

        if grading[i] == 1:
            cv2.circle(img, (cX, cY), radius, (0, 255, 0), cv2.FILLED)
        else:
            cv2.circle(img, (cX, cY), radius, (0, 0, 255), cv2.FILLED)

            ccX = (answers[i] * sectionWidth) + sectionWidth // 2
            cv2.circle(img, (ccX, cY), radius-30, (0, 255, 0), cv2.FILLED)

    return img


def get_warped_image(image, contour, width, height):
    pt1 = np.float32(contour)
    pt2 = np.float32(
            [
                [0, 0], [width, 0],
                [0, height],
                [width, height]
            ]
                        )

    warp_matrix = cv2.getPerspectiveTransform(pt1, pt2)
    warp_image = cv2.warpPerspective(image, warp_matrix, (width, height))

    return warp_image
