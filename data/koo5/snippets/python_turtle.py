from turtle import *
color('red', 'yellow')
speed(14)
begin_fill()
while True:
    forward(200)
    left(170)
    speed(abs(pos())/10)
    if abs(pos()) < 1:
        break
end_fill()
done()
