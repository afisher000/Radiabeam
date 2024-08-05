import serial
import time

# ICT and serial settings
port = 'COM1'
baudrate = 115200
termination = '\n\0'
Qcal = 0.005 # picoCoulombs
Ucal = 0.8722100 # volts


with serial.Serial(port=port, baudrate=baudrate) as ser:
    # Wait for connection
    time.sleep(2)

    # Flush buffer
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # Continuously poll
    while True:
        if ser.in_waiting: # ie. byte in buffer
            buffer = ser.readline().decode('utf-8')
            
            # Maybe have received multiple responses
            for response in buffer.split(termination):

                # Voltage sample indicated by 'A' prefix
                # Ex: 'A0:0123=00123ABC\n\0'
                # or '{frame_type}{frame_number}:{4_char_counter}={8_char_value}{terminator}'
                if response[0]=='A':
                    hex_value = response[8:]
                    volts = int(hex_value, 16) # Convert from microVolts

                    # Apply calibration
                    charge = Qcal * 10**(volts / Ucal) #picoCoulombs




