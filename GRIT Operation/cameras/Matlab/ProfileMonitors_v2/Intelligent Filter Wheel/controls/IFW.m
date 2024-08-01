classdef IFW
    % IFW is a calss to interact with the IFW filter wheel.
    % It makes use of M. Kravchenko's "IFW_backend" work to make a portable
    % version.

    properties (Access = protected)
        COM
        SERIAL_N
        s
    end

    properties
        device_ID
    end

    properties (Constant)
        b_rate = 19200; % baud rate
        timeout = 5;    % timeout time in seconds
    end

    methods
        function obj = IFW(device_ID)
        % IFW Class constructor. Requires device_ID, an integer
        % corresponding to a particular location on the beamline. It
        % creates a serial port object (s), stores the serial COM port, and
        % the SERIAL_N serial number
            if nargin == 1
                obj.device_ID = device_ID;
            end
            [obj.SERIAL_N, obj.COM] = readParams(obj.device_ID);     %call helper method to correlate requested device_ID with SN and COM port
            s = serialport(obj.COM,b_rate,"Timeout",timeout);
            configureTerminator(s,"CR/LF");
            writeline(s, "WSMODE");
            pause(0.1);
            out = read(s,1,"string");
            if out == "!"
                % disp("SUCCESS!")
                return
            else
                error('IFW Initialization failed')
            end
        end
    end

    methods (Access = private)
        function obj = readParams(deviceID)
        % This function reads parametrs from a "settings.txt"
        % Function finds the "DEVICE_ID=X" line and reads two following lines
        % with "SERIAL_N=XXXXXX" and "COMPORT=COMX" returnung the numerical 
        % serial number and COM port nubler.
            settings_data = importdata('settings.txt','\n');
            row_idx = find(~cellfun('isempty',strfind(settings_data,'DEVICE_ID=' + string(device_ID))));
            SERIAL_N = str2double(arrayfun(@(x) regexp(settings_data{x}, '\d+', 'match'),row_idx + 1));
            COM = 'COM' + string(arrayfun(@(x) regexp(settings_data{x}, '\d+', 'match'),row_idx + 2));
            clear settings_data row_idx
        end
    end
end