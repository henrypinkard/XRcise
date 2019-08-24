import csv
import numpy as np
import time
import os
from os import system
import sys
import select
import pickle
import matplotlib.pyplot as plt

POSSIBLE_EQUIPMENT = ['trx', 'weights', 'kettlebells', 'pullupbar']

def launch_include_list_editor(all_exercises):
    inclusion_list = []
    name = input('Name for this list of exercises')
    print('Type \'y\' to include')
    for exercise in all_exercises:
        y = input('Include {}?'.format(exercise['name']))
        if y == 'y':
            inclusion_list.append(exercise['name'])
    return name, inclusion_list

def make_exercise(name, paired='', cardio=False):
    return {'name': name, 'paired': paired == 'paired', 'cardio': cardio, 'count': 0}

def get_profile():
    """
    Profile store available equipment, inclusion list
    """

    def load_exercises(equipment):
        all_exercises = []
        with open(base_dir() + 'exercises.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            mat = None
            for i, row in enumerate(csv_reader):
                if i == 0:
                    muscle_group_categories = [entry for entry in row if entry != '']
                else:
                    name = row[0]
                    equipment_needed = row[1]
                    paired = row[2]
                    cardio_score = int(row[3])
                    muscle_groups_binary = np.array([float(f) for f in row[5:]])
                    if equipment_needed is None or equipment_needed == '' or \
                            equipment_needed == [] or equipment_needed.lower() in equipment:
                        if mat is None:
                            mat = np.reshape(muscle_groups_binary, [-1, 1])
                        else:
                            mat = np.concatenate([mat, np.reshape(muscle_groups_binary, [-1, 1])], axis=1)
                        all_exercises.append(make_exercise(name, paired, cardio_score))

        adjacency_mat = np.zeros((mat.shape[1], mat.shape[1]))
        normed_mat = mat / np.linalg.norm(mat, axis=0)
        for i in range(adjacency_mat.shape[0]):
            for j in range(adjacency_mat.shape[1]):
                adjacency_mat[i, j] = np.dot(normed_mat[:, i], normed_mat[:, j].T)
        # extra similiarty for exact same exercise so it becomes unlikely to be repeated
        adjacency_mat[np.diag_indices(mat.shape[1])] += 4
        return all_exercises, adjacency_mat, muscle_group_categories

    def save_profile(params):
        file = open(base_dir() + 'profile', 'wb')
        pickle.dump(params, file)
        file.close()

    def load_profile():
        if not os.path.isfile(base_dir() + 'profile'):
            return None
        file = open(base_dir() + 'profile', 'rb')
        params = pickle.load(file)
        file.close()
        return params

    def save_inclusion_lists(inclusion_lists):
        file = open(base_dir() + 'inclusion_lists', 'wb')
        pickle.dump(inclusion_lists, file)
        file.close()

    def load_inclusion_lists():
        if ('inclusion_lists' not in os.listdir(base_dir())):
            return {}  # not yet created
        file = open(base_dir() + 'inclusion_lists', 'rb')
        inclusion_lists = pickle.load(file)
        file.close()
        return inclusion_lists

    def filter_by_inclusion_list(all_exercises, adjacency_mat, include_list):
        # filter by included exercises
        valid_indices = []
        for included in include_list:
            for i, exercise in enumerate(all_exercises):
                if exercise['name'] == included:
                    valid_indices.append(i)
        valid_indices = np.array(valid_indices)
        filtered_all_exercises = [all_exercises[index] for index in valid_indices]
        filtered_adjacency_mat = adjacency_mat[valid_indices, :][:, valid_indices]
        return filtered_all_exercises, filtered_adjacency_mat

    profile = load_profile()
    include_lists = load_inclusion_lists()
    reload = True
    if profile is not None:
        print('\n\n Current profile')
        for key in profile.keys():
            print('\t' + key)
            print('\t\t' + str(profile[key]))
        reload = input('Edit existing profile (y/n)?') == 'y'
    if reload:
        profile = {}
        # check what equipment id available
        equipment = []
        for e in POSSIBLE_EQUIPMENT:
            if input('Do you have {} (y/n)?'.format(e)) == 'y':
                equipment.append(e)
                profile['equipment'] = equipment
        #Do you want to warm up
        warmup = input('Do you want to warm up (y/n)?') == 'y'
        profile['warmup'] = warmup
        # load exercises given equipment available and their distance similarity matrix
        all_exercises, adjacency_mat, muscle_group_categories = load_exercises(profile['equipment'])
        #check for exercise inclusion list
        include_list_prompt = 'Select exercise include list: \n0) New include list\n1) All exercises\n'
        for i, include_list_name in enumerate(include_lists.keys()):
            include_list_prompt += '{}) {}\n'.format(2 + i, include_list_name)
        selection = input(include_list_prompt + '\n')
        if selection == '1':
            # nothing to filter because using all
            selected_include_list_name = 'All exercises'
            return all_exercises, adjacency_mat
        elif selection == '0':
            selected_include_list_name, include_list = launch_include_list_editor(all_exercises)
            include_lists[selected_include_list_name] = include_list
            save_inclusion_lists(include_lists)
        else:
            index = int(selection) - 2
            selected_include_list_name = list(include_lists.keys())[index]
            include_list = include_lists[selected_include_list_name]
        all_exercises, adjacency_mat = filter_by_inclusion_list(all_exercises, adjacency_mat, include_list)
        profile['include_list'] = selected_include_list_name
        save_profile(profile)
    else:
        all_exercises, adjacency_mat, muscle_group_categories = load_exercises(profile['equipment'])
        if profile['include_list'] != 'All exercises':
            all_exercises, adjacency_mat = filter_by_inclusion_list(all_exercises, adjacency_mat,
                                                                    include_lists[profile['include_list']])

    return profile, all_exercises, adjacency_mat

def base_dir():
    return os.path.dirname(os.path.realpath(__file__)) + os.sep
