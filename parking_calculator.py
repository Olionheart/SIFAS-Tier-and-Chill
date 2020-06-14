import numpy as np
import pandas as pd
"""
Copyright <2020> <Olionheart>

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is 
hereby granted, provided that the above copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO 
THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL 
THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES 
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, 
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""
def get_ep_mult(ep_bonus):
    result = set()
    result.add(1)
    for i in range(2 ** len(ep_bonus)):
        iter = [int(x) for x in bin(i)[2:]]
        iter = [0 for k in range(len(ep_bonus)-len(iter))] + iter 
        result.add(1 + 0.01 * sum(np.array(iter) * np.array(ep_bonus)))
    result = list(result)
    result.sort(reverse=True)
    return result

def get_possible_ep(adv_plus, ep_mult):
    base_ep = np.array([875, 600, 405, 275, 860, 845, 830, 815, 581, 562, 543, 525, 390, 375, 360, 345, 262, 250, 237, 225]) if adv_plus else np.array([600, 405, 275, 581, 562, 543, 525, 390, 375, 360, 345, 262, 250, 237, 225])
    result = np.outer(base_ep, ep_mult).astype(int)
    return result

def ukp_solver(target, combination):
    dp_memory = [0]
    for i in range(1, target + 1):
        ans = -1
        for pts in combination:
            if i - pts >= 0 and dp_memory[i - pts] != -1:
                ans = pts 
                break
        dp_memory.append(ans)
    if dp_memory[-1] == -1:
        return False
    else:
        backtrack_dict = dict()
        iter = target
        while iter > 0:
            pts = dp_memory[iter]
            iter -= pts
            if pts in backtrack_dict.keys():
                backtrack_dict[pts] += 1
            else:
                backtrack_dict[pts] = 1
        assert iter == 0
        return backtrack_dict
        
print("This SIFAS parking calculator is made by 『TC』Olion♡ (twt: @O1ionheart)")
current_ep = 0
target_ep = 0
adv_plus = False
ep_bonus = [] 
get_input = True
debug = False

if get_input:
    # get current_ep
    try:
        current_ep = int(input("Please indicate your current event point (EP): "))
    except ValueError:
        success = False
        while not success:
            try:
                current_ep = int(input("Your input was not an integer, please try again: "))
                success = True
            except ValueError:
                pass

    # get adv_plus
    adv_plus = input("Are adv+ songs available (T if True): ").lower() == 't'
    
    # get ep_bonus
    ep_bonus = []
    new_ep_bonus = -1
    print("Please input your event point bonus from cards. Do not de-duplicate! \n(i.e. if you have 2 cards that give 3% bonus each, you should enter 3 twice) \nEnter 0 when you are done, or if the event is an item exchange event.")
    print("***NOTE: I haven't fixed rounding errors for marathon events yet!! Becareful!!***")
    while new_ep_bonus != 0:
        try:
            new_ep_bonus = int(input("Card #" + str(len(ep_bonus) + 1) + " : "))
        except ValueError:
            success = False
            while not success:
                try:
                    new_ep_bonus = int(input("Your input was not an integer, please try again: "))
                    success = True
                except ValueError:
                    pass
        ep_bonus.append(new_ep_bonus)
    ep_bonus.pop()

# get target_ep
try:
    target_ep = int(input("Please indicate your target event point (EP): "))
except ValueError:
    success = False
    while not success:
        try:
            target_ep = int(input("Your input was not an integer, please try again: "))
            success = True
        except ValueError:
            pass

if debug:
    print(current_ep)
    print(adv_plus)
    print(ep_bonus)
    print(get_ep_mult(ep_bonus))
    df = pd.DataFrame(get_possible_ep(adv_plus, np.array(get_ep_mult(ep_bonus))))
    print(get_possible_ep(adv_plus, np.array(get_ep_mult(ep_bonus))).flatten().tolist())

result = ukp_solver(target_ep - current_ep, get_possible_ep(adv_plus, np.array(get_ep_mult(ep_bonus))).flatten())
if result:
    print("Park found!: ", result)
else:
    print("Park not found! Try again ~")