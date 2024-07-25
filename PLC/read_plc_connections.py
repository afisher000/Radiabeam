import pyads

# Connection parameters
ams_net_id = 'x.x.x.x.x.x'  # Replace with your PLC's AMS Net ID
ams_net_port = 851          # Typically, this is 851 for the first runtime

# Connect to the PLC
plc = pyads.Connection(ams_net_id, ams_net_port)

try:
    # Open the connection
    plc.open()
    
    # Get the list of all symbols
    symbols = plc.get_all_symbols()
    
    # Print all symbols
    for symbol in symbols:
        print(f'Name: {symbol.name}, Type: {symbol.type}, Comment: {symbol.comment}')
    
finally:
    # Close the connection
    plc.close()