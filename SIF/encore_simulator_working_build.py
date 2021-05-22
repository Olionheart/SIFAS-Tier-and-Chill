"""
@author: Olionheart
Encore Simulator 1.0
Not optimized or generalized!
Status: just completed implementation - not tested with experimental results yet!
Supports standard scorer encore teams only
Assumption:
- uniform note density and full combo
- team has 5 encorer + 1 scorer of same note activation, 2 amps, and 1 sru
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
- when in doubt just coinflip like klab and it'll probably turn out close :DiaLUL: - DataGryphon, 2021 
Based on discussion in discord.gg/sif #sif_chat with DataGryphon and Pumick
Bug Fix(es):
- #1, 4 May 2021, multiply sru length by note density upon activation
- #2, 4 May 2021, fixed team tap multiplier (divide by 9, assume even note distribution)
- #3, 4 May 2021, added a catch-all parameter tap_score_modifier
Update(s):
- #1, 22 May 2021, added loadout and skill_proc_modifier
- #2, 22 May 2021, the simulation now supports note-based scorers that doesn't sync with encore (encore still needs to sync with each other) *** ignores amp-stealing of amp on amp-scorer without encore note ***
Note density look-up: https://docs.google.com/spreadsheets/d/1D48qaGuk4cjh8nbZkpR3NqGjO57jhKwkfS6Chqg7rV4/
"""
import numpy as np
import matplotlib.pyplot as plt

# Edit parameters here
total_note = 840 # note count of the song of interest (porkbun's default for master is 698)
note_density = 7.49 # average note density
team_tap_power = 80329 # total team attribute (smile/pure/cool) that is relevant to the song
team_tap_mult = 6 # total team multiplier (1 for each card that match song attribute and 1 for each card that match song group)
tap_score_modifier = 1.026 * 1.1 # a catch-all parameter to help you tune the calculated tap score to match what you actually get when you turn skills off
skill_proc_modifier = 1.1 # for chalfes/medfes
perfect_rate = 90 # tap perfect rate
loadout_profile = 0 # so you can configure a few teams and change just one line to switch
loadout_name = "default"

# default team parameters (i.e. loadout 0)
encore_note = 25 # note count of encore
scorer_note = 25 # note count of scorer (ideally should match the encore)
amp1_note = 20 # note count of 1st amp
amp2_note = 22 # note count of 2nd amp (2nd amp is to the right of 1st amp, in case both are not sl8)
sru_note = 32 # note count of sru
encore_chance = [42, 42, 42, 42, 38] # list of your encore activation chance, should be of length 5
amp1_chance = 66 # activation chance of 1st amp
amp2_chance = 72 # activation chance of 2nd amp
scorer_chance = 56 # activation chance of scorer
sru_chance = 40 # activation chance of sru
amp1_sl = 8 # skill level of 1st amp
amp2_sl = 8 # skill level of 2nd amp
# magnitude and length is given as a list where the first element is its base skill level and last element is the max value
scorer_mag = [4435, 4875, 5760, 7090, 8860, 9370, 10385, 11915, 13955] # score gain from scorer, pre-charm
sru_mag = [22, 24, 26, 31, 39, 49, 54, 64, 79, 98] # skill chance up of sru
sru_len = [7.5, 8] # skill duration of sru

# replace eli sru with maki sru
if loadout_profile == 2:
    team_tap_power = 103438
    sru_chance = 42 # activation chance of sru
    sru_mag = [27, 29, 32, 37, 44, 55, 60, 70, 86, 106] # skill chance up of sru
    sru_len = [5.5, 6] # skill duration of sru
    team_tap_mult = 14

# eli sru maxed
if loadout_profile == 3:
    team_tap_power = 94453
    sru_chance = 43 # activation chance of sru
    sru_mag = [24, 26, 31, 39, 49, 54, 64, 79, 98] # skill chance up of sru
    sru_len = [8] # skill duration of sru
    team_tap_mult = 13
    encore_chance = [42, 42, 42, 46, 46]

