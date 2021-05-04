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
"""
import numpy as np
import matplotlib.pyplot as plt

# Edit parameters here
total_note = 698 # note count of the song of interest (porkbun's default for master is 698)
note_density = 6.17 # average note density
team_tap_power = 70000 # total team attribute (smile/pure/cool) that is relevant to the song
team_tap_mult = 9 # total team multiplier (1 for each card that match song attribute and 1 for each card that match song group)
perfect_rate = 85 # tap perfect rate
encore_note = 26 # note count of scorer and encore
amp1_note = 22 # note count of 1st amp
amp2_note = 20 # note count of 2nd amp (2nd amp is to the right of 1st amp, in case both are not sl8)
sru_note = 32 # note count of sru
encore_chance = [40, 40, 40, 40, 40] # list of your encore activation chance, should be of length 5
amp1_chance = 68 # activation chance of 1st amp
amp2_chance = 66 # activation chance of 2nd amp
scorer_chance = 64 # activation chance of scorer
sru_chance = 42 # activation chance of sru
amp1_sl = 7 # skill level of 1st amp
amp2_sl = 8 # skill level of 2nd amp
scorer_sl = 8 # skill level of scorer
sru_sl = 7 # skill level of sru
# magnitude and length is given as a list where the first element is its base skill level and last element is the max value
scorer_mag = [4025, 4430, 5240, 6455, 8070, 8535, 9465, 10855, 12710] # score gain from scorer, pre-charm
sru_mag = [27, 29, 32, 37, 44, 55, 60, 70, 86, 106] # skill chance up of sru
sru_len = [6, 6.5] # skill duration of sru

# Do NOT edit
def rng(chance):
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
                sru_end_note += amp(sru_len, current_amp_charge)
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
        scorer_activate = rng(scorer_chance * sru_active_mag)
        amp_activate = (amp1_activate or amp2_activate)

        if encore_activate:
            num_proc = num_encore_proc(encore_chance, sru_active_mag)
            if amp_activate:
                if amp_coin_flip: # amp steal amp charge
                    if scorer_activate:
                        score += 2.5 * amp(scorer_mag, 0) * (1 + num_proc)
                    if sru_activate:
                        sru_end_note = note + amp(sru_len, 0)
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
                            sru_end_note = note + amp(sru_len, 0)
                            sru_active_mag = 1 + amp(sru_mag, 0) / 100
                        else:
                            sru_end_note = note + amp(sru_len, current_amp_charge)
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
                    sru_end_note = note + amp(sru_len, 0)
                    sru_active_mag = 1 + amp(sru_mag, 0) / 100
                    sru_self_covered = False
                    sru_active = True
                else: # sru proc only
                    sru_end_note = note + amp(sru_len, current_amp_charge)
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
                        sru_end_note = note + amp(sru_len, last_skill_amp_level)
                        sru_active_mag = 1 + amp(sru_mag, last_skill_amp_level) / 100
                        sru_self_covered = False
                        sru_active = True
                        last_activated_skill = "encore"
                        last_skill_amp_level = 0
                        current_amp_charge = 0

        else: # no encore-scorer combo on this note
            if amp_activate:
                if sru_activate:
                    if amp_coin_flip:
                        sru_end_note = note + amp(sru_len, 0)
                        sru_active_mag = 1 + amp(sru_mag, 0) / 100
                    else:
                        sru_end_note = note + amp(sru_len, current_amp_charge)
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
                sru_end_note = note + amp(sru_len, current_amp_charge)
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
    return 0.0125 * (0.88 + 0.12 * accuracy / 100) * team_power * (1 + 0.1 * team_bonus) * note_mult

if __name__ == "__main__":
    tap_score = get_tap_score(total_note, team_tap_power, team_tap_mult, perfect_rate)
    simulated_score = list()
    for simulation_round in range(10000):
        simulated_score.append(simulate() + tap_score)
    
    plt.hist(simulated_score)
    plt.show()

    print("Simulation Result")
    print("Tap Score:", tap_score)
    print("Mean Score:", np.mean(simulated_score))
    print("Standard Deviation:", np.std(simulated_score))
    print("99-th Percentile Score:", np.percentile(simulated_score, 99))