#utils_test_xibeng.py

from pymycobot import MyCobot280
from pymycobot import PI_PORT, PI_BAUD  # 当使用树莓派版本的mycobot时，可以引用这两个变量进行MyCobot初始化
import time
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
from gpiozero import LED

# 初始化一个MyCobot280对象
mc = MyCobot280(PI_PORT, PI_BAUD)

Device.pin_factory = LGPIOFactory(chip=0) # 显式指定/dev/gpiochip0
# 初始化 GPIOZERO 控制的设备
pump = LED(46)   # 气泵
valve = LED(37)  # 阀门
pump.on()
print("1")
time.sleep(0.05)
valve.on()
print("2")

# 开启吸泵
def pump_on():
    pump.on()
    valve.off()

# 停止吸泵
def pump_off():
    pump.off()
    valve.on()

pump_off()
print("3")
time.sleep(3)
pump_on()
print("4")
time.sleep(3)
pump_off()
print("5")
time.sleep(3)
pump_on()
print("6")