# eli sru maxed, replace bokuhika maki with soreboku
if loadout_profile == 4:
    team_tap_power = 94453
    sru_chance = 43 # activation chance of sru
    sru_mag = [24, 26, 31, 39, 49, 54, 64, 79, 98] # skill chance up of sru
    sru_len = [8] # skill duration of sru
    team_tap_mult = 13
    amp1_note = 21
    amp1_chance = 72
    encore_chance = [42, 42, 42, 46, 46]

# eli sru maxed, upgrade encore instead of new amp
if loadout_profile == 5:
    team_tap_power = 94453
    sru_chance = 43 # activation chance of sru
    sru_mag = [24, 26, 31, 39, 49, 54, 64, 79, 98] # skill chance up of sru
    sru_len = [8] # skill duration of sru
    team_tap_mult = 13
    encore_chance = [50, 50, 46, 46, 46]

# marucore with zodiac maki
if loadout_profile == 6:
    team_tap_power = 80507
    team_tap_mult = 11
    encore_note = 26 # note count of encore
    scorer_note = 26
    encore_chance = [40, 40, 40, 40, 40] # list of your encore activation chance, should be of length 5
    scorer_chance = 64 # activation chance of scorer
    amp1_sl = 8 # skill level of 1st amp
    amp2_sl = 8 # skill level of 2nd amp
    # magnitude and length is given as a list where the first element is its base skill level and last element is the max value
    scorer_mag = [4025, 4430, 5240, 6455, 8070, 8535, 9465, 10855, 12710] # score gain from scorer, pre-charm

# elicore 3 unity 2 soreboku
if loadout_profile == 7:
    team_tap_power = 68945
    team_tap_mult = 4
    encore_chance = [42, 42, 38, 38, 38]

# elicore 2 unity 3 soreboku
if loadout_profile == 8:
    team_tap_power = 65961
    team_tap_mult = 3
    encore_chance = [42, 42, 42, 38, 38]

# elicore 1 unity 4 soreboku
if loadout_profile == 9:
    team_tap_power = 62859
    team_tap_mult = 2
    encore_chance = [42, 42, 42, 42, 38]

# elicore 10 mic
if loadout_profile == 10:
    loadout_name = "elicore 10 mic"
    team_tap_power = 94453
    sru_chance = 43 # activation chance of sru
    sru_mag = [24, 26, 31, 39, 49, 54, 64, 79, 98] # skill chance up of sru
    sru_len = [8] # skill duration of sru
    team_tap_mult = 13
    encore_chance = [54, 54, 54, 54, 54]


# test: cheer rin 30n scorer + panacore 30n
if loadout_profile == 11:
    loadout_name = "15n/30n panacore test"
    encore_note = 30 # note count of scorer and encore
    scorer_note = 15 # SPECIAL: 15n scorer and 30n amp case (or any case where scorer has exactly half the note requirement of encorer)
    amp1_note = 21 # note count of 1st amp
    amp2_note = 22 # note count of 2nd amp (2nd amp is to the right of 1st amp, in case both are not sl8)
    sru_note = 31 # note count of sru
    encore_chance = [65, 65, 65, 65, 65] # list of your encore activation chance, should be of length 5
    amp1_chance = 69 # activation chance of 1st amp
    amp2_chance = 72 # activation chance of 2nd amp
    scorer_chance = 64 # activation chance of scorer
    sru_chance = 41 # activation chance of sru
    amp1_sl = 8 # skill level of 1st amp
    amp2_sl = 8 # skill level of 2nd amp
    # magnitude and length is given as a list where the first element is its base skill level and last element is the max value
    scorer_mag = [2200, 2425, 2880, 3555, 4460, 4715, 5225, 5990, 7015] # score gain from scorer, pre-charm
    sru_mag = [26, 26, 31, 39, 51, 54, 64, 79, 102] # skill chance up of sru
    sru_len = [7] # skill duration of sru

