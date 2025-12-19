import smbus2
import config

# I2C 통신을 위한 시스템 관리 버스(SMBus) 초기화
# - SMBus(System Management Bus): I²C 기술을 기반으로 컴퓨터의 상태(온도, 전압, 배터리 등)를 관리하고 모니터링하기 위해 만들어진 통신 규격
def init_smbus():
    try:
        smbus = smbus2.SMBus(1) 
        return smbus
    except (FileNotFoundError, PermissionError) as error:
        raise IOError("ERROR: I2C 통신을 위한 시스템 관리 버스(SMBus) 초기화 실패") from error

# 배터리 잔량(SoC: State of Charge) 측정
# - MAX17043: I2C 통신을 통해 배터리 잔량 정보 제공
def get_battery_soc(smbus: smbus2.SMBus):
    try:
        raw_data = smbus.read_i2c_block_data(
            config.MAX17043_I2C_ADDRESS,
            config.MAX17043_SOC_REGISTER,
            2
        )
        soc_integer = raw_data[0]
        soc_fractional = raw_data[1] / 256.0
        return soc_integer + soc_fractional
    except OSError as error:
        raise IOError("ERROR: 배터리 모니터 IC(MAX17043)와 통신에 실패") from error