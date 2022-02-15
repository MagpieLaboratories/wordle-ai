from operator import indexOf
import os
import numpy as np
import json
import random
import itertools

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
_all_possible_words_file = os.path.join(ROOT_DIR, "possible_words.txt")
_all_possible_answers_file = os.path.join(ROOT_DIR, "possible_answers.txt")
_all_possible_words_frequency_file = os.path.join(ROOT_DIR, "word_frequency.txt")
_all_words_freq_json_file = os.path.join(ROOT_DIR, "word_frequency.json")
_first_guess_results = os.path.join(ROOT_DIR, "firstresults.json")
# _first_guess_results2 = os.path.join(ROOT_DIR, "firstresults_2.json")
# _first_guess_results3 = os.path.join(ROOT_DIR, "firstresults_3.json")
# _first_guess_results4 = os.path.join(ROOT_DIR, "firstresults_4.json")
_testjson = os.path.join(ROOT_DIR, "testjson.json")
_pattern_matrices = os.path.join(ROOT_DIR, "pattern_grid.npy")

global_words= []
global_answers=[]

def get_words():
    global global_words
    if len(global_words) > 0:
        return global_words
    words = []
    with open(_all_possible_words_file) as fp:
        for word in fp.readlines():
            words.append(word.strip())
    global_words = words
    return words
    
def get_answers():
    global global_answers
    """
    although the complete list of 5-letter dictionary words is 12k, the list of possible wordle answers is much smaller
    """
    if len(global_answers) > 0:
        return global_answers

    words = []
    with open(_all_possible_answers_file) as fp:
        for word in fp.readlines():
            words.append(word.strip())
    global_answers = words
    return words

def get_words_with_freq():
    with open(_all_words_freq_json_file) as fp:
        return json.loads(fp)

def generate_word_frequency():
    word_freq = dict()
    with open(_all_possible_words_frequency_file) as fp:
        for line in fp.readlines():
            split = line.split(',')
            
            word_freq[split[0].strip()] = split[1].strip()
    with open(_all_words_freq_json_file, 'w') as fp:
        json.dump(word_freq, fp)

def letter_to_int(letter):
    return int(ord(letter)-97)

def int_to_letter(int):
    return chr(97+int)

def word_to_int_arr(word):
    intarr = np.zeros(5, dtype=int)
    for pos, char in enumerate(word):
        intarr[pos] = letter_to_int(char)
    return intarr

def int_arr_to_word(intarr):
    word = ""
    for int in intarr:
        word = word + int_to_letter(int)
    return word


