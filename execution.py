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

INSPIRATIONAL_QUOTES = ['Today\'s workout ends with an inspirational quote. Mike Tyson once said, I ain\'t the same '
                        'person I was when I bit that guy\'s ear off',
                        'Nice job. Keep it up and those legs will be sexy in no time.', 'You did a great job...for a human',
                        'And now for an inspirational quote from Nick Young. Passing? That\'s the point guards job',
                        'Never forget the words or Marshawn Lynch: I know I\'m gon get got. But I\'m gon get mine more '
                        'than I get got tho', 'Maybe you should have a glass of wine? Lebron drinks wine everyday',
                        'Remember, haters are just fans in denial']



class ExecutionEngine:

    def __init__(self, all_exercises, adjacency_mat, profile, duration):
        self.all_exercises = all_exercises
        self.adjacency_mat = adjacency_mat
        self.profile = profile

        if np.random.rand() < 0.5:
            self.voice = 'Allison'
        else:
            self.voice = 'Tom'

        sequence = self.build_workout_sequence(duration)

        # print full sequence
        for exercise, duration in sequence:
            print(exercise['name'] + ('' if not exercise['paired'] else ' right and left'))

        # begin workout
        self.speak('Press enter key to begin')
        input('Press enter key to begin')
        for exercise, duration in sequence:
            if duration[-1] == 's':
                if exercise['paired']:
                    if exercise['count'] % 2 == 0:
                        name = exercise['name'] + ' Right side'
                    else:
                        name = exercise['name'] + ' Left side'
                else:
                    name = exercise['name']
                duration = int(duration[:-1])
            else:
                pass
                # TODO: implement number of reps

            self.execute_exercise(name, duration)
            exercise['count'] = exercise['count'] + 1

        self.speak('Workout complete')
        self.speak(INSPIRATIONAL_QUOTES[np.random.randint(len(INSPIRATIONAL_QUOTES))])
        name = input('Enter a name to save this workout or type q to quit')
        if name != 'q':
            self.save_workout(sequence, name)
            print('Workout saved as {}'.format(name))

    def speak(self, text):
        system('say -v \"{}\" \"{}\"'.format(self.voice, text))

    def countdown(self, original_duration):
        count_milestones = [t for t in [30, 10, 5, 4, 3, 2, 1] if t < original_duration]
        start = time.time()
        remaining = original_duration
        duration = original_duration
        paused = False
        while True:
            while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline()
                if paused and line[0] == 'q':
                    self.speak('I\'m sorry. I\m not designed to let you quit. Resuming workout')
                # enter has been pressed
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
                    self.speak(str(milestone))
                if remaining < 0:
                    print('\n\n')
                    break

    def execute_exercise(self, name, duration):
        print('Exercise: {}'.format(name))
        print('Duration: {}\n'.format(duration))
        self.speak(name)
        self.speak('For {} seconds'.format(duration))
        self.countdown(duration)

    def make_exercise(self, name, paired='', cardio=False):
        return {'name': name, 'paired': paired == 'paired', 'cardio': cardio, 'count': 0}

    def sample_exercises(self, cardio_categories, verbose=False):
        exercises = []
        dissimilarity_vec = np.ones(len(self.all_exercises))
        ex_index = -1
        for i, cardio_classes in enumerate(cardio_categories):
            norm_probs = dissimilarity_vec / np.sum(dissimilarity_vec)
            if verbose:
                print('Currrent exercise: {}\n'.format(self.all_exercises[ex_index]['name']) if ex_index != -1 else 'None')
                sort_ind = np.argsort(norm_probs)
                for i in sort_ind:
                    print('{}: {:.3f}'.format(self.all_exercises[i]['name'], norm_probs[i]))
                print('\n\n\n')

            ex_index = np.nonzero(np.random.multinomial(1, norm_probs))[0][0]
            attempts = 0
            while self.all_exercises[ex_index]['cardio'] not in cardio_classes:
                ex_index = np.nonzero(np.random.multinomial(1, norm_probs))[0][0]  # resample until you get a valid one
                if attempts == 100:
                    break #no valid ones are likely
                attempts += 1
            exercises.append(self.all_exercises[ex_index])
            dissimilarity_vec *= np.exp(-self.adjacency_mat[ex_index, :])
        return exercises

    def build_workout_sequence(self, duration):
        # determine workout format
        format_index = np.random.randint(3)
        exercise_sequence = []
        if self.profile['warmup']:
            duration -= 2
            exercise_sequence.append((self.make_exercise('Warmup'), '120s'))
        if format_index == 0:
            #### 1 min strength 1 min cardio #####
            total_rounds = duration // 4
            ex_list = self.sample_exercises(total_rounds * [[1, 2, 3, 4], [4, 5]])
            for i in range(total_rounds):
                exercise_sequence.append((ex_list[2 * i + 0], '60s'))
                exercise_sequence.append((ex_list[2 * i + 1], '60s'))
                exercise_sequence.append((ex_list[2 * i + 0], '60s'))
                exercise_sequence.append((ex_list[2 * i + 1], '60s'))
        elif format_index == 1:
            # 2x 1 min of 3 types of strength exercises, 1 min cardio
            total_rounds = duration // 8
            ex_list = self.sample_exercises(total_rounds * [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [4, 5]])
            for i in range(total_rounds):
                exercise_sequence.append((ex_list[4 * i + 0], '60s'))
                exercise_sequence.append((ex_list[4 * i + 1], '60s'))
                exercise_sequence.append((ex_list[4 * i + 2], '60s'))
                exercise_sequence.append((ex_list[4 * i + 3], '60s'))
                exercise_sequence.append((ex_list[4 * i + 0], '60s'))
                exercise_sequence.append((ex_list[4 * i + 1], '60s'))
                exercise_sequence.append((ex_list[4 * i + 2], '60s'))
                exercise_sequence.append((ex_list[4 * i + 3], '60s'))
        elif format_index == 2:
            # 20 seconds on, 10 seconds rest x 8 for one strength exercise, 1 min crdio'
            total_rounds = duration // 5
            ex_list = self.sample_exercises([[1, 2, 3, 4], [4, 5]] * total_rounds)
            for i in range(total_rounds):
                for j in range(8):
                    exercise_sequence.append((ex_list[2 * i], '20s'))
                    exercise_sequence.append((self.make_exercise('Rest'), '10s'))
                exercise_sequence.append((ex_list[2 * i + 1], '60s'))
        # elif format_index == 3:
        #     #30 reps of each exercise; do full circuit twice
        return exercise_sequence