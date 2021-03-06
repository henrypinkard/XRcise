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
from classes import Exercise, Event

INSPIRATIONAL_QUOTES = ['Today\'s workout ends with an inspirational quote about personal growth.'
                        ' Mike Tyson once said, I ain\'t the same person I was when I bit that guy\'s ear off',
                        'Dont forget to wash your hands',
                        'You did a great job...for a human',
                        'Never forget the words or Marshawn Lynch: I know I\'m gon get got. But I\'m gon get mine more '
                        'than I get got tho',
                        'Remember, haters are just fans in denial'
                        'Your workout data will now be sold to highest bidder']


class ExecutionEngine:

    def __init__(self, exercise_bank, profile, duration):
        self.exercise_bank = exercise_bank
        self.profile = profile

        # if np.random.rand() < 0.5:
        self.voice = 'Allison'
        # else:
        #     self.voice = 'Tom'

        sequence = self.build_workout_sequence(duration, profile)

        # print full sequence
        for i in range(len(sequence)):
            if type(sequence[i].exercise) == tuple:
                print(sequence[i].exercise[0].get_name(profile['equipment']) +
                      ('' if not sequence[i].exercise[0].paired else ' right and left'))
            else:
                print(sequence[i].exercise.get_name(profile['equipment']) +
                      ('' if not sequence[i].exercise.paired else ' right and left'))

        # begin workout
        self.speak('Press enter key to begin')
        input('Press enter key to begin')
        for i in range(len(sequence)):
            if type(sequence[i].exercise) == tuple: #partner workout
                exercise1, exercise2 = sequence[i].exerise
                if exercise1.paired:
                    name1 = exercise1.get_name(profile['equipment']) + (' Right side' if
                                                                        exercise1.count % 2 == 0 else ' Left side')
                else:
                    name1 = exercise1.get_name(profile['equipment'])

                if exercise2.paired:
                    name2 = exercise2.get_name(profile['equipment']) + (' Right side' if
                                                                        exercise2.count % 2 == 0 else ' Left side')
                else:
                    name2 = exercise2.get_name(profile['equipment'])


                fullname = 'Human1: ' + name1 + '\nHuman2: ' + name2
                self.execute_exercise(fullname, sequence[i].duration)
                exercise1.count = exercise1.count + 1
                exercise2.count = exercise2.count + 1
            else:
                if sequence[i].exercise.paired:
                    if sequence[i].exercise.count % 2 == 0:
                        name = sequence[i].exercise.get_name(profile['equipment']) + ' Right side'
                    else:
                        name = sequence[i].exercise.get_name(profile['equipment']) + ' Left side'
                else:
                    name = sequence[i].exercise.get_name(profile['equipment'])

                self.execute_exercise(name,  sequence[i].duration)
                sequence[i].exercise.count = sequence[i].exercise.count + 1

        self.speak('Workout complete')
        self.speak(INSPIRATIONAL_QUOTES[np.random.randint(len(INSPIRATIONAL_QUOTES))])
        # name = input('Enter a name to save this workout or type q to quit')
        # if name != 'q':
        #     self.save_workout(sequence, name)
        #     print('Workout saved as {}'.format(name))

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

    def make_exercise(self, name, paired=''):
        return Exercise(name, paired=paired)

    def sample_exercises(self, number, profile,  verbose=False):
        exercises = []
        dissimilarity_vec = np.ones(self.exercise_bank.get_num_valid_exercises())
        ex_index = -1
        last_equipment = []
        for i in range(number):
            #renormalize
            norm_probs = dissimilarity_vec / np.sum(dissimilarity_vec)
            # if verbose:
            #     print('Currrent exercise: {}\n'.format(self.all_exercises[ex_index].name) if ex_index != -1 else 'None')
            #     sort_ind = np.argsort(norm_probs)
            #     for i in sort_ind:
            #         print('{}: {:.3f}'.format(self.all_exercises[i].name, norm_probs[i]))
            #     print('\n\n\n')

            ex_index = np.nonzero(np.random.multinomial(1, norm_probs))[0][0]
            new_equip = self.exercise_bank.get_exercise(ex_index).get_preferred_equipment(profile['equipment'])
            attempts = 0
            num_humans = 1 if 'num_humans' not in profile else profile['num_humans']
            if num_humans > 1:
                #for now, assume only one of each equipment for set of humans
                while (new_equip in last_equipment and new_equip != 'bodyweight'):
                    ex_index = np.nonzero(np.random.multinomial(1, norm_probs))[0][0]  # resample until you get a valid one
                    new_equip = self.exercise_bank.get_exercise(ex_index).get_preferred_equipment(profile['equipment'])
                    if attempts == 10000:
                        print('Couldnt find exercises with different equipment')
                        break #no valid ones are likely
                    attempts += 1
            exercises.append(self.exercise_bank.get_exercise(ex_index))
            dissimilarity_vec *= np.exp(-self.exercise_bank._adjacency_mat[ex_index, :])
            last_equipment.append(new_equip)
            if len(last_equipment) >= num_humans:
                last_equipment.pop(0)
        return exercises

    def build_workout_sequence(self, duration, profile):
        # determine workout format
        workout_type = np.random.randint(3)
        exercise_sequence = []
        if self.profile['warmup']:
            duration -= 2
            exercise_sequence.append(Event(self.make_exercise('Warmup'), 120))

        total_rounds = int(np.floor(duration * 60 / 200))
        total_exercises = total_rounds * 2
        exercises_list = self.sample_exercises(total_exercises, profile)

        def divide_chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i:i + n]

        num_humans = 1 if 'num_humans' not in profile else profile['num_humans']
        #this is reaaly only a 2 human format
        chunksize = 2
        for chunk in divide_chunks(exercises_list, chunksize):
            if len(chunk) < chunksize:
                continue #non multiple number of minutes
            if num_humans == 1:
                for iter in range(2):
                    exercise_sequence.append(Event(chunk[0], 40))
                    exercise_sequence.append(Event(chunk[1], 40))
                    exercise_sequence.append(Event(self.make_exercise('Rest'), 20))
            else:
                for iter in range(2):
                    exercise_sequence.append(Event((chunk[0], chunk[1]), 40))
                    exercise_sequence.append(Event((chunk[1], chunk[0]), 40))
                    exercise_sequence.append(Event(self.make_exercise('Rest'), 20))
        exercise_sequence = exercise_sequence[:-1] #remove final rest


        # if workout_type == 0:
        #     #### 1 min strength 1 min cardio #####
        #     total_rounds = duration // 4
        #     ex_list = self.sample_exercises(total_rounds * [[1, 2, 3, 4], [4, 5]], profile)
        #     for i in range(total_rounds):
        #         exercise_sequence.append((ex_list[2 * i + 0], '60s'))
        #         exercise_sequence.append((ex_list[2 * i + 1], '60s'))
        #         exercise_sequence.append((ex_list[2 * i + 0], '60s'))
        #         exercise_sequence.append((ex_list[2 * i + 1], '60s'))
        # elif workout_type == 1:
        #     # 2x 1 min of 3 types of strength exercises, 1 min cardio
        #     total_rounds = duration // 8
        #     ex_list = self.sample_exercises(total_rounds * [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [4, 5]], profile)
        #     for i in range(total_rounds):
        #         exercise_sequence.append((ex_list[4 * i + 0], '60s'))
        #         exercise_sequence.append((ex_list[4 * i + 1], '60s'))
        #         exercise_sequence.append((ex_list[4 * i + 2], '60s'))
        #         exercise_sequence.append((ex_list[4 * i + 3], '60s'))
        #         exercise_sequence.append((ex_list[4 * i + 0], '60s'))
        #         exercise_sequence.append((ex_list[4 * i + 1], '60s'))
        #         exercise_sequence.append((ex_list[4 * i + 2], '60s'))
        #         exercise_sequence.append((ex_list[4 * i + 3], '60s'))
        # elif workout_type == 2:
        #     # 20 seconds on, 10 seconds rest x 8 for one strength exercise, 1 min crdio'
        #     total_rounds = duration // 5
        #     ex_list = self.sample_exercises([[1, 2, 3, 4], [4, 5]] * total_rounds, profile)
        #     for i in range(total_rounds):
        #         for j in range(8):
        #             exercise_sequence.append((ex_list[2 * i], '20s'))
        #             exercise_sequence.append((self.make_exercise('Rest'), '10s'))
        #         exercise_sequence.append((ex_list[2 * i + 1], '60s'))
        # elif workout_type == 3:
        #     total_rounds = int(np.floor(duration / 4))
        #     #TODO: account for limited equipment
        #     ex_list = self.sample_exercises([[1, 2, 3, 4, 5]] * total_rounds * 2, profile)
        #     for i in range(total_rounds):
        #         ex0 = ex_list[2*i]
        #         ex1 = ex_list[2*i + 1]
        #         exercise_sequence.append(((ex0, ex1), '40s'))
        #         exercise_sequence.append(((ex1, ex0), '40s'))
        #         exercise_sequence.append(((self.make_exercise('Rest'), self.make_exercise('Rest')), '20s'))
        #         exercise_sequence.append(((ex0, ex1), '40s'))
        #         exercise_sequence.append(((ex1, ex0), '40s'))
        #         exercise_sequence.append(((self.make_exercise('Rest'), self.make_exercise('Rest')), '20s'))




        #     #30 reps of each exercise; do full circuit twice
        return exercise_sequence