# test: cheer rin 30n scorer + panacore 30n
if loadout_profile == 12:
    loadout_name = "30n/30n panacore test"
    encore_note = 30 # note count of scorer and encore
    scorer_note = 30 # SPECIAL: 15n scorer and 30n amp case (or any case where scorer has exactly half the note requirement of encorer)
    amp1_note = 21 # note count of 1st amp
    amp2_note = 22 # note count of 2nd amp (2nd amp is to the right of 1st amp, in case both are not sl8)
    sru_note = 31 # note count of sru
    encore_chance = [65, 65, 65, 65, 65] # list of your encore activation chance, should be of length 5
    amp1_chance = 69 # activation chance of 1st amp
    amp2_chance = 72 # activation chance of 2nd amp
    scorer_chance = 64 # activation chance of scorer
    sru_chance = 41 # activation chance of sru
    amp1_sl = 8 # skill level of 1st amp
    amp2_sl = 8 # skill level of 2nd amp
    # magnitude and length is given as a list where the first element is its base skill level and last element is the max value
    scorer_mag = [4385, 9145, 9145, 9145, 9145, 14330, 14330, 14330, 14330]  # score gain from scorer, pre-charm
    sru_mag = [26, 26, 31, 39, 51, 54, 64, 79, 102] # skill chance up of sru
    sru_len = [7] # skill duration of sru

# Do NOT edit (unless you know what you're doing)
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

