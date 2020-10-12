"""Constants for the Smart Ball integration."""

DOMAIN = "smart_ball"

# units
DEGREE = "°"
TEMP_CELSIUS = f"{DEGREE}C"

# device types
DEVICE_CLASS_LDR = "LDR_SENSOR"
DEVICE_CLASS_IRRemote = "IRRemote"
DEVICE_CLASS_TEMPERATURE = "Temperature"
DEVICE_CLASS_HUMIDITY = "Humidity"
DEVICE_CLASS_MOTION = "Motion"
DEVICE_CLASS_UPTIME = "Uptime"
DEVICE_CLASS_MOTION_BINARY = "Motion_Binary"
DEVICE_CLASS_IRRemote_BINARY = "IR_Binary"

# const settings
BINARY_SENSOR_STABLE_TIME = 10
REFRESH_INTERVAL = 5
