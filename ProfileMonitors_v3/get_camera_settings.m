function camera_settings = get_camera_settings(vid)
    vidSrc  = vid.Source;

    switch vidSrc.DeviceID   %vidSrc.DeviceID is the cam's serial number

        case '50-0537011139'
            camera_settings.GUIpos = 1;
            camera_settings.ID      = vid.DeviceID;
            camera_settings.Tag = 'Cam 01';
            camera_settings.pixelCalibration    = 18/736; % 5.6*(150/50)/1024;
            camera_settings.SN = vidSrc.DeviceID;
            camera_settings.flip_v = false;
            camera_settings.flip_h = false;
            camera_settings.filter_port = 'COM2';

        case '50-0537035519'
            camera_settings.GUIpos = 2;
            camera_settings.Tag = 'Cam 02';

            camera_settings.ID      = vid.DeviceID;
            camera_settings.pixelCalibration    = 18/1029; % 5.4*(150/50)/1024;
            camera_settings.SN = vidSrc.DeviceID;
            camera_settings.flip_v = false;
            camera_settings.flip_h = false;
            camera_settings.filter_port = 'COM4';
            
        case '50-0536999326'
            camera_settings.GUIpos = 3;
            camera_settings.Tag = 'Laser';

            camera_settings.ID      = vid.DeviceID;
            camera_settings.pixelCalibration    = 17.5/1024; % 5.0*(150/50)/1024;
            camera_settings.SN = vidSrc.DeviceID;
            camera_settings.flip_v = true;
            camera_settings.flip_h = false;
            camera_settings.filter_port = 'COM5';

        case '50-0536976126'
            camera_settings.GUIpos = 5;
            camera_settings.Tag = 'IP region 02';

            camera_settings.ID      = vid.DeviceID;
            camera_settings.pixelCalibration    = 18/1024; %5.2*(150/50)/1024;
            camera_settings.SN = vidSrc.DeviceID;
            camera_settings.flip_v = false;
            camera_settings.flip_h = false;
            camera_settings.filter_port = 'COM7';

        case '50-0536999325'
            camera_settings.GUIpos = 7;
            camera_settings.Tag = 'Beam Dump';

            camera_settings.ID      = vid.DeviceID;
            camera_settings.pixelCalibration    = 18/1074; % 5.8*(150/50)/1024;
            camera_settings.SN = vidSrc.DeviceID;
            camera_settings.flip_v = true;
            camera_settings.flip_h = true;
            camera_settings.filter_port = 'COM7';


        otherwise
            disp('camera found without a known assignment')
    end
end