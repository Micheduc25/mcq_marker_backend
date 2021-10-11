# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 12:21:44 2021

@author: Ndjock Michel
"""

import cv2
import imutils
import numpy as np
from .utils import *
from api.models import Quiz, Question, StudentQuestions, Student, Results
import pytesseract
from .scansheet import scanSheet
import os
from rest_framework import exceptions


class MCQCorrector:
    def __init__(
            self,
            sheet_instance: Quiz,
            sheet_questions: [Question],
            session: int,
            image_width=700,
            image_height=900, ):
        self.sheet_instance = sheet_instance
        self.sheet_questions = sheet_questions
        self.image_width = image_width
        self.image_height = image_height
        self.correction_index = 0  # represents the number of sheets which have been corrected
        self.session = session

        self.correspondence_dict = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'i': 0, 'ii': 1, 'iii': 2, 'iv': 3, 'v': 4,
                                    '1': 0, '2': 3, '3': 2, '4': 3, '5': 4}

        '''This function converts the list of correct answers into a map which matches these values to integer values'''

    def set_sheet(self, sheet: Quiz):
        self.sheet_instance = sheet
        self.correction_index = 0

    def get_int_answer_values(self, question: Question):
        return [self.correspondence_dict[val] for val in question.correct_ans]
        # we return an array containing arrays of values e.g [0,1,2]

    def get_answer_label_from_number(self, number):
        choice_label = self.sheet_instance.choiceLabels
        if choice_label == "A-B-C":
            return 'ABCDE'[number]
        elif choice_label == 'i-ii-iii':
            return ['i', 'ii', 'iii', 'iv', 'v'][number]
        else:
            return '12345'[number]

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

        # # we convert the answer choices to numerical values
        # correct_answers = self.get_int_answer_values()
        # # we set questions correct answers
        # if is_two_parts:
        #     answers1 = correct_answers[0:25]
        #     answers2 = correct_answers[25:]
        # else:
        #     answers1 = correct_answers

        # read the image from the given path
        img = cv2.imread(image_path)

        # we scan the image to get only the sheet
        imname = self.sheet_instance.sheet_name + str(self.correction_index)
        scanSheet(img, imname)

        abs_path = os.path.abspath('.')
        if os.path.exists(os.path.join(abs_path, imname + '.jpg')):
            img = cv2.imread(rf"{os.path.join(abs_path, imname + '.jpg')}")
            os.unlink(os.path.join(abs_path, imname + '.jpg'))

        else:
            raise Exception("path to scanned image does not exist!")

        # resize the image
        # img = cv2.resize(img, (self.image_width, self.image_height))

        img_contours = img.copy()
        # image with required contours
        cont_image = img.copy()

        # Image pre-processing ##########################################

        # convert image to grayscale
        # img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # add gaussian blur to grayscale image
        # img_blur = cv2.GaussianBlur(img_gray, (5, 5), 1)

        # edge detection
        img_canny = cv2.Canny(img, 10, 50)

        # ############################################################

        # We find the contours on the image
        contours, hierachy = cv2.findContours(img_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(img_contours, contours, -1, (0, 255, 0), 2)  # draw contours on image

        # We obtain all the rectangular contours and get the largest which represents the largest rectangle on our paper
        rect_con = rectContours(contours)

        # if our sheet has two parts, then the second biggest rectangle is our answers rectangle
        # and the third biggest is the sheet code rectangle

        if is_two_parts:
            biggest_contour = getCornerPoints(rect_con[1])  # left-most big rectangle
            biggest_contour2 = getCornerPoints(rect_con[0])  # right-most big rectangle
            # student_name = getCornerPoints(rect_con[2])
            # registration_number = getCornerPoints(rect_con[3], epsilon=0.034)
            student_code = getCornerPoints(rect_con[2])

        else:
            biggest_contour2 = None
            biggest_contour = getCornerPoints(rect_con[0])  # left-most big rectangle
            # student_name = getCornerPoints(rect_con[1])
            # registration_number = getCornerPoints(rect_con[2])
            student_code = getCornerPoints(rect_con[1])

        # we now show the draw those two biggest contours on our image

        if biggest_contour.size != 0 and student_code.size != 0:

            cv2.drawContours(cont_image, [biggest_contour], -1, (255, 0, 0), 8)
            if biggest_contour2 is not None:
                cv2.drawContours(cont_image, [biggest_contour2], -1, (0, 255, 255), 6)

            cv2.drawContours(cont_image, [student_code], -1, (0, 255, 255), 5)
            # cv2.imshow("Scanned", imutils.resize(cont_image, height=650))
            # cv2.waitKey(0)

            # we reorder the points of the big rectangles and the code and student name rectangles
            biggest_contour = reorder(biggest_contour)
            if biggest_contour2 is not None:
                biggest_contour2 = reorder(biggest_contour2)
            # student_name = reorder(student_name)
            # print("reg number shape:{}".format(registration_number.shape))

            # registration_number = reorder(registration_number)
            student_code = reorder(student_code)

            # we apply a warpPerspective to get a bird's eye view of the specific contours we need
            # we do this by getting the transformation matrix as below

            warp_image_colored = get_warped_image(img, biggest_contour, self.image_width, self.image_height)

            if biggest_contour2 is not None:
                warp_image_colored2 = get_warped_image(img, biggest_contour2, self.image_width, self.image_height)

            # We now apply Threshold to the warped images

            # # for first big rectangle
            # warp_image_gray =cv2.cvtColor(warp_image_colored, cv2.COLOR_BGR2GRAY)
            img_thresh = cv2.threshold(warp_image_colored, 200, 255, cv2.THRESH_BINARY_INV)[1]

            # cv2.imshow("Scanned", imutils.resize(img_thresh, height=650))
            # cv2.waitKey(0)

            # for second big rectangle
            if biggest_contour2 is not None:
                # warp_image_gray2 = cv2.cvtColor(warp_image_colored2, cv2.COLOR_BGR2GRAY)
                img_thresh2 = cv2.threshold(warp_image_colored2, 200, 255, cv2.THRESH_BINARY_INV)[1]

            # we now read student code ##########################################################3
            code_image = get_warped_image(img, student_code, 500, 240)
            # cv2.imshow('code', code_image)
            # cv2.waitKey(0)

            student_code_text = self.image_matrix_to_string(code_image)
            final_code = ''.join([char for char in student_code_text if str.isalnum(char)])
            # ###################################################################################

            # we check if student code corresponds to a student in the database
            try:
                student = Student.objects.get(pk=final_code)
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

                # print(pixel_values)
                # we find the box with the highest pixel value for each row(question) and store its index in an array

                given_answers_indexes1 = []

                # we set the pixel threshold value for correct shaded boxes
                pixel_threshold = 4520  # TODO adjust threshold value later

                # we pass through each row and check for the boxes with pixel values above a certain threshold
                # (1800 in this case)
                for row in pixel_values:
                    current_indexes = []
                    for i in range(0, len(row)):
                        if row[i] >= pixel_threshold:
                            current_indexes.append(i)
                    # given_index = np.where(row == np.amax(row))
                    given_answers_indexes1.append(current_indexes)

                # print("given indexes are ", str(given_answers_indexes1))

                if biggest_contour2 is not None:
                    given_answers_indexes2 = []

                    for row in pixel_values2:
                        current_indexes = []
                        for i in range(0, len(row)):
                            if row[i] >= pixel_threshold:
                                current_indexes.append(i)
                        # given_index = np.where(row == np.amax(row))
                        given_answers_indexes2.append(current_indexes)

                # Now we grade the questions
                # by comparing the givenAnswers indexes and the correct answers indexes defined above
                # we equally assign mark according to mark allocation and mark distribution for each question
                # for failed questions we subtract the fail_mark

                fail_mark = float(self.sheet_instance.failMark)
                result_summary = {}

                grading1 = []

                for i in range(0, body_rows_1):
                    points_percentage = 0.0
                    result_summary[i] = {'correct_choices': [], 'wrong_choices': [], 'percentage_pass': 0.0,
                                         'mark': 0.0}
                    # we evaluate the total % of the points for the given question which has been answered correctly
                    for ans in given_answers_indexes1[i]:

                        if ans in self.get_int_answer_values(self.sheet_questions[i]):
                            corct_ans = self.sheet_questions[i].correct_ans
                            ans_index = corct_ans.index(self.get_answer_label_from_number(ans))
                            points_percentage += float(self.sheet_questions[i].mark_distribution[ans_index])
                            result_summary[i]["correct_choices"].append(self.get_answer_label_from_number(ans))
                        else:
                            points_percentage = 0.0
                            result_summary[i]["wrong_choices"].append(self.get_answer_label_from_number(ans))

                    # if atleast one correct answer is given, we calculate the points obtained by multiplying the fraction
                    # of points obtained by the mark allocated to that question, else we subtract the fail mark from the
                    # final grading
                    final_question_points = 0.0
                    if points_percentage > 0:
                        points_total_percentage = 0.0
                        for pc in self.sheet_questions[i].mark_distribution:
                            points_total_percentage += float(pc)

                        points_frac = points_percentage / points_total_percentage
                        final_question_points = points_frac * self.sheet_questions[i].total_mark
                        result_summary[i]["percentage_pass"] = points_frac * 100

                    else:
                        final_question_points -= fail_mark

                    result_summary[i]["mark"] = final_question_points
                    grading1.append(final_question_points)

                    # after grading the question we store the result for that question in the database
                    question_response = StudentQuestions(student=student, question=self.sheet_questions[i],
                                                         answered_correct=result_summary[i]["correct_choices"],
                                                         answered_wrong=result_summary[i]["wrong_choices"],
                                                         percentage_pass=points_percentage,
                                                         mark=final_question_points,
                                                         session=self.session
                                                         )

                    question_response.save()

                # we repeat the same exercise for the second sheet body
                if biggest_contour2 is not None:
                    grading2 = []

                    for i in range(0, body_rows_2):
                        points_percentage = 0.0
                        # we evaluate the total % of the points for the given question which has been answered correctly
                        for ans in given_answers_indexes2[i]:
                            if ans in self.get_int_answer_values(self.sheet_questions[25 + i]):
                                corct_ans = self.sheet_questions[25 + i].correct_ans
                                ans_index = corct_ans.index(self.get_answer_label_from_number(ans))
                                points_percentage += float(self.sheet_questions[25 + i].mark_distribution[ans_index])
                                result_summary[25 + i]["correct_choices"].append(self.get_answer_label_from_number(ans))
                            else:
                                points_percentage = 0.0
                                result_summary[25 + i]["wrong_choices"].append(self.get_answer_label_from_number(ans))

                        final_question_points = 0.0
                        if points_percentage > 0:
                            points_total_percentage = 0.0
                            for pc in self.sheet_questions[25 + i].mark_distribution:
                                points_total_percentage += float(pc)

                            points_frac = points_percentage / points_total_percentage
                            final_question_points = points_frac * self.sheet_questions[25 + i].total_mark
                            result_summary[25 + i]["percentage_pass"] = points_frac * 100
                        else:
                            final_question_points -= fail_mark

                        result_summary[25 + i]["mark"] = final_question_points

                        grading2.append(final_question_points)

                        # after grading the question we store the result for that question in the database
                        question_response = StudentQuestions(student=student, question=self.sheet_questions[25+i],
                                                             answered_correct=result_summary[25+i]["correct_choices"],
                                                             answered_wrong=result_summary[25+i]["wrong_choices"],
                                                             percentage_pass=points_percentage,
                                                             mark=final_question_points,
                                                             session=self.session)

                        question_response.save()

                # we then find the total score of the student

                if biggest_contour2 is not None:
                    score = sum(grading1) + sum(grading2)

                else:
                    score = np.sum(grading1)

                print('student code:{}'.format(student_code_text))

                print("final score: ", score)
                questions_total = np.sum([q.total_mark for q in self.sheet_questions])

                final_result = Results(sheet=self.sheet_instance, student=student, mark=score, total=questions_total,
                                       session=self.session)
                final_result.save()

                return {
                    'student_code': final_code,
                    'student': student,
                    'session': self.session,
                    'score': score,
                    'total': questions_total,
                    'sheet_name': self.sheet_instance.sheet_name,
                    'summary': result_summary,
                    'sheet_number': self.correction_index
                }

            except Student.DoesNotExist:
                raise exceptions.ValidationError(
                    detail=f"Student with code {final_code} could not be found", code=404
                )

        return 'error'

    @staticmethod
    def image_matrix_to_string(image_matrix):
        custom_config = r'--oem 3 --psm 6'
        # im_rgb = cv2.cvtColor(image_matrix, cv2.COLOR_BGR2RGB)
        return pytesseract.image_to_string(image_matrix, config=custom_config)
