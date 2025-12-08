from machine import I2C, Pin
from lcd1602 import LCD
import utime
import time
import math


#/////////////////////////////////////////////////////////////////////////////


#SERVO BLOCK
servo = machine.PWM(Pin(15))
servo.freq(50)
button_lock = Pin(13, Pin.IN)

#Converts foreign values to values the servo can process
def interval_mapping(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

#Converts angle values into servo values and also rotates the servo accordingly
def servo_write(pin,angle):
    pulse_width = interval_mapping(angle, 0, 180, 0.5,2.5)
    duty = int(interval_mapping(pulse_width, 0, 20, 0,65535))
    pin.duty_u16(duty)


#///////////////////////////////////////////////////////////////////////////


#KEYPAD BLOCK

characters = [['1','2','3','A'],
              ['4','5','6','B'],
              ['7','8','9','C'],
              ['*','0','#','D']]

#Assigns each keys in the row by pin number
pin = [2,3,4,5]
row = []
for i in range(4):
    row.append(None)
    row[i] = machine.Pin(pin[i], machine.Pin.OUT)

#Assigns each keys in the column by pin number
pin = [6,7,8,9]
col = []
for i in range(4):
    col.append(None)
    col[i] = machine.Pin(pin[i], machine.Pin.IN)

#Reads keys from keypad based on powerlevels
def readKey():
    key = []
    for i in range(4):
        row[i].high()
        for j in range(4):
            if(col[j].value() == 1):
                key.append(characters[i][j])
        row[i].low()
    if key == []:
        return None
    else:
        return key

last_key = None


#///////////////////////////////////////////////////////////////////////////


#FILE SAVE SYSTEM
#Reads the previous code saved to file and closes to ensure the text file updates while the program is still running
def getCode():
    file = open('code.txt','r')
    oldCode = file.read()
    oldCode = oldCode.replace("'","").replace("[","").replace("]","").replace(",","").replace(" ","")
    print(oldCode)
    file.close()
    return oldCode


#Saves a new code (password) to a text file
def saveCode(newCode:list[int]):
    file = open('code.txt','w')
    file.write(''.join([str(s) for s in newCode]))
    file.close()


#///////////////////////////////////////////////////////////////////////////


#LCD BLOCK
        
#Initialize I2C communication
i2c = I2C(1, sda = Pin(26), scl = Pin(27), freq = 400000)

#Create an LCD object for interfacing with the LCD1602 display
lcd = LCD(i2c)

#Used for messages greater than 16 characters to display them as scrolling text
def scrollmessage(row,column,string):
    for i in range(len(string)):
        lcd.write(row,column,string[i:i+16])
        utime.sleep(0.1)
        
#Standard purpose and displays static messages that are less than 16 characters
def printmessage(string):
    lcd.message(string)
    

#///////////////////////////////////////////////////////////////////////////
        
        
#GENERAL CODE FOR THE KEYPAD-SERVO FUNCTIONS

set_password = []
input_list = []
disarmCode = []
#Tracks how many attempts are left before the alarm goes off
def trialcheck():
    global tries
    tries = tries-1
    if tries < 0:
        tries = 0
    lcd.clear
    time.sleep(1)
    lcd.clear()
    lockChime()
    printmessage('Incorrect')
    scrollmessage(0,1,f'{tries} more tries ')
    time.sleep(0.5)
    lcd.clear()
    input_list.clear()
    if tries == 0:
        printmessage('Sounding alarm')
        time.sleep(1)
        lcd.clear()
        input_list.clear()
        alarm()
        
#When the password is correct, this function activates and rotates the servo latch        
def unlockservo():
    input_list.clear()
    disarmCode.clear()
    servo_write(servo,90)
    unlockChime()
    lcd.clear()
    printmessage('Unlocked')
    time.sleep(1)
    lcd.clear()

#Checks and confirms whether password is correct or not
def passcheck():
    current_key = readKey()
    if current_key == ['#','D']:
        del input_list[-1]
        print(input_list)
                
        if stringconverter(input_list,len(password)) == password:
            unlockservo()
            general(resettries)
        else:
            trialcheck()
                    
    elif len(input_list) == 16 and stringconverter(input_list,len(password)) == password:
            unlockservo()
            general(resettries)
                    
    elif len(input_list) == 16:
        trialcheck()
        
#Main function of the system and primarily runs based on the keypad       
def general(attempts):
    global password
    global input_list
    global last_key
    global set_password
    global tries
    global resettries
    password = getCode()
    tries = attempts
    resettries = attempts
    
    disarmCode.clear()
    
    if math.floor(tries) > 99:
        tries = 99
    else:
        tries = math.floor(tries)

    while True:
        #GENERAL FUNCTION
        current_key = readKey()

        if current_key == last_key:
            continue
        last_key = current_key
        
        if current_key == ['0','#']:
            lcd.clear()
            servo_write(servo,0)
            printmessage('Locked ')
            lockChime()
            lcd.clear()
            general(attempts)
            
        x = []
        if current_key != None:
            xkey = current_key
            input_list.append(current_key)
            pressChime()
            printmessage(current_key)
            x.append(xkey)
            passcheck()
                
            #PASSWORD SETTING BLOCK
            if current_key == ['*','#']:
                set_password.clear()
                scrollmessage(0,0,'Password reseted, please enter a new 1 to 16 character password ')
                lcd.clear()
                time.sleep(1)
                
                #SETTING PASSWORD
                while True:
                    current_key = readKey()
                    if current_key == ['*','#'] or len(set_password) == 16:
                        if len(set_password) < 1:
                            scrollmessage(0,0,'Please enter a 1 to 16 character password ')
                            lcd.clear()
                            set_password.clear()
                            
                        elif len(set_password) > 0:
                            input_list.clear()
                            scrollmessage(0,0,f'Password set to {stringconverter(set_password,len(set_password))} ')
                            password = set_password
                            saveCode(str(password))
                            set_password.clear()
                            lcd.clear()
                            return general(tries)
                        
                    if current_key == last_key:
                        continue
                    if current_key != None:
                        print(current_key)
                        xkey = current_key
                        pressChime()
                        printmessage(current_key)
                        x.append(xkey)
                        set_password.append(current_key)
                    time.sleep(0.25)       
        time.sleep(0.25)
        
#Converts password list to a combined string used for displaying
def stringconverter(listpass,elements):
    global displaypass
    for i in range(0,len(listpass),elements+1):
        charlist = [str(*ch) for ch in listpass]
        displaypass = ''.join(charlist)
    return displaypass


#ALARM BLOCK///////////////////////////////////////////////////////////////////


buzzer = machine.PWM(machine.Pin(16))

#Plays a tone for a duration with a short pause after
def tone(frequency,duration, pause):
    buzzer.freq(frequency)
    buzzer.duty_u16(30000)
    utime.sleep_ms(duration)
    buzzer.duty_u16(0)
    utime.sleep_ms(pause)

#Plays a tone for a duration with no pause after
def qtone(freq,duration):
    tone(freq, duration, 0)

#Plays an annoying alarm
def alarm():
    global password
    for i in range(4):
        stop()
        tone(200,200,100)
        tone(150,500,200)

    for i in range(6):
        stop()
        tone(900,200,100)


    speed = 100
    noise = 300

    while True:
        stop()
        qtone(noise,speed)
        qtone(noise + 100,speed)
        qtone(noise + 50,speed)
        qtone(noise + 150,speed)
        if(speed > 10):
            speed -= 1
        else:
            speed = 100
        if(noise < 450):
            noise += 1
        elif(noise < 1000):
            noise = 1000
        if(noise >= 1000):
            noise += 10
        if(noise > 3500):
            noise = 50
        

#Plays a chime intended as feedback for a button press
def pressChime():
    tone(1100,100,100)
    
#Plays a chime intended to indicate that the safe has been locked
def lockChime():
    tone(500,250,100)
    tone(500,250,0)

#Plays a chime intended to indicate that the safe has been unlocked
def unlockChime():
    tone(700,250,50)
    tone(1000,250,50)


#Stop button
def stop():
    global disarmCode
    current_key = readKey()
    if current_key != None:
        pressChime()
        disarmCode.append(current_key)
        print(current_key)
        printmessage(current_key)
        if current_key == ['#','D']:
            del disarmCode[-1]
            print(disarmCode)
            if stringconverter(disarmCode,len(password)) == password:
                current_key = ''
                unlockservo()
                disarmCode.clear()
                general(resettries)
            else:
                lcd.clear()
                lockChime()
                printmessage('Incorrect')
                time.sleep(1)
                lcd.clear()
                disarmCode.clear()
                
        elif len(disarmCode) == 16:
            lcd.clear()
            lockChime()
            printmessage('Incorrect')
            time.sleep(1)
            lcd.clear()
            disarmCode.clear()
                
    
#///////////////////////////////////////////////////////////////////


#RUN
general(1)





