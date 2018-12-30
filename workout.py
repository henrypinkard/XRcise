import csv
import numpy as np
import time
import os
from os import system
import sys
import select
import matplotlib.pyplot as plt


POSSIBLE_EQUIPMENT = ['trx', 'weights', 'kettlebells', 'pullupbar']
FORMATS = ['1-1 strength-cardio', '3x1 strength-cardio', 'Tabata']
# , 'Circuit']
# FORMAT_DESCRIPTION = ['Alternate 1 minute of an exercise from the strength categories with 1 min of an exercise from the cardio category',
#     '1 min of one strength exercise, 1 min of second strength exercise, 1 min of third strength exercise, 1 min of cardio',
#     '20 seconds on, 10 seconds rest x 8 for one strength exercise, 1 min cardio',
#     '30 reps of each exercise; do full circuit twice']

class Exercise:

    def __init__(self, name, paired, cardio_score):
        self.name = name
        self.paired = paired == 'paired'
        self.cardio_score = cardio_score
        self.rounds = 0

def get_workout_params():
    """
    Prompt user for what equipment they have and what type of workout they want
    """
    # Workout duration (rounded to 5 minute intervals)
    duration = int(input('Enter workout duration (min):'))
    # check what equipment id available
    equipment = []
    for e in POSSIBLE_EQUIPMENT:
        if input('Do you have {} (y/n)?'.format(e)) == 'y':
            equipment.append(e)
    if np.random.rand() < 0.5:
        voice = 'Allison'
    else:
        voice = 'Tom'
    return duration, equipment, voice

def load_exercises(equipment):
    all_exercises = []
    with open('exercises.csv') as csv_file:
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
                muscle_groups_binary = np.array([float(f) for f in row[4:]])
                if equipment_needed is None or equipment_needed == '' or \
                        equipment_needed == [] or equipment_needed.lower() in equipment:
                    if mat is None:
                        mat = np.reshape(muscle_groups_binary, [-1, 1])
                    else:
                        mat = np.concatenate([mat, np.reshape(muscle_groups_binary, [-1, 1])], axis=1)
                    all_exercises.append(Exercise(name, paired, cardio_score))

    adjacency_mat = np.zeros((mat.shape[1], mat.shape[1]))
    #extra similiarty for exact same exercise

    normed_mat = mat / np.linalg.norm(mat, axis=0)
    for i in range(adjacency_mat.shape[0]):
        for j in range(adjacency_mat.shape[1]):
            adjacency_mat[i, j] = np.dot(normed_mat[:, i], normed_mat[:, j].T)
    adjacency_mat[np.diag_indices(mat.shape[1])] += 1
    #normalize
    adjacency_mat = adjacency_mat / np.max(np.ravel(adjacency_mat))
    return all_exercises, adjacency_mat, muscle_group_categories

def sample_exercises(cardio_categories, all_exercises, adjacency_mat, theta=0.0000001, memory=0.4, verbose=False):
    exercises = []
    similarity_vec = np.ones(len(all_exercises))
    ex_index = -1
    for i, cardio_classes in enumerate(cardio_categories):
        dissimilarity_vec = 1 / (theta + similarity_vec)
        norm_probs = dissimilarity_vec / np.sum(dissimilarity_vec)
        if verbose:
            print('Currrent exercise: {}\n'.format(all_exercises[ex_index].name) if ex_index != -1 else 'None')
            sort_ind = np.argsort(norm_probs)
            for i in sort_ind:
                print('{}: {:.3f}'.format(all_exercises[i].name, norm_probs[i]))
            print('\n\n\n')

        ex_index = np.nonzero(np.random.multinomial(1, norm_probs))[0][0]
        while all_exercises[ex_index].cardio_score not in cardio_classes:
            ex_index = np.nonzero(np.random.multinomial(1, norm_probs))[0][0] #resample until you get a valid one
        exercises.append(all_exercises[ex_index])
        # increase distance to exercise just picked and retain memory of which have been done
        if i == 0:
            similarity_vec = adjacency_mat[ex_index, :]
        else:
            memory_term = memory * similarity_vec
            new_term = (1 - memory) * adjacency_mat[ex_index, :]
            similarity_vec = memory_term + new_term
    return exercises

