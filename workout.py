import csv
import numpy as np
import time
import os

POSSIBLE_EQUIPMENT = ['trx', 'weights', 'kettlebells', 'pullupbar']
FORMATS = ['1-1 strength-cardio', '3x1 strength-cardio', 'Tabata']
# , 'Circuit']
FORMAT_DESCRIPTION = ['Alternate 1 minute of an exercise from the strength categories with 1 min of an exercise from the cardio category',
    '1 min of one strength exercise, 1 min of second strength exercise, 1 min of third strength exercise, 1 min of cardio',
    '20 seconds on, 10 seconds rest x 8 for one strength exercise, 1 min cardio',
    '30 reps of each exercise; do full circuit twice']

class Exercise:

    def __init__(self, name, equipment, paired=False):
        self.name = name
        self.paired = paired
        self.equipment = None if equipment is None or equipment == '' else equipment.lower()


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
    return duration, equipment

def load_exercises(equipment):
    all_exercises = {}
    for category in ['cardio', 'arms', 'legs', 'core']:
        path = os.path.dirname(os.path.realpath(__file__)) + os.sep + category + '.csv'
        exercises = []
        with open(path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                ex = Exercise(*row)
                if ex.equipment is None or ex.equipment in equipment:
                    exercises.append(ex)
        all_exercises[category] = exercises
    return all_exercises

def random_exercise(types):
    """
    :param type: 'cardio', 'arms', 'legs', 'core' or a list of them
    """
    choices = []
    if type(types) == list:
        for a_type in types:
            choices += all_exercises[a_type]
    else:
        choices += all_exercises[types]
    return choices[np.random.randint(len(choices))]

def build_workout_sequence():
    # determine workout format
    format_index = np.random.randint(len(FORMATS))
    format_name = FORMATS[format_index]
    exercise_sequence = []
    print('         ' + format_name)
    print('Description: ' + FORMAT_DESCRIPTION[format_index] + '\n\n')
    if format_index == 0:
        # 1 min strength 1 min cardio
        total_rounds = duration // 2
        for i in range(total_rounds):
            exercise_sequence.append((random_exercise(['arms', 'legs', 'core']), '60s'))
            exercise_sequence.append((random_exercise(['cardio']), '60s'))
    elif format_index == 1:
        # 1 min of 3 types of strength exercises, 1 min cardio
        total_rounds = duration // 4
        ex0 = random_exercise(['arms', 'legs', 'core'])
        ex1 = random_exercise(['arms', 'legs', 'core'])
        ex2 = random_exercise(['arms', 'legs', 'core'])
        ex3 = random_exercise(['cardio'])
        for i in range(total_rounds):
            exercise_sequence.append((ex0, '60s'))
            exercise_sequence.append((ex1, '60s'))
            exercise_sequence.append((ex2, '60s'))
            exercise_sequence.append((ex3, '60s'))
    elif format_index == 2:
        # 20 seconds on, 10 seconds rest x 8 for one strength exercise, 1 min cardio'
        total_rounds = duration // 5
        for i in range(total_rounds):
            ex0 = random_exercise(['arms', 'legs', 'core'])
            for j in range(8):
                exercise_sequence.append((ex0, '20s'))
                exercise_sequence.append((Exercise('Rest', None), '10s'))
            exercise_sequence.append((random_exercise(['cardio']), '60s'))
    # elif format_index == 3:
    #     #30 reps of each exercise; do full circuit twice
    return exercise_sequence


duration, equipment = get_workout_params()
all_exercises = load_exercises(equipment)

sequence = build_workout_sequence()

for exercise, duration in sequence:
    print('Exercise: {}'.format(exercise.name))
    print('Duration: {}\n'.format(duration))
    if duration[-1] == 's':
        duration_s = int(duration[:-1])
        print(exercise.name)
        start = time.time()
        while True:
            remaining = duration_s - (time.time() - start)
            print('\rTime remaining {}               '.format(int(remaining)), end='')
            if remaining < 0:
                #TODO: async play some sound
                print('\n\n')
                break
    else:
        pass
        #TODO: implement number of reps


