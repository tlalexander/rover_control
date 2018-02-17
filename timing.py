import time

# measure the smallest time delta by spinning until the time changes
def measure():
    t0 = time.time()
    t1 = t0
    loops = 0
    while t1 < (t0 + 333*1e-6):
    #while t1 == t0:
        t1 = time.time()
        loops +=1
    return (t0, t1, (t1-t0)*1e6, loops)

samples = [measure() for i in range(100)]

#while True:
#    print(measure())

avg = 0.0
for s in samples:
    avg += s[2]
    print(s)
avg = avg/len(samples)
print(avg)
