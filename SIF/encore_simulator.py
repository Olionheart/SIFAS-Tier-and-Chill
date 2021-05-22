"""
@author: Olionheart (IGN:『TC』Olion♡)
Encore Simulator 1.1
Semi-generalized encore simulator for School Idol Festival (SIF)
Supports teams comprised of note-based scorers, amps, encores, and sru
Not tested yet but will be tested with limited experimental results and previous version of simulator - should work fine for "standard" encore teams
Assumption:
- uniform note density and full combo
- scorer is always placed to the right of amp/sru and is equipped with a charm
- activation order on same note: scorer/sru from right-to-left order, encore, amp
- when multiple skills including amp activates on same note, there is a 50/50 chance for the amp to be consumed by amp activation vs right-to-left non-amp/encore
  - this coin flip is done once at song start and used throughout the song (why, klab, why)
- if (non-amp) skills activate on the same note as encore (particularly scorer), the right most (non-amp/encore) will be copied by the encore (most likely the scorer, if activated)
  - if no skill activate on the same note as encore (i.e. scorer did not proc), encore will most likely not proc or be useless in that cycle
  - if the last activated skill was encore, it cannot be copied and encore will not proc
  - if the last activated skill was amp, the encore will consume the amp (for no benefit) and output the previously used amp, resulting in essentially nothing
  - if the last activated skill was sru, the encore cannot activate it again if sru is already active (thus encore will not proc)
  - it is very unlikely that the last activated skill will be sru and sru is inactive (unless you're really unlucky or note density is very low) but if such is the case, encore will re-activate sru
  - on the very rare case that last cycle scorer activated (and no encore activated in that cycle) and no other skills activated between the cycle, the encores can copy the scorer from last cycle
- sru activation condition
  - cannot activate while sru is active
  - if note xn-th appears during the duration of sru (where x = activation condition), there is a chance that sru will renew itself upon ending for another full duration
  - even if more than one xn-th note appears during the duration of sru, it can only try to activate once at the end of its duration
  - when sru is not active, sru can proc on xn-th note even if it didn't end on xn-th note
  - for example, suppose that 32n sru ended on note 60, it has a chance to proc again on note 64
- both sru and amp do not affect things that activate on same note
- sru never ends exactly on a note
- encores are placed to the left of amps so that encore will not repeat amp if actual amp is to activate (i.e. so as to not waste the amp in this specific case) - unconfirmed speculation by pumick
- when in doubt just coinflip like klab and it'll probably turn out close :DiaLUL: - DataGryphon, 2021 
Based on discussion in discord.gg/sif #sif_chat with DataGryphon and Pumick
Bug Fix(es):
- #1, 4 May 2021, multiply sru length by note density upon activation
- #2, 4 May 2021, fixed team tap multiplier (divide by 9, assume even note distribution)
- #3, 4 May 2021, added a catch-all parameter tap_score_modifier
Update(s):
- #1, 22 May 2021, added loadout and skill_proc_modifier
- #2, 22 May 2021, the simulation now supports note-based scorers that doesn't sync with encore (encore still needs to sync with each other) *** ignores amp-stealing of amp on amp-scorer without encore note ***
- #3, 23 May 2021, huge overhaul, v.1.1 - the simulation should now support any note-based scorers (not necessarily just one scorer), multiple amps, multiple sru, and encores of different note (probably very bad lol)
Note density look-up (provided by Gryphon): https://docs.google.com/spreadsheets/d/1D48qaGuk4cjh8nbZkpR3NqGjO57jhKwkfS6Chqg7rV4/
"""
import enum
import numpy as np
import matplotlib.pyplot as plt

suppress_distribution_plot = False

# song parameter
# TODO: load song parameter from a txt or json file
total_note = 840 # note count of the song of interest (porkbun's default for master is 698)
song_attribute = 1 # 0 if smile, 1 if pure, 2 if cool
note_density = 7.49 # average note density
tap_score_modifier = 1.026 * 1.1 # a catch-all parameter to help you tune the calculated tap score to match what you actually get when you turn skills off
skill_proc_modifier = 1.1 # for chalfes/medfes
perfect_rate = 90 # tap perfect rate

