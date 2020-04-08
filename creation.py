import csv
import numpy as np
import time
import os
from os import system
import sys
import select
import pickle
import matplotlib.pyplot as plt
from classes import Exercise, ExerciseBank

POSSIBLE_EQUIPMENT = {'TRX': 'trx', 'Weights':'weights', 'Kettlebells':'kettlebell', 'Pullup bar':'pullupbar',
                      'Resistance bands':'band', 'towel + smooth floor':'towel'}

def base_dir():
    return os.path.dirname(os.path.realpath(__file__)) + os.sep

def launch_include_list_editor(all_exercises):
    inclusion_list = []
    name = input('Name for this list of exercises')
    print('Type \'y\' to include')
    for exercise in all_exercises:
        y = input('Include {} ({})?'.format(exercise.base_name, ','.join(exercise.equipment)))
        if y == 'y':
            inclusion_list.append(exercise.base_name)
    return name, inclusion_list

def get_profile():
    """
    Profile store available equipment, inclusion list
    """

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
        print('============================')
        print('====Avaliable Equipment=====')
        print('============================')
        for e in POSSIBLE_EQUIPMENT.keys():
            if input('Do you have {} (y/n)?'.format(e)) == 'y':
                equipment.append(POSSIBLE_EQUIPMENT[e])
        profile['equipment'] = equipment
        if len(equipment) != 0:
            num_humans = input('===============================\n'
                           'How many humans are participating?')
            profile['num_humans'] = int(num_humans)

        warmup = input('===============================\nDo you want to warm up (y/n)?') == 'y'
        profile['warmup'] = warmup
        # load exercises given equipment available and their distance similarity matrix
        exercise_bank = ExerciseBank(profile['equipment'])
        #check for exercise inclusion list
        include_list_prompt = '===================================================\n' \
                              '=========Select exercise include list==============\n' \
                              '===================================================\n' \
                              '0) Create a new list of exercises to include\n1) Use all exercises\n'
        for i, include_list_name in enumerate(include_lists.keys()):
            include_list_prompt += '{}) {}\n'.format(2 + i, include_list_name)
        selection = input(include_list_prompt + '\n')
        if selection == '1':
            # nothing to filter because using all
            return profile, exercise_bank
        elif selection == '0':
            selected_include_list_name, include_list = launch_include_list_editor(exercise_bank._all_exercises)
            include_lists[selected_include_list_name] = include_list
            save_inclusion_lists(include_lists)
        else:
            index = int(selection) - 2
            selected_include_list_name = list(include_lists.keys())[index]
            include_list = include_lists[selected_include_list_name]
        exercise_bank.filter_by_inclusion_list(include_list)
        profile['include_list'] = selected_include_list_name
        save_profile(profile)
    else:
        exercise_bank = ExerciseBank(profile['equipment'])
        if profile['include_list'] != 'All exercises':
            exercise_bank.filter_by_inclusion_list(include_lists[profile['include_list']])

    return profile, exercise_bank