def build_workout_sequence(duration, equipment):
    # load exercises given equipment available and their distance similarity matrix
    all_exercises, adjacency_mat, muscle_group_categories = load_exercises(equipment)
    # determine workout format
    format_index = np.random.randint(len(FORMATS))
    exercise_sequence = []

    if format_index == 0:
        #### 1 min strength 1 min cardio #####
        total_rounds = duration // 4
        for i in range(total_rounds):
            ex_list = sample_exercises([[1, 2, 3, 4], [4, 5]], all_exercises, adjacency_mat)
            exercise_sequence.append((ex_list[0], '60s'))
            exercise_sequence.append((ex_list[1], '60s'))
            exercise_sequence.append((ex_list[0], '60s'))
            exercise_sequence.append((ex_list[1], '60s'))
    elif format_index == 1:
        # 1 min of 3 types of strength exercises, 1 min cardio
        total_rounds = duration // 4
        ex_list = sample_exercises([[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [4, 5]], all_exercises, adjacency_mat)
        for i in range(total_rounds):
            exercise_sequence.append((ex_list[0], '60s'))
            exercise_sequence.append((ex_list[1], '60s'))
            exercise_sequence.append((ex_list[2], '60s'))
            exercise_sequence.append((ex_list[3], '60s'))
    elif format_index == 2:
        # 20 seconds on, 10 seconds rest x 8 for one strength exercise, 1 min crdio'
        total_rounds = duration // 5
        ex_list = sample_exercises([[1, 2, 3, 4], [4, 5]]*total_rounds, all_exercises, adjacency_mat)
        for i in range(total_rounds):
            for j in range(8):
                exercise_sequence.append((ex_list[2*i], '20s'))
                exercise_sequence.append((Exercise('Rest', None, None), '10s'))
            exercise_sequence.append((ex_list[2*i + 1], '60s'))
    # elif format_index == 3:
    #     #30 reps of each exercise; do full circuit twice
    return exercise_sequence, format_index

def speak(text, voice):
    system('say -v \"{}\" \"{}\"'.format(voice, text))

def countdown(original_duration, voice):
    count_milestones = [t for t in [30, 10, 5, 4, 3, 2, 1] if t < original_duration]
    start = time.time()
    remaining = original_duration
    duration = original_duration
    paused = False
    while True:
        while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            if paused and line[0] == 'q':
                speak('I\'m sorry. I\m not designed to let you quit. Resuming workout', voice)
            #enter has been pressed
            paused = not paused
        else:
            if paused:
                duration = remaining
                start = time.time()
                print('\rWorkout paused. Press return to resume or type q + return to quit     ', end='')
                continue
            remaining = duration - (time.time() - start)
            print('\rTime remaining {}               '.format(int(np.ceil(remaining))), end='')
            if len(count_milestones) > 0 and count_milestones[0] > remaining:
                milestone = count_milestones.pop(0)
                speak(str(milestone), voice)
            if remaining < 0:
                print('\n\n')
                break

def execute_exercise(name, duration, voice):
    print('Exercise: {}'.format(name))
    print('Duration: {}\n'.format(duration))
    speak(name, voice)
    speak('For {} seconds'.format(duration), voice)
    countdown(duration, voice)

#get user input for type of workout
duration, equipment, voice = get_workout_params()

sequence, format_index = build_workout_sequence(duration, equipment)

format_name = FORMATS[format_index]
print('         ' + format_name)
# print('Description: ' + FORMAT_DESCRIPTION[format_index] + '\n\n')
# speak(FORMAT_DESCRIPTION[format_index], voice)
#print full sequence
for exercise, duration in sequence:
    print(exercise.name + ('' if not exercise.paired else ' right and left'))

#begin workout
input('Press enter key to begin')
speak('Press enter key to begin', voice)
for exercise, duration in sequence:
    if duration[-1] == 's':
        if exercise.paired:
            if exercise.rounds % 2 == 0:
                name = exercise.name + ' Right side'
            else:
                name = exercise.name + ' Left side'
        else:
            name = exercise.name
        duration = int(duration[:-1])
    else:
        pass
        #TODO: implement number of reps

    execute_exercise(name, duration, voice)
    exercise.rounds += 1

speak('Workout complete. Nice job. Keep it up and those legs will be sexy in no time.', voice)
