from random import randrange
import math


def howmanyred(result):
    count=0
    for z in result:
        if z=='R': count+=1
    return count

def select(x, these_balls):
    #where x is number of balls we are selecting
    result=[]
    #where x is no of balls
    for i in range(0,x):
        s = randrange(len(these_balls))
        ball=these_balls[s]
        these_balls.pop(s) #we are not replacing!!!
        result.append(ball)
    return result


def predictedResult(these_balls,sel, reds):
    denominator=math.comb(len(these_balls),sel)
    no_reds=howmanyred(these_balls)
    numerator1=math.comb(no_reds,reds)
    numerator2=math.comb(len(these_balls)-no_reds,sel-reds)
    result=(numerator1*numerator2)/denominator
    return result

def montecarlo(sims,sel,reds):
    total=0
    count=0
    these_balls_org = ['R', 'R', 'R', 'B', 'B']
    for i in range(0,sims):
        these_balls=these_balls_org
        result=select(sel, these_balls)
        count+=1
        r=howmanyred(result)
        print (result, r)
        if r==reds: total+=1
    these_balls = ['R', 'R', 'R', 'B', 'B']
    print ("Predicted result: " + str(predictedResult(these_balls,sel, reds)))
    print ("Simulation result: " + str(total/count))



montecarlo(sims=10000, sel=3, reds=2)


