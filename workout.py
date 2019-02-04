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
INSPIRATIONAL_QUOTES = ['Today\'s workout ends with an inspirational quote. Mike Tyson once said, I ain\'t the same '
                        'person I was when I bit that guy\'s ear off',
                        'Nice job. Keep it up and those legs will be sexy in no time.', 'You did a great job...for a human',
                        'And now for an inspirational quote from Nick Young. Passing? That\'s the point guards job',
                        'Never forget the words or Marshawn Lynch: I know I\'m gon get got. But I\'m gon get mine more '
                        'than I get got tho', 'Maybe you should have a glass of wine? Lebron drinks wine everyday',
                        'Remember, haters are just fans in denial']


def get_workout_params():
    """
    Prompt user for what equipment they have and what type of workout they want
    """
    # Workout duration (rounded to 5 minute intervals)
    duration = int(input('Enter workout duration (min):'))
    params = load_workout_params()
    reload = True
    if params is not None:
        print('\n\n Previous settings')
        for key in params.keys():
            print('\t' + key)
            print('\t\t' + str(params[key]))
        reload = input('Edit previous workout settings (y/n)?') == 'y'
    if reload:
        params = {}
        # check what equipment id available
        equipment = []
        for e in POSSIBLE_EQUIPMENT:
            if input('Do you have {} (y/n)?'.format(e)) == 'y':
                equipment.append(e)
        params['equipment'] = equipment
        #Do you want to warm up
        warmup = input('Do you want to warm up (y/n)?') == 'y'
        params['warmup'] = warmup
        save_workout_params(params)
    return duration, params

def base_dir():
    return os.path.dirname(os.path.realpath(__file__)) + os.sep

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
                muscle_groups_binary = np.array([float(f) for f in row[4:]])
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
    #extra similiarty for exact same exercise so it becomes unlikely to be repeated
    adjacency_mat[np.diag_indices(mat.shape[1])] += 4
    return all_exercises, adjacency_mat, muscle_group_categories

def make_exercise(name, paired='', cardio=False):
    return {'name': name, 'paired': paired == 'paired', 'cardio': cardio, 'count': 0}

def sample_exercises(cardio_categories, all_exercises, adjacency_mat, verbose=False):
    exercises = []
    dissimilarity_vec = np.ones(len(all_exercises))
    ex_index = -1
    for i, cardio_classes in enumerate(cardio_categories):
        norm_probs = dissimilarity_vec / np.sum(dissimilarity_vec)
        if verbose:
            print('Currrent exercise: {}\n'.format(all_exercises[ex_index]['name']) if ex_index != -1 else 'None')
            sort_ind = np.argsort(norm_probs)
            for i in sort_ind:
                print('{}: {:.3f}'.format(all_exercises[i]['name'], norm_probs[i]))
            print('\n\n\n')

        ex_index = np.nonzero(np.random.multinomial(1, norm_probs))[0][0]
        while all_exercises[ex_index]['cardio'] not in cardio_classes:
            ex_index = np.nonzero(np.random.multinomial(1, norm_probs))[0][0] #resample until you get a valid one
        exercises.append(all_exercises[ex_index])
        dissimilarity_vec *= np.exp(-adjacency_mat[ex_index, :])
    return exercises