# select loadout
loadout_profile = 0 # so you can configure a few teams and change just one line to switch
loadout_name = "default"

# team tap-related parameter
team_attribute = [40022, 80329, 40312] # a list of total team attribute (smile/pure/cool) that is relevant to the song
team_tap_mult = [2, 6, 1] # a list of total team multiplier (1 for each card that match song attribute and 1 for each card that match song group) for each attribute

# team skill-related parameter
encore_note = [25] # a list of note count of encore, no duplicate (i.e. if you have 5x 25n encores, write [25])
score_note = [25] # a list of note count of each scorer, from right to left
amp_note = [20, 22] # a list of note count of each amp, from right to left
sru_note = [32] # a list of note count of each sru, from right to left (assumes that sru is to the left of all scorers)
encore_chance = [[42, 42, 42, 42, 38]] # list of list of activation rate of each encore, in the same order as encore_note
score_chance = [56] # list of activation rate of each scorer, from right to left
amp_chance = [66, 72] # list of activation rate of each amp, from right to left
sru_chance = [40] # list of activation rate of each sru, from right to left (assumes that sru is to the left of all scorers)
# magnitude and length is given as a list where the first element is its base skill level and last element is the max value
score_mag = [[4435, 4875, 5760, 7090, 8860, 9370, 10385, 11915, 13955]] # list of list of magnitude of each scorer
amp_mag = [8, 8] # list of skill level of each amp
sru_mag = [[22, 24, 26, 31, 39, 49, 54, 64, 79, 98]] # list of list of magnitude of each sru
sru_len = [[7.5, 8]] # list of list of duration of each sru

assert len(encore_note) == len(encore_chance)
assert len(score_note) == len(score_chance)
assert len(score_note) == len(score_mag)
assert len(amp_note) == len(amp_chance)
assert len(amp_note) == len(amp_mag)
assert len(sru_note) == len(sru_chance)
assert len(sru_note) == len(sru_mag)
assert len(sru_note) == len(sru_len)

# Do NOT edit (unless you know what you're doing)
class SkillType(enum.Enum):
    ENCORE = 0
    SCORE = 1
    AMP = 2
    SRU = 3
    NONE = 4
 
