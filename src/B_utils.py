import math 

def to_16_divisible(number, mode):
    if mode == "up":
        return math.ceil(number / 16) * 16
    if mode == "down":
        return math.floor(number / 16) * 16

def to_28_divisible(number, mode):
    if mode == "up":
        return math.ceil(number / 28) * 28
    if mode == "down":
        return math.floor(number / 28) * 28
    if mode == "round":
        return round(number / 28) * 28