def build_workout_sequence(duration, params):
    # load exercises given equipment available and their distance similarity matrix
    all_exercises, adjacency_mat, muscle_group_categories = load_exercises(params['equipment'])
    # determine workout format
    format_index = np.random.randint(3)
    exercise_sequence = []
    if params['warmup']:
        duration -= 2
        exercise_sequence.append((make_exercise('Warmup'), '120s'))
    if format_index == 0:
        #### 1 min strength 1 min cardio #####
        total_rounds = duration // 4
        ex_list = sample_exercises(total_rounds*[[1, 2, 3, 4], [4, 5]], all_exercises, adjacency_mat)
        for i in range(total_rounds):
            exercise_sequence.append((ex_list[2*i + 0], '60s'))
            exercise_sequence.append((ex_list[2*i + 1], '60s'))
            exercise_sequence.append((ex_list[2*i + 0], '60s'))
            exercise_sequence.append((ex_list[2*i + 1], '60s'))
    elif format_index == 1:
        # 2x 1 min of 3 types of strength exercises, 1 min cardio
        total_rounds = duration // 8
        ex_list = sample_exercises(total_rounds*[[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [4, 5]], all_exercises, adjacency_mat)
        for i in range(total_rounds):
            exercise_sequence.append((ex_list[4*i + 0], '60s'))
            exercise_sequence.append((ex_list[4*i + 1], '60s'))
            exercise_sequence.append((ex_list[4*i + 2], '60s'))
            exercise_sequence.append((ex_list[4*i + 3], '60s'))
            exercise_sequence.append((ex_list[4*i + 0], '60s'))
            exercise_sequence.append((ex_list[4*i + 1], '60s'))
            exercise_sequence.append((ex_list[4*i + 2], '60s'))
            exercise_sequence.append((ex_list[4*i + 3], '60s'))
    elif format_index == 2:
        # 20 seconds on, 10 seconds rest x 8 for one strength exercise, 1 min crdio'
        total_rounds = duration // 5
        ex_list = sample_exercises([[1, 2, 3, 4], [4, 5]]*total_rounds, all_exercises, adjacency_mat)
        for i in range(total_rounds):
            for j in range(8):
                exercise_sequence.append((ex_list[2*i], '20s'))
                exercise_sequence.append((make_exercise('Rest'), '10s'))
            exercise_sequence.append((ex_list[2*i + 1], '60s'))
    # elif format_index == 3:
    #     #30 reps of each exercise; do full circuit twice
    return exercise_sequence

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

def save_workout(sequence, name):
    file = open(base_dir() + 'favorite_workouts{}{}'.format(os.sep, name), 'wb')
    pickle.dump(sequence, file)
    file.close()

def get_saved_workout_names():
    return [s for s in os.listdir(base_dir() + 'favorite_workouts') if s[0] != '.']

def load_workout(name):
    file = open(base_dir() + 'favorite_workouts{}{}'.format(os.sep, name), 'rb')
    loaded_sequence = pickle.load(file)
    file.close()
    return loaded_sequence

def save_workout_params(params):
    file = open(base_dir() + 'workout_params', 'wb')
    pickle.dump(params, file)
    file.close()

def load_workout_params():
    if not os.path.isfile(base_dir() + 'workout_params'):
        return None
    file = open(base_dir() + 'workout_params', 'rb')
    params = pickle.load(file)
    file.close()
    return params

def prompt_for_loaded_workout():
    #get user input for type of workout
    saved = get_saved_workout_names()
    if len(saved) != 0:
        if not input('Load a previously saved workout (y/n)?') == 'y':
            return None
        for i, w in enumerate(saved):
            print('{}: {}'.format(i, w))
        choice = input('Type number to load previous workout')
        try:
            index = int(choice)
            if index < len(saved):
                return load_workout(saved[index])
        except:
            raise Exception('Error loading workout')

if np.random.rand() < 0.5:
    voice = 'Allison'
else:
    voice = 'Tom'

sequence = prompt_for_loaded_workout()

if sequence is None:
    #generate a new one
    duration, params = get_workout_params()
    sequence = build_workout_sequence(duration, params)

#print full sequence
for exercise, duration in sequence:
    print(exercise['name'] + ('' if not exercise['paired'] else ' right and left'))

#begin workout
speak('Press enter key to begin', voice)
input('Press enter key to begin')
for exercise, duration in sequence:
    if duration[-1] == 's':
        if exercise.paired:
            if exercise['count'] % 2 == 0:
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
    exercise['count'] = exercise['count'] + 1

speak('Workout complete', voice)
speak(INSPIRATIONAL_QUOTES[np.random.randint(len(INSPIRATIONAL_QUOTES))], voice)
name = input('Enter a name to save this workout or type q to quit')
if name != 'q':
    save_workout(sequence, name)
    print('Workout saved as {}'.format(name))