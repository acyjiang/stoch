# -*- coding: utf-8 -*-
"""
Created on Tue Jan 11 13:53:47 2022

@author: hcohe
"""

import numpy as np
import pandas as pd
import copy
import time
import sys
import threading


sys.path.insert(0, "C:\\Users\\hcohe\\Desktop\\codes\\SurveyProp-ver3")
from SurveyProp_classes import *

global_lock_f1 = threading.Lock()


T = 20  # number of rounds
res_dict = {}
res_per_itration_dict = {}

class_type = randomKSAT


def calc_hamming(vec1, vec2):
    ham_dist = 0

    for i in range(len(vec1)):
        if vec1[i] != vec2[i]:
            ham_dist = ham_dist + 1
    return ham_dist


def absentLiteralCounter(lit_dict):
    counter = 0
    for key in lit_dict:
        if lit_dict[key] == 0:
            counter += 1
    return counter


def SAT_test(n, c, test_it, algorithm, class_type):

    global T
    max_iters = 1000
    k = 3  # number of literals per clause
    m = int(np.ceil(n * c))

    res_arr = np.zeros(11)
    res_arr_per_iteration = np.zeros(11)

    for i in range(T // 10):
        print(
            "------n={}--c={}---test segment# {}---itertation# {}---\n".format(
                n, c, test_it, i
            )
        )
        prop = class_type(n, m, k, max_iters)

        start = time.process_time()

        if algorithm == "WP":
            prop.warning_id()
            # res_arr += test_results(prop,start)
        elif algorithm == "BP":
            prop.belief_prop()
            # res_arr += test_results(prop,start)
        elif algorithm == "SP":
            prop.surveyID()
            # res_arr += test_results(prop,start)

        res_arr_per_iteration = test_results(prop, start)
        res_arr += res_arr_per_iteration  # test_results(prop,start)
        accumulate_results_per_iteration(n, c, res_arr_per_iteration, algorithm)
        del prop
        prop = None

    print(
        "------test segment# {} for n={} and c={} for algorithm {} has ended------".format(
            test_it, n, c, algorithm
        )
    )
    return res_arr


def test_results(prop, start):
    SAT_counter = 0
    runtime = 0
    hamming_distnace = 0
    dont_care_conter = 0
    iteration_counter = 0
    num_of_SAT_clauses = 0

    absent_literals = 0
    majorityVote_sat_counter = 0
    majorityVote_hamming_distnace = 0
    majorityVote_num_of_SAT_clauses = 0

    WP_contradiction_counter = 0

    lit_dict, result_val = prop.validateFinalAssignmemt()
    # count number of dont cares
    for key in lit_dict:
        if lit_dict[key] == "Don't Care" and (
            prop.majority_vote_dictionary[key] != 0
            or prop.majority_vote_dictionary[-key] != 0
        ):
            dont_care_conter = dont_care_conter + 1
    # assign dont cares with random values and check the validity of the literals assignmnet again
    for i in range(len(prop.assignment)):
        if prop.assignment.astype(int)[i] == 0:
            prop.assignment.astype(int)[i] = np.random.choice([-1, 1], 1, p=[0.5, 0.5])[
                0
            ]
    lit_dict, result_val = prop.validateFinalAssignmemt()

    print(result_val)
    # calculate run time
    runtime = runtime + (time.process_time() - start)

    if prop.SAT_validation == True:
        SAT_counter += 1

    hamming_distnace += calc_hamming(
        prop.literal_assignment.astype(int), prop.assignment.astype(int)
    )
    iteration_counter += prop.iteration_counter
    num_of_SAT_clauses += prop.num_of_SAT_clauses

    absent_literals += absentLiteralCounter(prop.majority_vote_dictionary)
    if prop.SAT_validation_majority == True:
        majorityVote_sat_counter += 1
    majorityVote_num_of_SAT_clauses += prop.num_of_SAT_clauses_majority
    majorityVote_hamming_distnace += calc_hamming(
        prop.literal_assignment, prop.majority_vote_result.astype(int)
    )
    print(prop.literal_assignment)

    WP_contradiction_counter = prop.wp_contradiction_counter

    return np.array(
        [
            SAT_counter,
            num_of_SAT_clauses,
            hamming_distnace,
            runtime,
            dont_care_conter,
            iteration_counter,
            absent_literals,
            majorityVote_sat_counter,
            majorityVote_num_of_SAT_clauses,
            majorityVote_hamming_distnace,
            WP_contradiction_counter,
        ]
    )


def test_flow(n, c, test_it, algorithm):
    # res_arr = []
    res_arr = SAT_test(n, c, test_it, algorithm, class_type)  # randomKSAT
    accumulate_results(n, c, res_arr, algorithm)


def accumulate_results(n, c, res_arr, algorithm):
    global res_dict

    key = (n, c, algorithm)

    while global_lock_f1.locked():
        continue
    global_lock_f1.acquire()

    if key in res_dict:
        res_dict[key] += res_arr
    elif key not in res_dict:
        res_dict[key] = res_arr

    global_lock_f1.release()


def accumulate_results_per_iteration(n, c, res_arr, algorithm):

    global res_per_itration_dict

    key = (n, c, algorithm)

    while global_lock_f1.locked():
        continue
    global_lock_f1.acquire()

    if key in res_per_itration_dict:
        res_per_itration_dict[key].append(res_arr)
    elif key not in res_per_itration_dict:
        res_per_itration_dict[key] = []
        res_per_itration_dict[key].append(res_arr)

    global_lock_f1.release()


def parse_results(class_type):
    global res_dict
    global res_per_itration_dict
    global T

    df = pd.DataFrame(
        columns=[
            "N and C",
            "SAT Percentage",
            "Average Percentage of SAT Clauses",
            "Average Percent Hamming distance",
            "Average Runtime",
            "Average Percent Dont Care",
            "Average Number of Iterations",
            "Average number of absent literals",
            "SAT Percentage (MV)",
            "Average Percentage of SAT Clauses(MV)",
            "Average Percent Hamming distance (MV)",
            "Average Number of Contradictions (WP)",
        ]
    )

    df_per_iteration = pd.DataFrame(
        columns=[
            "N and C",
            "SAT Bit",
            "Number of SAT Clauses",
            "Hamming distance",
            "Runtime",
            "Number of Dont Care",
            "Number of Iterations",
            "number of absent literals",
            "SAT Bit (MV)",
            "Number of SAT Clauses(MV)",
            "Hamming distance (MV)",
            "Number of Contradictions (WP)",
        ]
    )

    for key in res_dict:
        n = key[0]
        c = key[1]
        algorithm = key[2]
        m = np.ceil(n * c)
        file_name = (
            str(class_type.__name__) + "_" + str(algorithm) + "_n_" + str(n) + ".csv"
        )

        res_arr = res_dict[key] / T
        df = df.append(
            {
                "N and C": (n, c),
                "SAT Percentage": res_arr[0] * 100,
                "Average Percentage of SAT Clauses": 100 * res_arr[1] / m,
                "Average Percent Hamming distance": 100 * res_arr[2] / n,
                "Average Runtime": res_arr[3] / 3600,
                "Average Percent Dont Care": res_arr[4] / n,
                "Average Number of Iterations": res_arr[5],
                "Average number of absent literals": res_arr[6] / n,
                "SAT Percentage (MV)": res_arr[7] * 100,
                "Average Percentage of SAT Clauses(MV)": 100 * res_arr[8] / m,
                "Average Percent Hamming distance (MV)": 100 * res_arr[9] / n,
                "Average Number of Contradictions (WP)": 100 * res_arr[10] / n,
            },
            ignore_index=True,
        )

        df.to_csv(file_name)

    for key in res_per_itration_dict:
        n = key[0]
        c = key[1]
        algorithm = key[2]

        file_name_per_res = (
            str(class_type.__name__)
            + "_"
            + "perIter"
            + str(algorithm)
            + "_n_"
            + str(n)
            + ".csv"
        )

        for res_arr in res_per_itration_dict[key]:
            df_per_iteration = df_per_iteration.append(
                {
                    "N and C": (n, c),
                    "SAT Bit": res_arr[0],
                    "Number of SAT Clauses": res_arr[1],
                    "Hamming distance": res_arr[2],
                    "Runtime": res_arr[3] / 3600,
                    "Number of Dont Care": res_arr[4],
                    "Number of Iterations": res_arr[5],
                    "number of absent literals": res_arr[6],
                    "SAT Bit (MV)": res_arr[7],
                    "Number of SAT Clauses(MV)": res_arr[8],
                    "Hamming distance (MV)": res_arr[9],
                    "Number of Contradictions (WP)": res_arr[10],
                },
                ignore_index=True,
            )
        df_per_iteration.to_csv(file_name_per_res)


def main(n, algorithm):
    np.random.seed(12345)
    global T
    print(
        "------------Running test for n={}, With Algoritm {} -------\n".format(
            n, algorithm
        )
    )

    n = int(n)
    c = [20]
    thread_list = []
    thread_ratio = T // 10

    try:
        start = time.process_time()
        for i in range(T // thread_ratio):
            for alpha in c:
                thread = threading.Thread(
                    target=test_flow, args=(n, alpha, i, algorithm)
                )
                thread_list.append(thread)
        for thread in thread_list:
            thread.start()
        for thread in thread_list:
            thread.join()

        end = time.process_time()
    except Exception as err:
        print("Error while running a thread")
        print(err)

    parse_results(class_type)
    print("Total time of {} minutes".format((end - start) / 60))


if __name__ == "__main__":
    n = int(sys.argv[1])
    algorithm = str(sys.argv[2])
    # n = 10
    # algorithm = "SP"
    main(n, algorithm)
