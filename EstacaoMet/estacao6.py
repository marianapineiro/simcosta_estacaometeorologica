import machine
from machine import Pin, UART, SoftI2C
from time import sleep
from ADS1115 import *
import ustruct
from ulab import numpy as np
import random


uart_storex = UART(2, 19200)
#uart_bussola = UART(0, 4800)
framesync = "WQMX"

WS_in_min = 0.0
WS_in_max = 5.0
WS_out_min = 0.0    #WIND SPEED RANGE: 0 to 100 M/S
WS_out_max = 100.0
 
WD_in_min = 0.01
WD_in_max = 4.94
WD_out_min = 0.0     #WIND DIRECTION RANGE: 0 to 360
WD_out_max = 360.0

T_in_min = 0
T_in_max = 3413
T_out_min = -40     #range temperatura: -40°C à +60°C
T_out_max = 60
 
H_in_min = 0
H_in_max = 3413
H_out_min = 0       #range humidade: 0-100%
H_out_max = 100

P_in_min = 0
P_in_max = 5
P_out_min = 800     #range pressao 800 a 1060 hpa 
P_out_max = 1060

WS_data = []
# print(type(WS_data)) 
WD_data = []
T_data = []
H_data = []
P_data = []
 

 
ADS1115_1_ADDRESS = 0x48
ADS1115_2_ADDRESS = 0X49

i2c = SoftI2C(scl = Pin(22), sda = Pin(21))

adc_1 = ADS1115(ADS1115_1_ADDRESS, i2c=i2c)
adc_2 = ADS1115(ADS1115_2_ADDRESS, i2c=i2c)

adc_1.setVoltageRange_mV(ADS1115_RANGE_6144)
adc_1.setCompareChannels(ADS1115_COMP_0_GND)
adc_1.setMeasureMode(ADS1115_SINGLE)
adc_2.setVoltageRange_mV(ADS1115_RANGE_6144)
adc_2.setCompareChannels(ADS1115_COMP_0_GND)
adc_2.setMeasureMode(ADS1115_SINGLE) 

interruptCounter=0
totalInterruptsCounter=0

timer=machine.Timer(0)
        
timer.init(period=1000, mode=machine.Timer.PERIODIC, callback=handlerInterrupt) #period=1000, ou seja, a interrupção acontece uma vez por segundo; mode=machine.Timer.PERIODIC pois acontece em loop, a cada 1000 ms; callback=handlerInterrupt ou seja, a função que vai acontecer quando a interrupção for chamada

def handlerInterrupt(timer):
    global interruptCounter
    interruptCounter = interruptCounter + 1
        
    T_value = readChannel_1(ADS1115_COMP_0_GND)
    H_value = readChannel_1(ADS1115_COMP_1_GND)
    WS_value = readChannel_1(ADS1115_COMP_2_GND)  #random.uniform(0.0, 10.0)
    WD_value = readChannel_1(ADS1115_COMP_3_GND)
#     LM_value =  readChannel_2(ADS1115_COMP_0_GND)
    P_value = readChannel_2(ADS1115_COMP_3_GND)

    TH_data = TemperatureHumidityRead(T_value, H_value)
    wind_data = anemometerRead(WS_value, WD_value)
    pressure_data = barometerRead(P_value)
#     bussola_data = getBussolaInfo(uart_bussola.read())

    estacao = wind_data + TH_data + pressure_data#+ bussola_data

    estacao=str(estacao).strip('[]')   #transforma list em string retirando conchetes da msg 
    estacao=[framesync,estacao]        #coloca framesync no inicio da msg
    print(estacao)
    estacao_comma_separated = ','.join(estacao)



def readChannel_1(channel):
    adc_1.setCompareChannels(channel)
    adc_1.startSingleMeasurement()
    while adc_1.isBusy():
        pass
    voltage = adc_1.getResult_V()
    return voltage

def readChannel_2(channel):
    adc_2.setCompareChannels(channel)
    adc_2.startSingleMeasurement()
    while adc_2.isBusy():
        pass
    voltage = adc_2.getResult_V()
    return voltage



def anemometerRead(WS_value, WD_value):
    WS = (WS_value - WS_in_min) * (WS_out_max - WS_out_min) / (WS_in_max - WS_in_min) + WS_out_min
    WS_data.append(WS)
#     print(len(WS_data))
    WS_mean = np.mean(WS_data)
    WS_stdev = np.std(WS_data)
    
    WD = (WD_value - WD_in_min) * (WD_out_max - WD_out_min) / (WD_in_max - WD_in_min) + WD_out_min
    
    WD_data.append(WD)
    WD_mean = np.mean(WD_data)
    WD_stdev = np.std(WD_data)
    
    gc.collect() # control of garbage collection
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
    
    anemometerData = [WS_mean, WS_stdev, WD_mean, WD_stdev]   #List
    #print(type(anemometerData))
    #anemometerData = str(anemometerData)                     #make list into string
     
    #print(type(anemometerData))
    return anemometerData


def barometerRead(P_value):
    P = (P_value - P_in_min) * (P_out_max - P_out_min) / (P_in_max - P_in_min) + P_out_min
    print(P)
    P_data.append(P)
    print(P_data)
#     print(len(WS_data))
    P_mean = np.mean(P_data)
    P_stdev = np.std(P_data)
  
    gc.collect() # control of garbage collection
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
    
    barometerData = [P_mean, P_stdev]   #List
    return barometerData


def TemperatureHumidityRead(T_value, H_value):
    T = (T_value - T_in_min) * (T_out_max - T_out_min) / (T_in_max - T_in_min) + T_out_min
    T_data.append(T)
    # print(len(WS_data))
    T_mean = np.mean(T_data)
    T_stdev = np.std(T_data)
    
    H = (H_value - H_in_min) * (H_out_max - H_out_min) / (H_in_max - H_in_min) + H_out_min
    H_data.append(H)
    H_mean = np.mean(H_data)
    H_stdev = np.std(H_data)
    
    gc.collect() # control of garbage collection
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
    
    probeData = [T_mean, T_stdev, H_mean, H_stdev]
    #probeData = str(probeData)
    return probeData

def getBussolaInfo (bussola):
    if bussola != None:
         bussola=str(bussola)
         bussval = get_first_nbr_from_str(bussola)
         print(bussval)
    return bussval

def get_first_nbr_from_str(input_str):
    if not input_str and not isinstance(input_str, str):
        return 0
    out_number = ''
    for ele in input_str:
        if (ele == '.' and '.' not in out_number) or ele.isdigit():
            out_number += ele
        elif out_number:
            break
    return float(out_number)

while True:
    if interruptCounter > 0:
        state = machine.disable_irq()
        interruptCounter = interruptCounter - 1
        machine.enable_irq(state)
        
        #totalInterruptsCounter = totalInterruptsCounter + 1
        #print("interrupt has occurred: "+ str(totalInterruptsCounter))
        
        
     





