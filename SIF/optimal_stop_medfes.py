import matplotlib.pyplot as plt
from itertools import accumulate

# @author: Olionheart
# edit the note count of available songs here
song_note_count = [599,550,537,533,500,431,429,424]

# do not edit (unless you're sure I made a mistake)
song_count = len(song_note_count)
medley_note_count = list()
for i in range(song_count-2):
    for j in range(i+1,song_count-1):
        for k in range(j+1,song_count):
            medley_note_count.append(song_note_count[i]+song_note_count[j]+song_note_count[k])
medley_note_count.sort(reverse=True)
cum_note_count = list(accumulate(medley_note_count))
medley_count = len(medley_note_count)
print(medley_count)

# optimal stopping criterion (risk-neutral)
m_j = [0 for i in range(10)]
E_j = [0 for i in range(11)]
p_j = [0 for i in range(10)]

E_j[10] = sum(medley_note_count)/medley_count
for j in reversed(range(10)):
    best_m_j = 0
    best_E_j = 0
    best_p_j = 0
    for i in range(medley_count):
        temp_m_j = medley_note_count[i]
        temp_E_j = cum_note_count[i] / medley_count + E_j[j+1] * (1 - (i+1) / medley_count)
        if temp_E_j > best_E_j:
            best_E_j = temp_E_j
            best_m_j = temp_m_j
            best_p_j = (i+1) / medley_count
    m_j[j] = best_m_j
    E_j[j] = best_E_j
    p_j[j] = best_p_j

cum_p_j = list()
curr_p_max = 1
for j in range(10):
    cum_p_j.append(curr_p_max * p_j[j])
    curr_p_max *= (1 - p_j[j])
cum_p_j.append(curr_p_max)

fig, (ax1, ax2, ax3) = plt.subplots(3)
ax1.plot([i+1 for i in range(10)], m_j, 'ro')
ax1.set_title('minimum note count to stop at each step')
ax1.set(xlabel='reroll step', ylabel='note count')
ax2.plot([i+1 for i in range(10)], E_j[:-1], 'ro')
ax2.set_title('expected note count for each step')
ax2.set(xlabel='reroll step', ylabel='expected note count')
ax3.plot([i for i in range(11)], cum_p_j)
ax3.set_title('distribution of reroll count')
ax3.set(xlabel='reroll count', ylabel='probability')
plt.subplots_adjust(hspace=1)
# plt.show()

print("expected rerolls = ", sum([cum_p_j[i] * i for i in range(11)]))
print("expected note count = ", E_j[0])
print("optimal stopping note count:")
for i in range(10):
    print("step", i+1, ":", m_j[i])

# simple stopping criterion (risk-neutral)
best_E = 0
best_m = 0
best_p = 0
for i in range(medley_count):
    temp_m = medley_note_count[i]
    temp_p = (i+1) / medley_count
    temp_E = (1 - (1 - temp_p) ** 10) * cum_note_count[i] / (i+1) + (1 - temp_p) ** 10 * E_j[10]
    if temp_E > best_E:
        best_E = temp_E
        best_m = temp_m
        best_p = temp_p

cum_p = list()
curr_p_max = 1
for j in range(10):
    cum_p.append(curr_p_max * best_p)
    curr_p_max *= (1 - best_p)
cum_p.append(curr_p_max)

print("stopping criterion =", best_m)     
print("expected rerolls =", sum([cum_p_j[i] * i for i in range(11)]))   
print("expected note count =", best_E)