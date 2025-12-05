from machine import I2C, Pin
from lcd1602 import LCD
import utime
import time


#/////////////////////////////////////////////////////////////////////////////

#SERVO BLOCK
servo = machine.PWM(Pin(15))
servo.freq(50)
button_lock = Pin(13, Pin.IN)

def interval_mapping(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def servo_write(pin,angle):
    pulse_width=interval_mapping(angle, 0, 180, 0.5,2.5)
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

#File save system
#reads the previous code saved to file
def getCode():
    with open('code.txt','r') as file:
        oldCode = list(file.read())
        print(oldCode)
    return oldCode


#saves a new code to file
def saveCode(newCode:list[int]):
    with open('code.txt','w') as file:
        file.write(''.join([str(s) for s in newCode]))



#///////////////////////////////////////////////////////////////////////////
#Initialize I2C communication
i2c = I2C(1, sda = Pin(26), scl = Pin(27), freq = 400000)

#Create an LCD object for interfacing with the LCD1602 display
lcd = LCD(i2c)
    
#LCD BLOCK
def scrollmessage(string):
    for i in range(len(string)):
        lcd.write(0,0,string[i:i+16])
        utime.sleep(0.05)

def printmessage(string):
    lcd.message(string)


#///////////////////////////////////////////////////////////////////////////
#GENERAL CODE FOR THE KEYPAD-SERVO FUNCTIONS
password = getCode()
print(password)
input_list = []
def general():
    global input_list
    global password
    global last_key
    #for i in range(0,len(password),7):
     #   index = password[2+i:5+i]
    #print(empty)
    while True:
        if button_lock.value() == 1:
            lcd.clear()
            servo_write(servo,0)
            printmessage('Locked ')
            lockChime()
            input_list.clear()
            time.sleep(1)
            lcd.clear()
        
        #GENERAL FUNCTION
        current_key = readKey()
        if current_key == last_key:
            continue
        last_key = current_key
        
        x = []
        if current_key != None:
            xkey = current_key
            input_list.append(current_key)
            pressChime()
            printmessage(current_key)
            print(*current_key)
            x.append(xkey)
            if len(input_list) == 6:
                input_list = list(str(input_list))
                print(input_list)
                if input_list == password:
                    servo_write(servo,90)
                    unlockChime()
                    lcd.clear()
                    printmessage('Unlocked')
                    time.sleep(1)
                    input_list.clear()
                    lcd.clear()
                else:
                    time.sleep(1)
                    lcd.clear()
                    printmessage('Incorrect ')
                    time.sleep(1)
                    lcd.clear()
                    input_list.clear()
                    alarm()
               
                
            #PASSWORD SETTING BLOCK
            set_password = []
            if current_key == ['*','#']:
                password.clear()
                scrollmessage('Password reseted, please enter a new 6-character password ')
                lcd.clear()
                time.sleep(1)
                
                #SETTING PASSWORD
                while True:
                    current_key = readKey()
                    if current_key == last_key:
                        continue
                    if current_key != None:
                        xkey = current_key
                        pressChime()
                        printmessage(*current_key)
                        print(*current_key)
                        x.append(xkey)
                        set_password.append(current_key)
                        #printmessage(password)
                        if len(set_password) == 6:
                            input_list.clear()
                            scrollmessage(f'Password set to {set_password} ')
                            password = set_password
                            saveCode(str(password))
                            lcd.clear()
                            break
                    time.sleep(0.25)       
        time.sleep(0.25)







#ALARM BLOCK///////////////////////////////////////////////////////////////////

buzzer = machine.PWM(machine.Pin(16))

#plays a tone for a duration with a short pause after
def tone(frequency,duration, pause):
    buzzer.freq(frequency)
    buzzer.duty_u16(30000)
    utime.sleep_ms(duration)
    buzzer.duty_u16(0)
    utime.sleep_ms(pause)

#plays a tone for a duration with no pause after
def qtone(freq,duration):
    tone(freq, duration, 0)

disarmCode = []
#plays an annoying alarm. currently no way to cancel
def alarm():
    global password
    for i in range(4):
        if stop() == password:
            print('Stop')
            servo_write(servo,90)
            unlockChime()
            lcd.clear()
            printmessage('Unlocked')
            time.sleep(1)
            input_list.clear()
            lcd.clear()
            break
        tone(200,200,100)
        tone(150,500,200)

    for i in range(6):
        if stop() == password:
            print('Stop')
            servo_write(servo,90)
            unlockChime()
            lcd.clear()
            printmessage('Unlocked')
            time.sleep(1)
            input_list.clear()
            lcd.clear()
            break
        tone(900,200,100)


    speed = 100
    noise = 300

    while True:
        if stop() == password:
            print('Stop')
            servo_write(servo,90)
            unlockChime()
            lcd.clear()
            printmessage('Unlocked')
            time.sleep(1)
            input_list.clear()
            lcd.clear()
            break
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
        

#plays a chime intended as feedback for a button press
def pressChime():
    tone(1100,100,100)
    
#plays a chime intended to indicate that the safe has been locked
def lockChime():
    tone(500,250,100)
    tone(500,250,0)

#plays a chime intended to indicate that the safe has been unlocked
def unlockChime():
    tone(700,250,50)
    tone(1000,250,50)


#stop button
def stop():
    global disarmCode
    thisKey = readKey()
    if thisKey != None:
        pressChime()
        disarmCode.append(thisKey)
        printmessage(*thisKey)
        if len(disarmCode) > 6:
            lcd.clear()
            printmessage('Incorrect')
            lcd.clear()
            lockChime()
            disarmCode.clear()
            
    return list(str(disarmCode))
            
    """xkey = current_key
    pressChime()
    printmessage(*current_key)
    print(*current_key)
    x.append(xkey)"""
    
#ALARM BLOCK///////////////////////////////////////////////////////////////////


#RUN
general()