class GameState:
    def __init__(self, sru_count):
        self.score = 0 # skill-based score
        self.amp_coin_flip = rng(50) # if true, amp will steal amp charge on tie with scorer/sru
        self.last_skill = SkillType.NONE # last activated skill, for encore repeat
        self.last_mag = 0 # associated magnitude, store the score if scorer, store (mag, len) if sru, store 0 if amp/encore (not used because encore cannot repeat them)
        self.curr_amp = 0 # current amp charge
        self.sru_active = False # True if there is active sru coverage, False otherwise
        self.sru_mag = 1 # skill rate amplification - 1 if sru is not active, 1 + x / 100 if sru of magnitude x is active
        self.sru_covered = [False] * sru_count # track self-covered state of each sru independently
        self.sru_end_note = 0 # track the note that current sru will end on, 0 if sru is not active
        self.sru_count = sru_count # used to reset sru_covered

    # get final score
    def get_score(self):
        return self.score * 2.5 # resolve charm multiplier here ***

    # call to check the current amp charge
    def get_amp(self):
        return self.curr_amp

    # call when amp activates
    def proc_amp(self, new_amp_lvl):
        self.curr_amp = new_amp_lvl
        self.last_skill = SkillType.AMP
        self.last_mag = 0
        # does not need to clear amp

    # call when scorer activate
    def proc_score(self, score):
        self.score += score
        self.last_skill = SkillType.SCORE
        self.last_mag = score
        self.curr_amp = 0 # consumes amp

    # call when encore(s) activate
    # num_proc = number of encores that activate
    # scorer_bypass_mag = the magnitude of the scorer that activates on the same note, 0 if no scorer activates on the same note
    # curr_note = the current note, in case the encore repeats SRU
    def proc_encore(self, num_proc, scorer_bypass_mag, curr_note):
        if scorer_bypass_mag == 0:
            if self.last_skill == SkillType.SCORE:
                self.score += self.last_mag * num_proc
                self.curr_amp = 0 # consumes amp (sadly)
            elif self.last_skill == SkillType.SRU and not self.sru_active:
                # if SRU is already active, this will be skipped because encore cannot repeat SRU when it is already active
                self.sru_active = True
                self.sru_mag = self.last_mag[0]
                self.sru_end_note = curr_note + self.last_mag[1] * note_density
                self.sru_covered = [False] * self.sru_count
                self.curr_amp = 0 # consumes amp (sadly)
            # else, last_skill is either encore, amp, or none
            # in this case, do nothing because encore or none can't be repeated
            # while repeating amp results in essentially nothing
        else:
            self.score += scorer_bypass_mag * num_proc
            self.curr_amp = 0 # consumes amp - should be redundant, but making sure
        self.last_skill = SkillType.ENCORE
        self.last_mag = 0

    # call when sru procs, either on note or renew
    def proc_sru(self, mag, len, curr_note):
        self.sru_active = True
        self.sru_mag = mag
        self.sru_end_note = curr_note + len * note_density
        self.sru_covered = [False] * self.sru_count
        self.last_skill = SkillType.SRU
        self.last_mag = (mag, len)
        self.curr_amp = 0 # consumtes amp

    # call to reset sru status when an sru ends (and does not renew)
    def sru_end(self):
        self.sru_active = False
        self.sru_mag = 1
        self.sru_end_note = 0
        self.sru_covered = [False] * self.sru_count

    # call when sru_active and activation note of the sru passes (i.e. self-coverage)
    def sru_self_cover(self, sru_index):
        self.sru_self_cover[sru_index] = True

    # call to determine if sru will renew itself
    # return the index of the sru that will renew the sru state
    # if no sru will proc, return -1
    def rng_sru_self_coverage(self):
        for index in range(self.sru_count):
            if self.sru_self_cover[index] and rng(sru_chance[index]):
                return index
        return -1

def rng(chance):
    chance *= skill_proc_modifier
    if chance > 100:
        return True
    if np.random.binomial(1, chance/100) == 1:
        return True
    return False

def num_encore_proc(chance_list, rate_mag):
    num_proc = 0
    for chance in chance_list:
        if rng(chance * rate_mag):
            num_proc += 1
    return num_proc

def get_amp_level(sl):
    if sl >= 16:
        return 12
    if sl >= 8:
        return sl - 4
    if sl == 7:
        return 4
    if sl >= 4:
        return 3
    return 2

def amp(skill_power_list, amp_level):
    if amp_level + 1 > len(skill_power_list):
        return skill_power_list[-1]
    return skill_power_list[amp_level]

def generate_spell_queue(note_count, skill_note):
    spell_queue = list()
    for note in skill_note:
        i = 1
        while i * note <= note_count:
            spell_queue.append(i * note)
            i += 1
    spell_queue = list(set(spell_queue))
    spell_queue.sort()
    return spell_queue

def schedule_amp(note, active_sru_mag):
    for i in range(len(amp_note)):
        if (note % amp_note[i] == 0) and rng(amp_chance[i] * active_sru_mag):
            return i
    return -1

def schedule_sru(note, is_sru_active):
    if is_sru_active:
        return -1
    for i in range(len(sru_note)):
        if (note % sru_note[i] == 0) and rng(sru_chance[i]):
            return i
    return -1

def schedule_encore(note, active_sru_mag):
    count = 0
    for i in range(len(encore_note)):
        if note % encore_note == 0:
            count += num_encore_proc(encore_chance[i], active_sru_mag)
    return count

