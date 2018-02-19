
import time
import threading

STEP_SPEED = 0.05
SCREEN_WIDTH = 200

# Overdamped
TICK_TIME = 30
P_VALUE = 0.5
D_VALUE = 0.1


# # Overdamped
# TICK_TIME = 30
# P_VALUE = 0.5
# D_VALUE = 0.5

# # Overdamped
# TICK_TIME = 5
# P_VALUE = 0.1
# D_VALUE = 0.25
#
#
#
# # Overdamped
# TICK_TIME = 5
# P_VALUE = 0.5
# D_VALUE = 0.25

# Underdamped long settling time
# TICK_TIME = 5
# P_VALUE = 0.001
# D_VALUE = 0.01 # Change this to 0.05 to fix

# Overshoot with long settling time
# TICK_TIME = 2
# P_VALUE = 0.005 # Default 0.005 extra fast 0.05
# D_VALUE = 0.25

def main():
    ball = Ball()
    timer = 0
    trigger_time = 0
    ticks = 0
    while True:
        time.sleep(STEP_SPEED)
        timer += STEP_SPEED
        if timer > trigger_time:
            trigger_time += TICK_TIME
            ticks += 1
            if ticks %2 == 0:
                ball.position_target = SCREEN_WIDTH / 6 * 2
            else:
                ball.position_target = SCREEN_WIDTH / 6 * 4
        ball.timetick(STEP_SPEED)
        print_spaces(ball.position_target, ball.position_actual)

class Ball:
    def __init__(self):
        self.position_actual = SCREEN_WIDTH/2
        self.position_target = 0
        self.velocity = 0
        self.last_error = 0

    def timetick(self, tick_time):
        if self.position_actual != self.position_target:
            error = self.position_target - self.position_actual
            self.velocity += P_VALUE * error * tick_time + (self.last_error - error) * D_VALUE * -1
            self.position_actual += self.velocity * tick_time
            self.last_error = error


    def set_target(self, setpoint):
        self.target = setpoint


#
#     def update_values(self, interval, overrun):
#         if math.fabs(self.velocity_command) > MAX_VELOCITY:
#             self.velocity_command = 0
#         error =  self.velocity_command - self.velocity_feedback
#
#
#         self.errors.insert(0, error)
#         self.errors.pop()
#
#         error_diffs = [i-j for i, j in zip(self.errors[:-1], self.errors[1:])]
#         average_error_diffs = 0
#         for e in error_diffs:
#             average_error_diffs += e
#         average_error_diffs /= len(error_diffs)
#
#         #print("Velocity Command %r, velocity_feedback %r, error %r" % (self.velocity_command, self.velocity_feedback, average_error_diffs))
#         #print(self.errors)
#
#
#         d_comp = interval/(interval+overrun)
#
#         current_command = error * P_SCALAR + D_SCALAR * average_error_diffs * d_comp
#
#         self.last_error = error
#
#         if (current_command * np.sign(self.velocity_command)) > 0:
#             brake = False
#             if current_command > MAX_CURRENT:
#                 current_command = MAX_CURRENT
#             elif current_command < -MAX_CURRENT:
#                 current_command = -MAX_CURRENT
#         else:
#             brake = True
#             if current_command > MAX_BRAKE_CURRENT:
#                 current_command = MAX_BRAKE_CURRENT
#             elif current_command < -MAX_BRAKE_CURRENT:
#                 current_command = -MAX_BRAKE_CURRENT
#
#         self.set_current(current_command, brake)
#
#     def set_current(self, current_command, brake=True):
#         self.vesc.set_motor_current(current_command, self.canId, brake)
#
#     def tick_velocity(self, tick_length):
#         if self.velocity_command != self.velocity_goal:
#             # Increment by acceleration * tick_length with the appropriate sign
#             increment = self.acceleration * tick_length * np.sign(self.velocity_goal-self.velocity_command) # * np.sign(self.velocity_goal)
#             #print("velocity %d, velocity setpoint %f, increment %f, position %g" % (int(self.velocity*1000), self.velocity_setpoint, increment, self.position))
#             self.velocity_command += increment
#         self.tick_position(tick_length)
#
#     def tick_position(self, tick_length):
#         self.position += self.velocity_command * tick_length


def print_spaces(dot_position, ball_position):
    dot_position = int(dot_position)
    ball_position = int(ball_position)
    if dot_position < ball_position:
        print(' ' * int(dot_position) + '.' + ' ' * int(ball_position-dot_position-1) + 'O')
    elif dot_position > ball_position:
        print(' ' * int(ball_position) + 'O' + ' ' * int(dot_position - ball_position-1) + '.')
    else:
        print(' ' * int(ball_position) + 'O')


if __name__ == "__main__":
    main()