class WordleBoard():
    def __init__(self, Solution = None, hardmode = False):
        self.internal_test = False
        self.guesses = []
        self.possible_words = self.get_words()
        self.possible_answers = self.get_answers()
        self.solution_int = Solution if Solution else random.choice(self.possible_answers)
        self.solution = int_arr_to_word(self.solution_int)
        self.score = 0
        self.solution_space = [[x for x in range(26)] for y in range(5)] ##ints not letters
        self.contained_letters = []
        self.excluded_letters = []
        self.guessed_letters = []
        self.pattern = []
        self.hard_mode = hardmode

    def get_words(self):
        words = get_words()
        word_ints = []
        for word in words:
            word_ints.append(word_to_int_arr(word))
        return word_ints

    def get_answers(self):
        words = get_answers()
        word_ints = []
        for word in words:
            word_ints.append(word_to_int_arr(word))
        return word_ints
    
    def get_readable_possible_answers(self):
        if len(self.guesses) == 0:
            pass
        else:
            for word in self.possible_answers:
                if not self.guess_is_valid(word):
                    self.possible_answers.remove(word)

        words = []
        for word in self.possible_answers:
            words.append(int_arr_to_word(word))
        return words

    def get_solution(self):
        return self.solution
    
    def get_score(self):
        return self.score
    
    def set_solution(self, solution):
        solution = solution.lower()
        self.solution = solution
        self.solution_int = word_to_int_arr(solution)
    
    def add_guess(self, guess):
        self.guesses.append(guess)
        guessed_word_index = {}

        for pos, letter in enumerate(guess):
            if letter in guessed_word_index:
                guessed_word_index[letter] += 1
            else:
                guessed_word_index[letter] = 1
            ##if letter not yet guessed, or number of guessed instances of this letter is fewer than the guessed word index for that letter, add letter as a guess
            if letter not in self.guessed_letters or self.guessed_letters.count(letter) < guessed_word_index[letter]:
                self.guessed_letters.append(letter)
    
    def guess_is_valid(self, guess, contained_letters = None, excluded_letters = None, solution_space = None, ):
        """returns true if guess does not break current solution space logic"""
        guess_letters = np.array(np.copy(self.contained_letters if contained_letters is None else contained_letters)).tolist()
        exclets = self.excluded_letters if excluded_letters is None else excluded_letters
        exclets_counter = []
        solspace = self.solution_space if solution_space is None else solution_space

        for position, letter in enumerate(guess):
            if letter in guess_letters:
                # guess_letters = np.delete(guess_letters, letter)
                guess_letters.remove(letter)
            #are we guessing a letter we know is not in the word?
            if letter in exclets:
                if letter in contained_letters:
                    if exclets_counter.count(letter) >= contained_letters.count(letter):
                        return False
                    else:
                        exclets_counter.append(letter)
                else:
                    return False
            #are we guessing a letter in a position which is proven false?
            if letter not in solspace[position] :
                return False
        #did we forget to guess a known included letter? if so, we need to count this as a missed guess - the computer knows it is wrong
        if len(guess_letters) > 0:
            return False
        return True

    def get_current_guess_space_ints(self):
        if len(self.guesses) == 0:
            return self.possible_words
        else:
            self.possible_words = [x for x in self.possible_words if self.guess_is_valid(x)]
        return self.possible_words

    def get_current_guess_space(self):
        if self.hard_mode == False:
            return self.get_max_guess_space()
        if len(self.guesses) == 0:
            return [ int_arr_to_word(x) for x in self.possible_words]
        else:
            self.possible_words = [ x for x in self.possible_words if self.guess_is_valid(x)]
        return [ int_arr_to_word(x) for x in self.possible_words ]
        
    def get_current_valid_guess_count(self):
        if len(self.guesses) == 0:
            return len(self.possible_words)
        else:
            self.possible_words = [ x for x in self.possible_words if self.guess_is_valid(x)]
        return len([ int_arr_to_word(x) for x in self.possible_words ])


    def get_max_guess_space(self):
        return get_words()

    def get_current_solution_space_ints(self):
        if len(self.guesses) == 0:
            return self.possible_answers
        else:
            self.possible_answers = [x for x in self.possible_answers if self.guess_is_valid(x)]
        return self.possible_answers

    def get_current_solution_space(self):
        if len(self.guesses) == 0:
            return self.possible_answers
        else:
            self.possible_answers = [ int_arr_to_word(x) for x in self.possible_answers if self.guess_is_valid(x)]
        return self.possible_answers
    
    def size_of_current_solution_space(self):
        """current number of possible valid guesses"""
        if len(self.guesses) == 0:
            return len(self.possible_answers)
        else:
            self.possible_answers = [x for x in self.possible_answers if self.guess_is_valid(x)]
        return len(self.possible_answers)


    def get_words_for_solution_space(self, all_words = True, solutionspaceoverride = None, excludedoverride = None, containedOverride = None):
        words = []
        if all_words:
            words = [ x for x in self.possible_words if self.guess_is_valid(x, containedOverride, excludedoverride, solutionspaceoverride)]
        else:
            words = [ x for x in self.possible_answers if self.guess_is_valid(x, containedOverride, excludedoverride, solutionspaceoverride)]
        return words

    def copy_sol_array(self):
        newarr = [0 for x in range(5)]
        for pos, n in enumerate(self.solution_space):
            newarr[pos] = np.copy(n).tolist()
        return newarr

    def find_outcome_space_for_guess(self, guess, all_words = True, currentoutcomes = {}):
        outcomespace = self.find_possible_outcomes_for_guess(guess, all_words, currentoutcomes)
        outcomelengths = {}
        for key in outcomespace:
            if isinstance(key, str):
                outcomelengths[key] = outcomespace[key]
            else:
                outcomelengths[key] = len(outcomespace[key])
        return outcomelengths

    def find_possible_outcomes_for_guess(self, guess, all_words = True, currentoutcomes = {}):
        """returns the solution space and probability for a guess based on existing information"""
        possible_outcomes = currentoutcomes

        ##0 green, 1 orange, 2 black
        for i in [0,1,2]:
            for j in [0,1,2]:
                for k in [0,1,2]:
                    for l in [0,1,2]:
                        for m in [0,1,2]:
                            if str(i+3*j+9*k+27*l+81*m) in possible_outcomes:
                                continue

                            solution_space_Copy = self.copy_sol_array()
                            contained_letters_copy = np.copy(self.contained_letters).tolist()
                            ##(l == 1 and m == 2) or (l == 2 and m == 1) or (l == 1 and m == 1) or (l == 2 and m == 2) or (l == 0 and m == 2) or (l == 2 and m == 0)
                            excluded_letters_copy = np.copy(self.excluded_letters).tolist()
                            
                            guessed_word_index = {}
                            contained_letters_copy_this_guess = []
                            excluded_letters_copy_this_guess = []
                            # possible_outcomes[i+3*j+9*k*27*l+81*m] = []
                            valid = True
                            ##only in hard mode can it be invalid, without hard mode we can guess anything and then work out if its possible at the end

                            for pos, x in enumerate([i,j,k,l,m]):
                                
                                if guess[pos] in guessed_word_index:
                                    guessed_word_index[guess[pos]] += 1
                                else:
                                    guessed_word_index[guess[pos]] = 1

                                if x == 0: #green
                                    contained_letters_copy_this_guess.append(guess[pos])
                                    ##is this letter in the solution space position?
                                    if guess[pos] in solution_space_Copy[pos]: #and guess[pos] not in excluded_letters_copy: #not true - repeated letter can occur after correct placement
                                        ##we need to update the solution space to be only this letter
                                        solution_space_Copy[pos] = [guess[pos]]
                                    ##if not then there are no valid words. e.g. if s is not in the word at all then sXXXX is an impossible guess
                                    else:
                                        valid = False
                                        break
                                elif x == 1: #yellow
                                    contained_letters_copy_this_guess.append(guess[pos])
                                    ##is this letter not in the excluded letters? OR is it definitely in the included letters? both are valid yellows
                                    ##remember that a 2nd letter can be excluded while the first one is still valid (and contained)
                                    if guess[pos] not in excluded_letters_copy or guess[pos] in contained_letters_copy:
                                        if(excluded_letters_copy.count(guess[pos]) > contained_letters_copy.count(guess[pos]) ):
                                            valid = False
                                            break
                                        ##this position in the word cannot be this letter - remove it (it is not green)
                                        if guess[pos] in solution_space_Copy[pos]:
                                            solution_space_Copy[pos].remove(guess[pos])
                                        # ##but the overall word must contain the letter
                                        # if guess[pos] not in contained_letters_copy or contained_letters_copy.count(guess[pos]) < guessed_word_index[guess[pos]]:
                                        #     contained_letters_copy_this_guess.append(guess[pos])
                                    ##if not - then its an impossible guess. its excluded without being included. no possible words.
                                    else:
                                        valid = False
                                        break
                                elif x == 2: #black
                                    excluded_letters_copy_this_guess.append(guess[pos])
                                    ##is this an excluded letter? if so it is immediately valid as a black letter
                                    ##else, if it an included letter but its guess index is greater than 1 if so it can also be valid as a black letter?
                                    if guess[pos] in excluded_letters_copy :
                                        ##remove this letter as a possibility in every letter space after pos if guessed_word_index is more than 1
                                        ##we cannot do so before pos because that could interfere with an earlier letter guess in the solution space
                                        for nposition, n in enumerate(solution_space_Copy):
                                            if guessed_word_index[guess[pos]] > 1 and nposition < pos:
                                                pass
                                            else:
                                                if guess[pos] in n:
                                                    n.remove(guess[pos])
                                    
                                        ##and include it as an excluded letter
                                        #     excluded_letters_copy_this_guess.append(guess[pos])
                                    else:
                                        if guess[pos] in contained_letters_copy :
                                            if guessed_word_index[guess[pos]] > contained_letters_copy.count(guess[pos]):
                                                ##remove this letter as a possibility in every letter space after pos if guessed_word_index is more than 1
                                                ##we cannot do so before pos because that could interfere with an earlier letter guess in the solution space
                                                for nposition, n in enumerate(solution_space_Copy):
                                                    if guessed_word_index[guess[pos]] > 1 and nposition < pos:
                                                        pass
                                                    else:
                                                        if guess[pos] in n:
                                                            n.remove(guess[pos])
                                                # ##and include it as an excluded letter
                                                # if guess[pos] not in excluded_letters_copy:
                                                #     excluded_letters_copy_this_guess.append(guess[pos])
                                            else:
                                                valid = False
                                                break
                                        else:
                                            ##remove this letter as a possibility in every letter space after pos if guessed_word_index is more than 1
                                            for nposition, n in enumerate(solution_space_Copy):
                                                
                                                ##we cannot do so before pos because that could interfere with an earlier letter guess in the solution space
                                                if guessed_word_index[guess[pos]] > 1 and nposition < pos:
                                                    pass
                                                else:
                                                    ##we also cannot do so after pos for double/triple because e.g. ABYES --> 00020 for ABYSS --> 00000
                                                    # ##the first S is black, but because the second one is not we can't remove it 
                                                    if guess.tolist().count(guess[pos]) < 2 and nposition > pos:
                                                        if guess[pos] in n:
                                                            n.remove(guess[pos])
                                                    elif nposition == pos:
                                                        if guess[pos] in n:
                                                            n.remove(guess[pos])

                                            ##and include it as an excluded letter
                                            if guess[pos] not in excluded_letters_copy:
                                                excluded_letters_copy.append(guess[pos])
                                ##combine lists
                                for item in contained_letters_copy_this_guess:
                                    if item not in contained_letters_copy:
                                        contained_letters_copy.append(item)
                                    else:
                                        if contained_letters_copy_this_guess.count(item) > contained_letters_copy.count(item):
                                            contained_letters_copy.append(item)
                                for item in excluded_letters_copy_this_guess:
                                    if item not in excluded_letters_copy:
                                        excluded_letters_copy.append(item)
                                    else:
                                        if excluded_letters_copy_this_guess.count(item) > excluded_letters_copy.count(item):
                                            excluded_letters_copy.append(item)

                            ##calc
                            if valid:
                                possible_outcomes[i+3*j+9*k+27*l+81*m] = self.get_words_for_solution_space(all_words, solution_space_Copy, excluded_letters_copy, contained_letters_copy)
        return possible_outcomes


    def make_guess(self, guess):
        """returns true if guess is correct, else updates internal state of class to reflect guess and returns False"""
        self.score += 1
        if guess == self.solution:
            return True
        else:
            guess_int = np.array(word_to_int_arr(guess))
            self.add_guess(guess_int)
            #each guess should cut down on solution space
            for position, letter in enumerate(guess_int):
                ##green match -> solution space on this index has only 1 value
                if position in np.where(self.solution_int == letter)[0]:
                    if letter not in self.contained_letters:
                        self.contained_letters.append(letter)
                    self.solution_space[position] = [letter]
                    pass
                #yellow -> solution space on this index has lost 1 value, update contained letters
                elif letter in self.solution_int: 
                    if letter not in self.contained_letters:
                        self.contained_letters.append(letter)
                    if letter in self.solution_space[position]:
                        self.solution_space[position].remove(letter)
                ##not in word -> solution space on all indices has lost this value
                else:
                    self.excluded_letters.append(letter)
                    for n in self.solution_space:
                        if letter in n:
                            n.remove(letter)
                    pass
            return False

