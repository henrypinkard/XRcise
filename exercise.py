import csv
import numpy as np
import os

def base_dir():
    return os.path.dirname(os.path.realpath(__file__)) + os.sep

class Exercise:

    POSSIBLE_EQUIPMENT = {'TRX': 'trx', 'Weights': 'weights', 'Kettlebells': 'kettlebell', 'Pullup bar': 'pullupbar',
                          'Resistance bands': 'band', 'towel + smooth floor': 'towel'}

    def __init__(self, base_name, equipment=['bodyweight'], paired='', cardio=0):
         self.paired = paired
         self.cardio = cardio
         self.count = 0
         self.equipment = equipment
         self.base_name = base_name

    def get_name(self, available_equipment):
        #do the version of the exercise with trhe equipment thats highest on hierarchy
        hierarchy = ['trx', 'weights', 'kettlebell', 'pullupbar', 'band', 'towel', 'bodyweight']
        hierarchy = [e for e in hierarchy if e in available_equipment] + ['bodyweight']
        for equip in hierarchy:
            if equip in self.equipment:
                return equip + ': ' + self.base_name if equip != 'bodyweight' else self.base_name
        raise Exception('Mismatch with avaialable equipment')

class ExerciseBank:

    def __init__(self, available_equipment):
        self._all_exercises = []
        with open(base_dir() + 'exercises.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            mat = None
            for i, row in enumerate(csv_reader):
                if i == 0:
                    self.muscle_group_categories = [entry for entry in row if entry != '']
                else:
                    name = row[0]
                    equipment_needed = [s.strip().lower() for s in row[1].split(',')]
                    paired = row[2]
                    cardio_score = int(row[3])
                    muscle_groups_binary = np.array([float(f) for f in row[5:]])
                    exercise_possible = False
                    for e in ['bodyweight'] + available_equipment:
                        if e in equipment_needed:
                            exercise_possible = True
                    if exercise_possible:
                        if mat is None:
                            mat = np.reshape(muscle_groups_binary, [-1, 1])
                        else:
                            mat = np.concatenate([mat, np.reshape(muscle_groups_binary, [-1, 1])], axis=1)
                        self._all_exercises.append(Exercise(name, paired=paired, cardio=cardio_score, equipment=equipment_needed))

        self._adjacency_mat = np.zeros((mat.shape[1], mat.shape[1]))
        normed_mat = mat / np.linalg.norm(mat, axis=0)
        for i in range(self._adjacency_mat.shape[0]):
            for j in range(self._adjacency_mat.shape[1]):
                self._adjacency_mat[i, j] = np.dot(normed_mat[:, i], normed_mat[:, j].T)
        # extra similiarty for exact same exercise so it becomes unlikely to be repeated
                self._adjacency_mat[np.diag_indices(mat.shape[1])] += 4

    def filter_by_inclusion_list(self, include_list):
        # filter by included exercises
        mask = np.array([e.base_name in include_list for e in self._all_exercises])
        self._all_exercises = [e for e in self._all_exercises if e.base_name in include_list]
        self._adjacency_mat = self._adjacency_mat[mask, :][:, mask]

    def get_num_valid_exercises(self):
        return len(self._all_exercises)

    def get_exercise(self, index):
        return self._all_exercises[index]



