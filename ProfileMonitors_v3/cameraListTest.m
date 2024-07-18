function cameras=cameraListTest()

% If cameras already connected, reset, then load devices
if not(isempty(imaqfind))
    disp('cameras already connected. Resetting all cameras')
    imaqreset
end
vids    = imaqhwinfo('gige');


% Initialize cameras structure
nvids   = length(vids.DeviceInfo);
cameras.n(1:nvids)=0;
for i=1:nvids
    cameras.Tag{i}='';
    cameras.SN{i}='';
end

% Loop over video devices
for i=1:nvids
    vid     = videoinput('gige', i);
    vidSrc  = vid.Source;
    
    switch vidSrc.DeviceID   %vidSrc.DeviceID is the cam's serial number
        case '50-0537011139'
            n = (nvids+1) - 1;
            cameras.Tag{n}='Cam 01';
            cameras.pixelCalibration(n)=18/736; % 5.6*(150/50)/1024;
            cameras.n(n)=vid.DeviceID;
            cameras.SN{n}='50-0537011139';
            cameras.flip_v(n) = false;
            cameras.flip_h(n) = false;
            cameras.filter_port = 'COM2';

        case '50-0537035519'
            n = (nvids+1) - 2;
            cameras.Tag{n}='Cam 02';
            cameras.pixelCalibration(n)=18/1029; % 5.4*(150/50)/1024;
            cameras.n(n)=vid.DeviceID;
            cameras.SN{n}='50-0537035519';
            cameras.flip_v(n) = false;
            cameras.flip_h(n) = false;
            cameras.filter_port = 'COM4';

        case '50-0536999326'
            n = (nvids+1) - 3;
            cameras.Tag{n}='Laser';
            cameras.pixelCalibration(n) = 17.5/1024; % 5.0*(150/50)/1024;
            cameras.n(n)=vid.DeviceID;    %vids.DeviceID is not the SN, but is the videoInputObject's ID number
            cameras.SN{n}='50-0536999326';
            cameras.flip_v(n) = true;
            cameras.flip_h(n) = false;
            cameras.filter_port = 'COM5';

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
            n = (nvids+1) - 5;
            cameras.Tag{n}='IP region 02';
            cameras.pixelCalibration(n)=18/1024; %5.2*(150/50)/1024;
            cameras.n(n)=vid.DeviceID;
            cameras.SN{n}='50-0536976126';
            cameras.flip_v(n) = false;
            cameras.flip_h(n) = false;
            cameras.filter_port = 'COM7';

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
            n = (nvids+1) - 7;
            cameras.Tag{n}='Beam Dump';
            cameras.pixelCalibration(n)=18/1074; % 5.8*(150/50)/1024;
            cameras.n(n)=vid.DeviceID;
            cameras.SN{n}='50-0536999325';
            cameras.flip_v(n) = true;
            cameras.flip_h(n) = true; %
            cameras.filter_port = 'COM7';

        otherwise
            disp('camera found without a known assignment')
    end
    clear vidSrc
    delete(vid)
end
end

