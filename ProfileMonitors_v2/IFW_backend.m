% This file contain functions to operate IFW
% Maksim Kravchenko & Marcos Ruelas, RadiaBeam Technologies, 2022
% 
% Init date 02/24/2022
%
% Documentation for IFW device: https://optecinc.com/astronomy/catalog/ifw/images/17350_manual.pdf 
% 
% All functions use device_ID for connection with a certain COM port, that 
% should be configured in "IFW_settings.txt" file

disp("TESTING: returnHome")
returnHome(1);
checkStatus(1);
disp("TESTING: turnFilter")
turnFilter(1,"l");
checkStatus(1);
disp("TESTING: chooseFilter")
chooseFilter(1,3);
checkStatus(1);
disp("TESTING: returnHome")
returnHome(1);
checkStatus(1);


function [filter_ID] = returnHome(device_ID)
clear s:
s = initIFW(device_ID);
writeline(s, "WHOME");
pause(20);
writeline(s, "WFILTR");
pause(0.1);
filter_ID = read(s,4,"string");
% filter_ID = str2double(regexp(read(s,4,"string"), '\d*', 'match', 'once'));
% disp(filter_ID);
end


function [filter_ID] = chooseFilter(device_ID, filter_n)
% This function turns filter wheel to the specifed in "filter_n" position
    if filter_n > 5 | filter_n < 1
        disp("ERROR! Wrong value of filter position")
    end
    clear s;
    s = initIFW(device_ID);
    writeline(s, "WFILTR");
    pause(0.1);
    filter_ID = str2double(regexp(read(s,4,"string"), '\d*', 'match', 'once'));
    pause(0.1);
    writeline(s, "WGOTO"+filter_n);
    pause(15);
    output = regexp(read(s,2,"string"), '*', 'match');
    if output == "*"
        writeline(s, "WFILTR");
        pause(0.1);
        filter_ID = str2double(regexp(read(s,4,"string"), '\d*', 'match', 'once'));
        disp("SUCCESS");
    end
end


function [filter_ID] = turnFilter(device_ID, direction)
% This functions sends a signal to IFW to make single turn clockwise(right)
% or contrclockwise(left) and returns current position of filter wheel
    clear s;
    s = initIFW(device_ID);
    writeline(s, "WFILTR");
    pause(0.1);
    filter_ID = str2double(regexp(read(s,4,"string"), '\d*', 'match', 'once'));
    if direction == "left" | direction == "l"
        filter_ID = abs(filter_ID - 1);
        if filter_ID < 1 
            filter_ID = 5;
        end
    end
    if direction == "right" | direction == "r"
        filter_ID = filter_ID + 1;
        if filter_ID > 5
            filter_ID = 1;
        end
    end
    writeline(s, "WGOTO"+string(filter_ID));
    pause(5);
    writeline(s, "WFILTR");
    pause(0.1);
    filter_ID = str2double(regexp(read(s,4,"string"), '\d*', 'match', 'once'));
end


function [filter_ID] = checkStatus(device_ID)
% This functiob returns "filter_ID" wich is currently 
% set on the IFW assigned to the "device_ID"
% The "device_ID" for each IFW must be congidured in "IFW_settings.txt"
[SER, COM] = readParams(device_ID);
clear s;
s = initIFW(device_ID);
writeline(s, "WFILTR");
pause(0.02);
filter_ID = str2double(regexp(read(s,4,"string"), '\d*', 'match', 'once'));
disp(filter_ID);
end


function [s] = initIFW(device_ID)
[SER, COM] = readParams(device_ID);
s = serialport(COM,19200,"Timeout",5);
configureTerminator(s,"CR/LF");
writeline(s, "WSMODE");
pause(0.1);
out = read(s,1,"string");
if out == "!"
    % disp("SUCCESS!")
    return
else
    disp("ERROR! Initialization failed")
end
end


function [SERIAL_N, COM] = readParams(device_ID)
% This function reads parametrs from a "IFW_settings.txt"
% Function finds the "DEVICE_ID=X" line and reads two following lines
% with "SERIAL_N=XXXXXX" and "COMPORT=COMX" returnung the numerical 
% serial number and COM port nubler.
    settings_data = importdata('IFW_settings.txt','\n');
    row_idx = find(~cellfun('isempty',strfind(settings_data,'DEVICE_ID=' + string(device_ID))));
    SERIAL_N = str2double(arrayfun(@(x) regexp(settings_data{x}, '\d+', 'match'),row_idx + 2));
    COM = 'COM' + string(arrayfun(@(x) regexp(settings_data{x}, '\d+', 'match'),row_idx + 3));
end