def simulate():
    score = 0
    amp_coin_flip = rng(50) # if true, amp will steal amp charge on tie with scorer/sru
    current_amp_charge = 0
    last_activated_skill = None
    last_skill_amp_level = 0
    sru_active = False
    sru_active_mag = 1
    sru_self_covered = False
    sru_end_note = 0

    for note in range(1, total_note + 1):
        encore_activate = (note % encore_note == 0)
        sru_activate = (note % sru_note == 0)
        
        if sru_active and note > sru_end_note:
            # sru ends prior to this note (we will assume that it is virtually impossible for the sru to end on the exact frame of the note)
            # check if sru will renew itself
            if sru_self_covered and rng(sru_chance):
                sru_end_note += amp(sru_len, current_amp_charge) * note_density
                sru_active_mag = 1 + amp(sru_mag, current_amp_charge) / 100
                last_activated_skill = "sru"
                last_skill_amp_level = current_amp_charge
                current_amp_charge = 0
            else:
                sru_active = False
                # redundancy, just to be safe
                sru_end_note = 0
                sru_active_mag = 1
                sru_self_covered = False

        if sru_activate and sru_active:
            # sru cannot activate, but set self-covered state to true
            sru_self_covered = True
            sru_activate = False
        
        if sru_activate:
            sru_activate = rng(sru_chance)
            # after this line, sru_activate will be true if and only if sru will proc on this note
        
        amp1_activate = (note % amp1_note == 0 and rng(amp1_chance * sru_active_mag))
        amp2_activate = (note % amp2_note == 0 and rng(amp2_chance * sru_active_mag))
        scorer_activate = (note % scorer_note == 0) and rng(scorer_chance * sru_active_mag)
        amp_activate = (amp1_activate or amp2_activate)

        if encore_activate:
            num_proc = num_encore_proc(encore_chance, sru_active_mag)
            if amp_activate:
                if amp_coin_flip: # amp steal amp charge
                    if scorer_activate:
                        score += 2.5 * amp(scorer_mag, 0) * (1 + num_proc)
                    if sru_activate:
                        sru_end_note = note + amp(sru_len, 0) * note_density
                        sru_active_mag = 1 + amp(sru_mag, 0) / 100
                        sru_self_covered = False
                        sru_active = True
                    if amp2_activate:
                        current_amp_charge = get_amp_level(amp2_sl + current_amp_charge)
                    else:
                        current_amp_charge = get_amp_level(amp1_sl + current_amp_charge)
                    last_activated_skill = "amp"
                    last_skill_amp_level = 0 # it doesn't matter, encore will not touch amp
                else:
                    if scorer_activate:
                        score += 2.5 * amp(scorer_mag, current_amp_charge) * (1 + num_proc)
                    if sru_activate:
                        if scorer_activate:
                            sru_end_note = note + amp(sru_len, 0) * note_density
                            sru_active_mag = 1 + amp(sru_mag, 0) / 100
                        else:
                            sru_end_note = note + amp(sru_len, current_amp_charge) * note_density
                            sru_active_mag = 1 + amp(sru_mag, current_amp_charge) / 100
                        sru_self_covered = False
                        sru_active = True
                    if scorer_activate or sru_activate or num_proc > 0:
                        current_amp_charge = 0
                    if amp2_activate:
                        current_amp_charge = get_amp_level(amp2_sl + current_amp_charge)
                    else:
                        current_amp_charge = get_amp_level(amp1_sl + current_amp_charge)
                    last_activated_skill = "amp"
                    last_skill_amp_level = 0
                    
            elif sru_activate: # encore-scorer combo with sru - encore will not interfere with sru
                if scorer_activate: # resolve scorer first                    
                    score += 2.5 * amp(scorer_mag, current_amp_charge) * (1 + num_proc)
                    if num_proc == 0:
                        last_activated_skill = "sru"
                        last_skill_amp_level = 0
                    else:
                        last_activated_skill = "encore"
                    current_amp_charge = 0
                    sru_end_note = note + amp(sru_len, 0) * note_density
                    sru_active_mag = 1 + amp(sru_mag, 0) / 100
                    sru_self_covered = False
                    sru_active = True
                else: # sru proc only
                    sru_end_note = note + amp(sru_len, current_amp_charge) * note_density
                    sru_active_mag = 1 + amp(sru_mag, current_amp_charge) / 100
                    sru_self_covered = False
                    sru_active = True
                    last_activated_skill = "sru"
                    last_skill_amp_level = current_amp_charge
                    current_amp_charge = 0

            else: # only encore-scorer combo
                if scorer_activate:
                    score += 2.5 * amp(scorer_mag, current_amp_charge) * (1 + num_proc)
                    if num_proc == 0:
                        last_activated_skill = "scorer"
                        last_skill_amp_level = current_amp_charge
                    else:
                        last_activated_skill = "encore"
                    current_amp_charge = 0
                else: # scorer doesn't proc, check if encore can proc on old sru
                    if last_activated_skill == "scorer":
                        score += 2.5 * amp(scorer_mag, last_skill_amp_level) * num_proc
                        if num_proc >= 1:
                            last_activated_skill = "encore"
                            last_skill_amp_level = 0
                            current_amp_charge = 0
                    elif last_activated_skill == "sru" and not sru_active and num_proc >= 1:
                        sru_end_note = note + amp(sru_len, last_skill_amp_level) * note_density
                        sru_active_mag = 1 + amp(sru_mag, last_skill_amp_level) / 100
                        sru_self_covered = False
                        sru_active = True
                        last_activated_skill = "encore"
                        last_skill_amp_level = 0
                        current_amp_charge = 0

        else: # no encore-scorer combo on this note
            if scorer_activate:
                score += 2.5 * amp(scorer_mag, current_amp_charge)
                last_activated_skill = "scorer"
                last_skill_amp_level = current_amp_charge
                current_amp_charge = 0
            if amp_activate:
                if sru_activate:
                    if amp_coin_flip:
                        sru_end_note = note + amp(sru_len, 0) * note_density
                        sru_active_mag = 1 + amp(sru_mag, 0) / 100
                    else:
                        sru_end_note = note + amp(sru_len, current_amp_charge) * note_density
                        sru_active_mag = 1 + amp(sru_mag, current_amp_charge) / 100
                        current_amp_charge = 0
                    sru_active = True
                    sru_self_covered = False
                if amp2_activate:
                    current_amp_charge = get_amp_level(amp2_sl + current_amp_charge)
                else:
                    current_amp_charge = get_amp_level(amp1_sl + current_amp_charge)
                last_activated_skill = "amp"
                last_skill_amp_level = 0
            elif sru_activate:
                sru_end_note = note + amp(sru_len, current_amp_charge) * note_density
                sru_active_mag = 1 + amp(sru_mag, current_amp_charge) / 100
                sru_active = True
                sru_self_covered = False
                last_activated_skill = "sru"
                last_skill_amp_level = current_amp_charge 
                current_amp_charge = 0   

    return score

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
    tap_score = get_tap_score(total_note, team_tap_power, team_tap_mult, perfect_rate) * tap_score_modifier
    simulated_score = list()
    for simulation_round in range(10000):
        simulated_score.append(simulate() + tap_score)
    
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
