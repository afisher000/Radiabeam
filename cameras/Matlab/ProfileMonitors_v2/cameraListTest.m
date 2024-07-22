function PM_n=cameraListTest()
numStns=7;
if not(isempty(imaqfind))
    %this will run when there are already cameras connected
    disp('cameras already connected. Resetting all cameras')
    imaqreset
    % imaqmex('feature', '-gigeDisablePacketResend', true);
end

vids=imaqhwinfo('gige');
nvids=length(vids.DeviceInfo);    % number of video devices found


% PM_n.pixelCalibration(1:numStns)=5.0*(150/50)/1024;
PM_n.n(1:numStns)=0;
for i=1:numStns
    PM_n.Tag{i}='';
    PM_n.SN{i}='';
end

for i=1:nvids
    vid=eval(vids.DeviceInfo(i).VideoInputConstructor);
    vidSrc=vid.Source;
    switch vidSrc.DeviceID   %vidSrc.DeviceID is the cam's serial number
        case '50-0537011139'
            n = (numStns+1) - 1;
            PM_n.Tag{n}='Cam 01';
            PM_n.pixelCalibration(n)=18/736; % 5.6*(150/50)/1024;
            PM_n.n(n)=vid.DeviceID;
            PM_n.SN{n}='50-0537011139';
            PM_n.flip_v(n) = false;
            PM_n.flip_h(n) = false;
            PM_n.filter_port = 'COM2';

        case '50-0537035519'
            n = (numStns+1) - 2;
            PM_n.Tag{n}='Cam 02';
            PM_n.pixelCalibration(n)=18/1029; % 5.4*(150/50)/1024;
            PM_n.n(n)=vid.DeviceID;
            PM_n.SN{n}='50-0537035519';
            PM_n.flip_v(n) = false;
            PM_n.flip_h(n) = false;
            PM_n.filter_port = 'COM4';

        case '50-0536999326'
            n = (numStns+1) - 3;
            PM_n.Tag{n}='Laser';
            PM_n.pixelCalibration(n) = 17.5/1024; % 5.0*(150/50)/1024;
            PM_n.n(n)=vid.DeviceID;    %vids.DeviceID is not the SN, but is the videoInputObject's ID number
            PM_n.SN{n}='50-0536999326';
            PM_n.flip_v(n) = true;
            PM_n.flip_h(n) = false;
            PM_n.filter_port = 'COM5';

%         case '50-0536999271'
%             n = (numStns+1) - 4;
%             PM_n.Tag{n}='IP region 01';
%             PM_n.pixelCalibration(n)=18/1024; %5.2*(150/50)/1024;
%             PM_n.n(n)=vid.DeviceID;
%             PM_n.SN{n}='50-0536976126';
%             PM_n.flip_v(n) = true;
%             PM_n.flip_h(n) = true;
%             PM_n.filter_port = 'COM99'; 

        case '50-0536976126'
            n = (numStns+1) - 5;
            PM_n.Tag{n}='IP region 02';
            PM_n.pixelCalibration(n)=18/1024; %5.2*(150/50)/1024;
            PM_n.n(n)=vid.DeviceID;
            PM_n.SN{n}='50-0536976126';
            PM_n.flip_v(n) = false;
            PM_n.flip_h(n) = false;
            PM_n.filter_port = 'COM7';

%         case '50-0999999999'
%             n = (numStns+1) - 6;
%             PM_n.Tag{n}='IP region 03';
%             PM_n.pixelCalibration(n)=18/1024; %5.2*(150/50)/1024;
%             PM_n.n(n)=vid.DeviceID;
%             PM_n.SN{n}='50-0536976126';
%             PM_n.flip_v(n) = false;
%             PM_n.flip_h(n) = true;
%             PM_n.filter_port = 'COM6';

        case '50-0536999325'
            n = (numStns+1) - 7;
            PM_n.Tag{n}='Beam Dump';
            PM_n.pixelCalibration(n)=18/1074; % 5.8*(150/50)/1024;
            PM_n.n(n)=vid.DeviceID;
            PM_n.SN{n}='50-0536999325';
            PM_n.flip_v(n) = true;
            PM_n.flip_h(n) = true; %
            PM_n.filter_port = 'COM7';

        otherwise
            disp('camera found without a known assignment')
    end
    clear vidSrc
    delete(vid)
end
end