def simulate(spell_queue):
    game_state = GameState(len(sru_note))
    for note in spell_queue:
        # resolve expired (or renewed) sru
        if game_state.sru_active and note > game_state.sru_end_note:
            # sru ends prior to this note (we assume that sru does not end on the exact frame of the note)
            # check if sru will renew itself
            sru_index = game_state.rng_sru_self_coverage()
            if sru_index != -1:
                new_sru_mag = 1 + amp(sru_mag[sru_index], game_state.get_amp()) / 100
                new_sru_len = amp(sru_len[sru_index], game_state.get_amp())
                game_state.proc_sru(new_sru_mag, new_sru_len, game_state.sru_end_note)
            else:
                game_state.sru_end()

        # resolve sru self-coverage
        if game_state.sru_active:
            for i in range(len(sru_note)):
                if note % sru_note[i] == 0:
                    game_state.sru_self_cover(i)

        # schedule skills (score > sru > encore > amp)
        score_schedule = [((note % score_note[i] == 0) and rng(score_chance[i] * game_state.sru_mag)) for i in range(len(score_note))] # list of boolean if each scorer will activate on this note
        sru_schedule = schedule_sru(note, game_state.sru_active) # index of the sru that will activate on this note, -1 if no sru will activate
        encore_schedule = schedule_encore(note, game_state.sru_mag) # number of encores to activate on this note
        amp_schedule = schedule_amp(note, game_state.sru_mag) # index of the amp that will activate on this note, -1 if no amp will activate

        amp_stealing = game_state.amp_coin_flip and (amp_schedule != -1) # amp stealing happens if amp will proc and coin flip is true
        amp_amp_power = game_state.get_amp() # is used if and only if amp_stealing is true - save amp power for the amp and clear current amp charge
        if amp_stealing: # clear current amp charge if amp stealing
            game_state.curr_amp = 0
        first_scorer_proc = True # for setting scorer bypass on encore
        scorer_bypass_mag = 0

        # resolve skill procs
        # resolve scorer
        for i in range(len(score_note)):
            if score_schedule[i]:
                magnitude = amp(score_mag[i], game_state.get_amp())
                if first_scorer_proc:
                    scorer_bypass_mag = magnitude
                    first_scorer_proc = False
                game_state.proc_score(magnitude)

        # resolve sru
        if sru_schedule != -1:
            magnitude = amp(sru_mag[sru_schedule], game_state.get_amp())
            length = amp(sru_len[sru_schedule], game_state.get_amp())
            game_state.proc_sru(magnitude, length, note)   

        # resolve encore
        if encore_schedule != 0:
            game_state.proc_encore(encore_schedule, scorer_bypass_mag, note)

        # resolve amp
        if amp_schedule != -1:
            if not amp_stealing:
                amp_amp_power = game_state.get_amp()
            game_state.proc_amp(get_amp_level(amp_mag[amp_schedule] + amp_amp_power))

    return game_state.get_score()

def get_tap_score(note_count, team_power, team_bonus, accuracy):
    note_mult = 0
    for note in range(note_count):
        if note < 50:
            note_mult += 1
        elif note < 100:
            note_mult += 1.1
        elif note < 200:
            note_mult += 1.15
        elif note < 400:
            note_mult += 1.2
        elif note < 600:
            note_mult += 1.25
        elif note < 800:
            note_mult += 1.3
        else:
            note_mult += 1.35
    return 0.0125 * (0.88 + 0.12 * accuracy / 100) * team_power * (1 + 0.1 * team_bonus / 9) * note_mult

if __name__ == "__main__":
    spell_queue = generate_spell_queue(total_note, set(encore_note + score_note + amp_note + sru_note))
    tap_score = get_tap_score(total_note, team_attribute[song_attribute], team_tap_mult[song_attribute], perfect_rate) * tap_score_modifier
    simulated_score = list()
    for simulation_round in range(10000):
        simulated_score.append(simulate(spell_queue) + tap_score)

    if not suppress_distribution_plot:
        plt.hist(simulated_score, 50)
        plt.show()

    print("Simulation Result")
    print("Loadout:", loadout_profile)
    print("Name:", loadout_name)
    print("Tap Score:", tap_score)
    print("Mean Score:", np.mean(simulated_score))
    print("Standard Deviation:", np.std(simulated_score))
    print("95-th Percentile Score:", np.percentile(simulated_score, 95))
    print("99-th Percentile Score:", np.percentile(simulated_score, 99))
    print("0.01% High Score:", max(simulated_score))