global_words = []
global_answers = []

if __name__ == "__main__":
    test = WordleBoard()
    test.set_solution('cynic') ##or whatever
    guesses = []
    finish = False

    while not finish:
        scores = {}
        with open(_first_guess_results) as fp:
            scores = json.loads(fp.read())
        
        current_guess_space_total = test.get_current_valid_guess_count()
        best_score = 9999
        best_word = ""

        possible_guesses = test.get_current_guess_space()
        count = 0
        skip = 62
        for guess_word in possible_guesses:
            count += 1
            if skip > count:
                continue

            if sum(scores[guess_word].values()) != current_guess_space_total:
            # if count < 251:
                print(f"Updating ${guess_word}. Previous max performance: {max(scores[guess_word].values())} with total: {sum(scores[guess_word].values())}")
                guess_result = test.find_outcome_space_for_guess(word_to_int_arr(guess_word), True)
                max_value = max(guess_result.values())
                scores[guess_word] = guess_result
                if sum(guess_result.values()) != current_guess_space_total:
                    ##double letter issues
                    print(f"error! guess total {sum(guess_result.values())} is not equal to valid guess count: {current_guess_space_total}")
                print(f" {guess_word} performed at: {max_value}")

                if max_value < best_score:
                    best_word = guess_word
                    best_score = max_value 
                    print(f"! _ new best word: {best_word} with score: {best_score}")
                
            if count%10 == 0 and len(guesses) == 0:
                print(f'saving after {count} results')
                with open(_first_guess_results, 'w') as fp:
                    json.dump(scores, fp)
        
        print(f'saving after {count} results')
        with open(_first_guess_results, 'w') as fp:
            json.dump(scores, fp)

        stop = True
        guesses.append(best_word)

        finish = test.make_guess(best_word)
    
    print('done')
    print(f'score: {test.get_score}')


