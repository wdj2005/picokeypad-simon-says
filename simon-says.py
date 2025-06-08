# MicroPython Simple Simon game
# Based on 
# Circuit Playground Express Simple Simon
#
# Game play based on information provided here:
# http://www.waitingforfriday.com/?p=586
#
# Author: Carter Nelson
# MIT License (https://opensource.org/licenses/MIT)
import time
import random
import picokeypad
import machine
from machine import Pin, PWM, ADC

#Some constants
FAILURE_TONE        = 100
SEQUENCE_DELAY      = 0.8
GUESS_TIMEOUT       = 3.0
DEBOUNCE            = 0.250
#Define difficulty levels:
SEQUENCE_LENGTH = {
  1 : 8,
  2 : 14,
  3 : 20,
  4 : 31
}
SIMON_BUTTONS = {
  1 : { 'pads':(0,1,4,5), 'pixels':(0,1,4,5), 'R':0xFF, 'G':0xFF, 'B':0x00, 'freq':415 }, 
  2 : { 'pads':(2,3,6,7), 'pixels':(2,3,6,7), 'R':0x00, 'G':0x00, 'B':0xFF, 'freq':252 }, 
  3 : { 'pads':(8,9,12,13), 'pixels':(8,9,12,13), 'R':0xFF, 'G':0x00, 'B':0x00, 'freq':209 }, 
  4 : { 'pads':(10,11,14,15), 'pixels':(10,11,14,15), 'R':0x00, 'G':0xFF, 'B':0x00, 'freq':310 },  
}

#Pad 1: Yellow
#Pad 2: Blue
#Pad 3: Red
#Pad 4: Green

#Wire a buzzer to GPIO15 for sound!
buzzer = PWM(Pin(15))

keypad = picokeypad.PicoKeypad()
keypad.set_brightness(0.7)

NUM_PADS = keypad.get_num_pads()

#Play a tone at full volume (duty cycle)
def play_tone(frequency, duration):
    buzzer.duty_u16(1000)
    buzzer.freq(frequency)
    time.sleep(duration)
    buzzer.duty_u16(0)
    

def choose_skill_level():
    # Default
    skill_level = 1
    # Loop until button 15 is pressed
    
    while not keypad.get_button_states() == 32768:
        # Button 14 increases skill level setting
        if keypad.get_button_states() == 16384:
            skill_level += 1
            skill_level = skill_level if skill_level < 5 else 1
            # Indicate current skill level
            keypad.clear() #Blank the LEDs
            for p in range(skill_level):
                keypad.illuminate(p, 0x00, 0x20, 0x00)
            time.sleep(DEBOUNCE)
            #Illuminate start game button (15)
            keypad.illuminate(15, 0xFF, 0xFF, 0xFF)
            keypad.update()
    return skill_level

def new_game(skill_level):
    # Seed the random function with noise from ADC pins
    
    a1 = ADC(Pin(26))
    a2 = ADC(Pin(27))
    a3 = ADC(Pin(28))
    
    seed  = a1.read_u16()
    seed += a2.read_u16()
    seed += a3.read_u16()

    random.seed(seed)    

    print("Seed=",seed)

    # Populate the game sequence
    return [random.randint(1,4) for i in range(SEQUENCE_LENGTH[skill_level])]

def indicate_button(button, duration):
    # Turn them all off
    keypad.clear()
    # Turn on the ones for the given button
    for p in button['pixels']:
        keypad.illuminate(p, button['R'], button['G'], button['B'] )
    keypad.update()
        
    # Play button tone
    if button['freq'] == None:
        time.sleep(duration)
    else:
        play_tone(button['freq'], duration)
    # Turn them all off again
    keypad.clear()
    keypad.update()
    
def show_sequence(sequence, step):
    # Set tone playback duration based on current location
    if step <= 5:
        duration = 0.420
    elif step <= 13:
        duration = 0.320
    else:
        duration = 0.220
    
    # Play back sequence up to current step
    for b in range(step):
        time.sleep(0.05)
        indicate_button(SIMON_BUTTONS[sequence[b]], duration)    

   
    
def get_button_press():
    
    current_buttons = keypad.get_button_states()
    # Loop over all four buttons and return which button is pressed
    for button in SIMON_BUTTONS.values():
        # Loop over each pad
        for pad in button['pads']:
            if current_buttons == (1 << pad):
                indicate_button(button, DEBOUNCE)
                return button
    return None

def game_lost(step):
    # Show button that should have been pressed
    keypad.clear()
    for p in SIMON_BUTTONS[sequence[step]]['pixels']:
        keypad.illuminate(p, SIMON_BUTTONS[sequence[step]]['R'], SIMON_BUTTONS[sequence[step]]['G'], SIMON_BUTTONS[sequence[step]]['B'] )
    keypad.update()
    # Play sad sound :(
    play_tone(FAILURE_TONE, 1.5)
    
    # And just sit here until reset
    while True:
        pass
    
def game_won():
    # Play 'razz' special victory signal
    for i in range(3):
        indicate_button(SIMON_BUTTONS[4], 0.1)        
        indicate_button(SIMON_BUTTONS[2], 0.1)        
        indicate_button(SIMON_BUTTONS[3], 0.1)        
        indicate_button(SIMON_BUTTONS[1], 0.1)        
    indicate_button(SIMON_BUTTONS[4], 0.1)            
    indicate_button(SIMON_BUTTONS[2], 0.1)

    # Change tones to failure tone
    for button in SIMON_BUTTONS.values():
        button['freq'] = FAILURE_TONE
        
    # Continue for another 0.8 seconds
    for i in range(2):
        indicate_button(SIMON_BUTTONS[3], 0.1)        
        indicate_button(SIMON_BUTTONS[1], 0.1)        
        indicate_button(SIMON_BUTTONS[4], 0.1)        
        indicate_button(SIMON_BUTTONS[2], 0.1)        
    
    # Change tones to silence
    for button in SIMON_BUTTONS.values():
        button['freq'] = None
    
    # Loop lights forever
    while True:
        indicate_button(SIMON_BUTTONS[3], 0.1)        
        indicate_button(SIMON_BUTTONS[1], 0.1)        
        indicate_button(SIMON_BUTTONS[4], 0.1)        
        indicate_button(SIMON_BUTTONS[2], 0.1)                

# Initialize & setup global variables    
keypad.clear()
#Illuminate Skill level button (14) ready to take input
keypad.illuminate(14, 0xFF, 0xFF, 0xFF)
keypad.update()

#Global variables
skill_level = choose_skill_level()
sequence = new_game(skill_level)
current_step = 1

#Loop forever
while True:
    # Show sequence up to current step
    show_sequence(sequence, current_step)
    
    # Read player button presses
    for step in range(current_step):
        start_guess_time = time.time()
        guess = None
        while (time.time() - start_guess_time < GUESS_TIMEOUT) and (guess == None):
            guess = get_button_press()
        if not guess == SIMON_BUTTONS[sequence[step]]:
            game_lost(sequence[step])
            

    # Advance the game forward
    current_step += 1
    if current_step > len(sequence):
        game_won()
    
    # Small delay before continuing    
    time.sleep(SEQUENCE_DELAY)


