classdef IFW_2
    % IFW is a calss to interact with the IFW filter wheel.
    % It makes use of M. Kravchenko's "IFW_backend" work to make a portable
    % version.

    properties (Access = protected)

    end

    properties
        device_ID
        filterID
        filterTAG 
        COM
        SERIALN
        s
    end

    properties (Constant)
        b_rate = 19200; % baud rate
        timeout = 5;    % timeout time in seconds
    end

    methods
        function obj = IFW_2(device_ID, tag)
        % IFW Class constructor. Requires device_ID, an integer
        % corresponding to a particular location on the beamline. It
        % creates a serial port object (s), stores the serial COM port, and
        % the SERIAL_N serial number
            if nargin == 1
                obj.device_ID = device_ID;
            end      

            fprintf('Device_ID = %d\n', device_ID);
            % [obj.SERIAL_N, obj.COM] = obj.readParams(obj.device_ID);     %call helper method to correlate requested device_ID with SN and COM port
            settings_data = importdata('IFW_settings.txt','\n');
            % row_idx = find(~cellfun('isempty',strfind(settings_data,'DEVICE_ID=' + string(obj.device_ID)))); %#ok<STRCL1> 
%             row_idx = find(~cellfun('isempty',strfind(settings_data,append('CAMERA_SN=', device_ID)))); %#ok<STRCL1> 
            row_idx = find(~cellfun('isempty',strfind(settings_data,append('CAMERA_SN=', string(device_ID) )))); %#ok<STRCL1> edited by Andrew

            obj.SERIALN = str2double(arrayfun(@(x) regexp(settings_data{x}, '\d+', 'match'),row_idx + 1));
            obj.COM = 'COM' + string(arrayfun(@(x) regexp(settings_data{x}, '\d+', 'match'),row_idx + 2));    


            % Hardcode IFW settings
            switch tag
                case 'Cam 01'
                    obj.COM = 'COM2';
                case 'Cam 02'
                    obj.COM = 'COM4';
                case 'Beam Dump'
                    obj.COM = 'COM7';
                otherwise
                    error('Camera settings not given in IFW.m switch statement.');
            end


            obj.s = serialport(obj.COM, obj.b_rate,"Timeout", obj.timeout);

            configureTerminator(obj.s,"CR/LF");
            writeline(obj.s, "WSMODE");
            pause(0.1);
            out = "default";
            try
                out = read(obj.s,1,"string");
            catch warning
                warning('Could not get response from IFW driver');
                throw(warning);
                return
            end

            try
                if out == "!"
                    % disp("SUCCESS!")
                    writeline(obj.s, "WFILTR");
                    pause(0.1);
                    obj.filterID = str2double(regexp(read(obj.s, 4,"string"), '\d*', 'match', 'once'));
                    pause(0.1);
                    writeline(obj.s, "WHOME");
                    return
                end
            catch exception
                throw(exception);
            end
        end

        function turnWheel(obj)
        % This function intilializes the turn of a IFW to a chosen position
            if obj.filterID > 5 | obj.filterID < 1
                disp("ERROR! Wrong value of filter position")
            end
            writeline(obj.s, "WFILTR");
            % current_filter_ID = (regexp(read(obj.s, 4,"string"), '\d*', 'match', 'once'));
            % fprintf('Curent Filter Position: %s\n',current_filter_ID);
            % fprintf('Desired Filter Position: %d\n',obj.filterID);
            pause(0.2);
            writeline(obj.s, "WGOTO"+obj.filterID);
            % pause(5);
            % output = regexp(read(obj.s,2,"string"), '*', 'match');
            % if output == "*"
            %     writeline(obj.s, "WFILTR");
            %     pause(0.1);
            %     % obj.filterID = str2double(regexp(read(obj.s,  4,"string"), '\d*', 'match', 'once'));
            % end
            
            
            clear device_ID position filter_ID
        end

        function readParams(obj)
        % This function reads parametrs from a "IFW_settings.txt"
        % Function finds the "DEVICE_ID=X" line and reads two following lines
        % with "SERIAL_N=XXXXXX" and "PORT=COMX" returnung the numerical 
        % serial number and COM port nubler.
            settings_data = importdata('IFW_settings.txt','\n');
            row_idx = find(~cellfun('isempty',strfind(settings_data,'DEVICE_ID=' + string(obj.device_ID)))); %#ok<STRCL1> 
            % row_idx = find(~cellfun('isempty',strfind(settings_data,'CAMERA_SN=' + string(deviceID))));
            obj.SERIALN = str2double(arrayfun(@(x) regexp(settings_data{x}, '\d+', 'match'),row_idx + 2));
            obj.COM = 'COM' + string(arrayfun(@(x) regexp(settings_data{x}, '\d+', 'match'),row_idx + 3));
            clear settings_data row_idx
        end

        function filterID = getFilterID(obj)
            writeline(obj.s, "WFILTR");
            pause(0.2)
            filterID = str2double(regexp(read(obj.s, 4,"string"), '\d*', 'match', 'once'));
        end    
        
        function closeCOM(obj)
            obj.s
        end
    end
end