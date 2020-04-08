import csv
import numpy as np
import time
import os
from os import system
import sys
import select
import pickle
import matplotlib.pyplot as plt
from creation import get_profile
from execution import ExecutionEngine
import argparse


# def save_workout(sequence, name):
#     file = open(base_dir() + 'favorite_workouts{}{}'.format(os.sep, name), 'wb')
#     pickle.dump(sequence, file)
#     file.close()
#
# def get_saved_workout_names():
#     return [s for s in os.listdir(base_dir() + 'favorite_workouts') if s[0] != '.']
#
# def load_workout(name):
#     file = open(base_dir() + 'favorite_workouts{}{}'.format(os.sep, name), 'rb')
#     loaded_sequence = pickle.load(file)
#     file.close()
#     return loaded_sequence

# def prompt_for_loaded_workout():
#     #get user input for type of workout
#     saved = get_saved_workout_names()
#     if len(saved) != 0:
#         if not input('Load a previously saved workout (y/n)?') == 'y':
#             return None
#         for i, w in enumerate(saved):
#             print('{}: {}'.format(i, w))
#         choice = input('Type number to load previous workout')
#         try:
#             index = int(choice)
#             if index < len(saved):
#                 return load_workout(saved[index])
#         except:
#             raise Exception('Error loading workout')
#
# sequence = prompt_for_loaded_workout()


# parser = argparse.ArgumentParser()
# parser.add_argument('--workout_type', type=int, default=3)
# args = parser.parse_args()



profile, exercise_bank = get_profile()
duration = int(input('Enter workout duration (min):'))
ExecutionEngine(exercise_bank, profile, duration)

