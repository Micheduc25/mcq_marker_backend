# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 12:21:44 2021

@author: Ndjock Michel
"""

import cv2
import numpy as np
from .utils import *
from api.models import Quiz
import pytesseract


class MCQCorrector:
    def __init__(
            self,
            sheet_instance: Quiz,
            image_width=700,
            image_height=900, ):
        self.sheet_instance = sheet_instance
        self.image_width = image_width
        self.image_height = image_height
        self.correction_index = 0  # represents the number of sheets which have been corrected

    '''This function converts the list of correct answers into another list which maps these values to integer values'''
    def get_int_answer_values(self):
        correspondence_dict = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'i': 0, 'ii': 1, 'iii': 2, 'iv': 3, 'v': 4,
                               '1': 0, '2': 3, '3': 2, '4': 3, '5': 4}
        int_answer_values = []
        correct_answers = self.sheet_instance.correctAnswers

        for ans in correct_answers:
            int_answer_values.append(correspondence_dict[ans])

        return int_answer_values

    def correct_sheet(self, image_path):

        self.correction_index += 1

        # we determine if the sheet has two parts according to the number of questions
        questions = int(self.sheet_instance.questions)

        if (questions - 25) > 0:
            is_two_parts = True
        else:
            is_two_parts = False

        # we determine the number of rows and columns in each part of the sheet body
        if questions <= 25:
            body_rows_1 = questions
        else:
            body_rows_1 = 25
            body_rows_2 = questions - 25

        num_choices = int(self.sheet_instance.choices)
        body_cols_1 = num_choices
        body_cols_2 = num_choices

        # we convert the answer choices to numerical values
        correct_answers = self.get_int_answer_values()
        # we set questions correct answers
        if is_two_parts:
            answers1 = correct_answers[0:25]
            answers2 = correct_answers[25:]
        else:
            answers1 = correct_answers

        # read the image from the computer

        img = cv2.imread(image_path)
        # resize the image
        img = cv2.resize(img, (self.image_width, self.image_height))

        img_contours = img.copy()
        # image with required contours
        cont_image = img.copy()

        # Image pre-processing ##########################################

        # convert image to grayscale
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # add gaussian blur to grayscale image
        img_blur = cv2.GaussianBlur(img_gray, (5, 5), 1)

        # edge detection
        img_canny = cv2.Canny(img_blur, 10, 50)

        # ############################################################

        # We find the contours on the image
        contours, hierachy = cv2.findContours(img_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(img_contours, contours, -1, (0, 255, 0), 2)  # draw contours on image

        # We obtain all the rectangular contours and get the largest which represents the largest rectangle on our paper
        rect_con = rectContours(contours)


        # if our sheet has two parts, then the second biggest rectangle is our answers rectangle
        # and the third biggest is the student name rectangle
        # the 4th and 5th are the registration number and student code rectangles
        if is_two_parts:
            biggest_contour = getCornerPoints(rect_con[1])  # left-most big rectangle
            biggest_contour2 = getCornerPoints(rect_con[0])  # right-most big rectangle
            student_name = getCornerPoints(rect_con[2])
            registration_number = getCornerPoints(rect_con[3], epsilon=0.034)
            student_code = getCornerPoints(rect_con[4])

        else:
            biggest_contour2 = None
            biggest_contour = getCornerPoints(rect_con[0])  # left-most big rectangle
            student_name = getCornerPoints(rect_con[1])
            registration_number = getCornerPoints(rect_con[2])
            student_code = getCornerPoints(rect_con[3])

        # we now show the draw those two biggest contours on our image

        if biggest_contour.size != 0 and student_name.size != 0 and\
                registration_number.size != 0 and student_code.size != 0:

            cv2.drawContours(cont_image, [biggest_contour], -1, (255, 0, 0), 8)
            if biggest_contour2 is not None:
                cv2.drawContours(cont_image, [biggest_contour2], -1, (0, 255, 255), 6)

            cv2.drawContours(cont_image, [student_name, registration_number, student_code], -1, (0, 255, 255), 5)

            # we reorder the points of the big rectangles and the code and student name rectangles
            biggest_contour = reorder(biggest_contour)
            if biggest_contour2 is not None:
                biggest_contour2 = reorder(biggest_contour2)
            student_name = reorder(student_name)
            # print("reg number shape:{}".format(registration_number.shape))

            registration_number = reorder(registration_number)
            student_code = reorder(student_code)

            # we apply a warpPerspective to get a bird's eye view of the specific contours we need
            # we do this by getting the transformation matrix as below

            warp_image_colored = get_warped_image(img, biggest_contour, self.image_width, self.image_height)

            if biggest_contour2 is not None:
                warp_image_colored2 = get_warped_image(img, biggest_contour2, self.image_width, self.image_height)

            # We now apply Threshold to the warped images

            # # for first big rectangle
            warp_image_gray = cv2.cvtColor(warp_image_colored, cv2.COLOR_BGR2GRAY)
            img_thresh = cv2.threshold(warp_image_gray, 180, 255, cv2.THRESH_BINARY_INV)[1]

            # for second big rectangle
            if biggest_contour2 is not None:
                warp_image_gray2 = cv2.cvtColor(warp_image_colored2, cv2.COLOR_BGR2GRAY)
                img_thresh2 = cv2.threshold(warp_image_gray2, 180, 255, cv2.THRESH_BINARY_INV)[1]

            # we split the two biggest rectangles into individual bubbles
            boxes1 = splitBoxes(img_thresh, rows=body_rows_1, cols=body_cols_1)

            if biggest_contour2 is not None:
                boxes2 = splitBoxes(img_thresh2, rows=body_rows_2, cols=body_cols_2)

            # we then count non-zero pixels for each bubble and arrange the bubbles in a 2-dimensional array
            # each sub array corresponds to one row of the answer sheet body

            pixel_values = np.zeros((body_rows_1, body_cols_1), np.int32)
            if biggest_contour2 is not None:
                pixel_values2 = np.zeros((body_rows_2, body_cols_2), np.int32)

            count_c = 0
            count_r = 0

            for box in boxes1:
                pixel_values[count_r][count_c] = np.count_nonzero(box)
                count_c += 1
                if count_c == body_cols_1:
                    count_r += 1
                    count_c = 0

            count_c = 0
            count_r = 0

            if biggest_contour2 is not None:
                for box in boxes2:
                    pixel_values2[count_r][count_c] = np.count_nonzero(box)
                    count_c += 1
                    if count_c == body_cols_2:
                        count_r += 1
                        count_c = 0

            # we find the box with the highest pixel value for each row(question) and store its index in an array

            given_answers_indexes1 = []

            for row in pixel_values:
                given_index = np.where(row == np.amax(row))
                given_answers_indexes1.append(given_index[0][0])

            if biggest_contour2 is not None:
                given_answers_indexes2 = []

                for row in pixel_values2:
                    given_index = np.where(row == np.amax(row))
                    given_answers_indexes2.append(given_index[0][0])

            # Now we grade the questions
            # by comparing the givenAnswers indexes and the correct answers indexes defined above
            # we equally assign mark according to mark allocation each question

            mark_allocation = [int(mk) for mk in self.sheet_instance.marksAllocation]
            result_summary = {}

            grading1 = []

            for i in range(0, body_rows_1):
                if answers1[i] == given_answers_indexes1[i]:
                    grading1.append(mark_allocation[i]*1)
                    result_summary[str(i + 1)] = mark_allocation[i] * 1

                else:
                    grading1.append(0)
                    result_summary[str(i + 1)] = 0

            if biggest_contour2 is not None:
                grading2 = []

                for i in range(0, body_rows_2):
                    if answers2[i] == given_answers_indexes2[i]:
                        grading2.append(mark_allocation[25+i]*1)
                        result_summary[str(i+1+25)] = mark_allocation[25+i]*1
                    else:
                        grading2.append(0)
                        result_summary[str(i+1+25)] = 0
            # we then find the score of the student

            if biggest_contour2 is not None:
                score = sum(grading1) + sum(grading2)

            else:
                score = np.sum(grading1)

            # we now read student name , registration number and code
            student_name_image = get_warped_image(img, student_name, 600, 100)
            reg_number_image = get_warped_image(img, registration_number, 600, 100)
            code_image = get_warped_image(img, student_code, 300, 100)

            student_name_text = self.image_matrix_to_string(student_name_image)
            reg_number_text = self.image_matrix_to_string(reg_number_image)
            code_image = self.image_matrix_to_string(code_image)
            print('student name:{}'.format(reg_number_text))

            print("final score: ", score)
            # cv2.imshow('contours', cont_image)
            # cv2.waitKey(0)

            return {
                'student_name': student_name_text,
                'registration_number': reg_number_text,
                'student_code': code_image,
                'score': score,
                'summary': result_summary,
                'sheet_number': self.correction_index
            }

        return 'error'

    @staticmethod
    def image_matrix_to_string(image_matrix):
        im_rgb = cv2.cvtColor(image_matrix, cv2.COLOR_BGR2RGB)
        return pytesseract.image_to_string(im_rgb)
