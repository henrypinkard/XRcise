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
from exercise import Exercise

INSPIRATIONAL_QUOTES = ['Today\'s workout ends with an inspirational quote. Mike Tyson once said, I ain\'t the same '
                        'person I was when I bit that guy\'s ear off',
                        'Nice job. Keep it up and those legs will be sexy in no time.', 'You did a great job...for a human',
                        'And now for an inspirational quote from Nick Young. Passing? That\'s the point guards job',
                        'Never forget the words or Marshawn Lynch: I know I\'m gon get got. But I\'m gon get mine more '
                        'than I get got tho', 'Maybe you should have a glass of wine? Lebron drinks wine everyday',
                        'Remember, haters are just fans in denial']


class ExecutionEngine:

    def __init__(self, exercise_bank, profile, duration, workout_type):
        self.exercise_bank = exercise_bank
        self.profile = profile

        if np.random.rand() < 0.5:
            self.voice = 'Allison'
        else:
            self.voice = 'Tom'

        sequence = self.build_workout_sequence(duration, workout_type)

        # print full sequence
        for exercise, duration in sequence:
            if type(exercise) == tuple:
                print(exercise[0].get_name(profile['equipment']) + ('' if not exercise[0].paired else ' right and left'))
            else:
                print(exercise.get_name(profile['equipment']) + ('' if not exercise.paired else ' right and left'))

        # begin workout
        self.speak('Press enter key to begin')
        input('Press enter key to begin')
        for exercise, duration in sequence:
            if type(exercise) == tuple:
                exercise1, exercise2 = exercise
                if duration[-1] == 's':
                    if exercise1.paired:
                        name1 = exercise1.get_name(profile['equipment']) + (' Right side' if
                                                            exercise.count % 2 == 0 else ' Left side')
                        name2 = exercise2.get_name(profile['equipment']) + (' Right side' if
                                                                            exercise.count % 2 == 0 else ' Left side')
                    else:
                        name1 = exercise1.get_name(profile['equipment'])
                        name2 = exercise2.get_name(profile['equipment'])
                    duration = int(duration[:-1])
                else:
                    pass
                    # TODO: implement number of reps?

                fullname = 'Human1: ' + name1 + '\nHuman2: ' + name2
                self.execute_exercise(fullname, duration)
                exercise1.count = exercise1.count + 1 #only keep count for one in pair
            else:
                if duration[-1] == 's':
                    if exercise.paired:
                        if exercise.count % 2 == 0:
                            name = exercise.get_name(profile['equipment']) + ' Right side'
                        else:
                            name = exercise.get_name(profile['equipment']) + ' Left side'
                    else:
                        name = exercise.get_name(profile['equipment'])
                    duration = int(duration[:-1])
                else:
                    pass
                    # TODO: implement number of reps?

                self.execute_exercise(name, duration)
                exercise.count = exercise.count + 1

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
        print(name)
        print('Duration: {}\n'.format(duration))
        self.speak(name)
        self.speak('For {} seconds'.format(duration))
        self.countdown(duration)

    def make_exercise(self, name, paired='', cardio=False):
        return Exercise(name, paired=paired, cardio=cardio)

    def sample_exercises(self, cardio_categories, verbose=False):
        exercises = []
        dissimilarity_vec = np.ones(self.exercise_bank.get_num_valid_exercises())
        ex_index = -1
        for i, cardio_classes in enumerate(cardio_categories):
            norm_probs = dissimilarity_vec / np.sum(dissimilarity_vec)
            # if verbose:
            #     print('Currrent exercise: {}\n'.format(self.all_exercises[ex_index].name) if ex_index != -1 else 'None')
            #     sort_ind = np.argsort(norm_probs)
            #     for i in sort_ind:
            #         print('{}: {:.3f}'.format(self.all_exercises[i].name, norm_probs[i]))
            #     print('\n\n\n')

            ex_index = np.nonzero(np.random.multinomial(1, norm_probs))[0][0]
            attempts = 0
            while self.exercise_bank.get_exercise(ex_index).cardio not in cardio_classes:
                ex_index = np.nonzero(np.random.multinomial(1, norm_probs))[0][0]  # resample until you get a valid one
                if attempts == 100:
                    break #no valid ones are likely
                attempts += 1
            exercises.append(self.exercise_bank.get_exercise(ex_index))
            dissimilarity_vec *= np.exp(-self.exercise_bank._adjacency_mat[ex_index, :])
        return exercises

    def build_workout_sequence(self, duration, workout_type=-1):
        # determine workout format
        if workout_type == -1:
            workout_type = np.random.randint(3)
        exercise_sequence = []
        if self.profile['warmup']:
            duration -= 2
            exercise_sequence.append((self.make_exercise('Warmup'), '120s'))
        if workout_type == 0:
            #### 1 min strength 1 min cardio #####
            total_rounds = duration // 4
            ex_list = self.sample_exercises(total_rounds * [[1, 2, 3, 4], [4, 5]])
            for i in range(total_rounds):
                exercise_sequence.append((ex_list[2 * i + 0], '60s'))
                exercise_sequence.append((ex_list[2 * i + 1], '60s'))
                exercise_sequence.append((ex_list[2 * i + 0], '60s'))
                exercise_sequence.append((ex_list[2 * i + 1], '60s'))
        elif workout_type == 1:
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
        elif workout_type == 2:
            # 20 seconds on, 10 seconds rest x 8 for one strength exercise, 1 min crdio'
            total_rounds = duration // 5
            ex_list = self.sample_exercises([[1, 2, 3, 4], [4, 5]] * total_rounds)
            for i in range(total_rounds):
                for j in range(8):
                    exercise_sequence.append((ex_list[2 * i], '20s'))
                    exercise_sequence.append((self.make_exercise('Rest'), '10s'))
                exercise_sequence.append((ex_list[2 * i + 1], '60s'))
        elif workout_type == 3:
            total_rounds = int(np.floor(duration / 3))
            #TODO: account for limited equipment
            ex_list = self.sample_exercises([[1, 2, 3, 4, 5]] * total_rounds * 4)
            for i in range(total_rounds):
                ex0 = ex_list[i]
                ex1 = ex_list[i + 1]
                ex2 = ex_list[i + 2]
                ex3 = ex_list[i + 3]
                exercise_sequence.append(((ex0, ex1), '40s'))
                exercise_sequence.append(((ex1, ex0), '40s'))
                exercise_sequence.append(((self.make_exercise('Rest'), self.make_exercise('Rest')), '20s'))
                exercise_sequence.append(((ex2, ex3), '40s'))
                exercise_sequence.append(((ex3, ex2), '40s'))
                exercise_sequence.append(((self.make_exercise('Rest'), self.make_exercise('Rest')), '20s'))



        #     #30 reps of each exercise; do full circuit twice
        return exercise_sequence