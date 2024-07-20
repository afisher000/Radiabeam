function open_camera(camera, source)
    % Last edited July 19-2024
    % This function opens a camera and setups up a GUI.

    %% Create h struct
    h.camera        = camera;
    h.source        = source;
    h.divisor       = 2; % scales size of camera image

    %% Define Image Directory
    date_string = datestr(now, 'yyyy-mmmm-dd');
    h.image_dir = fullfile(pwd, 'Saved Images', date_string, h.camera.Tag);

    if ~exist(h.image_dir, 'dir')
       mkdir(h.image_dir);
    end
    
    %% Open Camera   
    h.vid                         = MakoCaller(camera.ID);
    clear vidObj;
    h.camObj                      = get(h.vid,'Source');
    h.vid.ReturnedColorSpace      ='grayscale';
    h.vidRes                      = get(h.vid, 'VideoResolution');
    h.nBands                      = get(h.vid, 'NumberOfBands');
    h.autoSave                    = false;
    h.Threshold                   = 0;
    h.frameCounter                = 0;

    h.vid.FramesPerTrigger        = 1;   % each trigger gives 1 frame
    h.vid.FramesAcquiredFcnCount  = 1;   % change this to average more shots
    h.vid.LoggingMode             = 'memory';
    
    %% Connect to filter-wheel
    try
        h.objIFW = IFW(h.camera);
        h.objIFW.filterTAG = 'Clear';
    catch exception
        disp('Failed to connect to Filter Wheel');
    end

    %% Print temperature
    temperature = int16(get(h.camObj, 'DeviceTemperature'));
    fprintf('Temperature: %d C.\n',temperature);

    %% Create gui figure and initialize elements
    h = setup_camera_gui(h);
    
    %% Set camera properties
    h.CamCtrl.shutter.String  = num2str(get(h.camObj,'ExposureTimeAbs'));
    h.CamCtrl.gain.String     = num2str(get(h.camObj,'Gain'));
    
    
    %% Specify acquisition callbacks
    % When camera is triggered...
    h.vid.TriggerFcn          = @TriggerFcn_Callback; %called when camera is triggered

    % When frames are acquired... (use for data processing)
    h.vid.FramesAcquiredFcn   = @(source, eventID) FramesAcquiredFcn_Callback(source, eventID, h);

    %% Start camera operation
    start(h.vid); %calls h.vid StartFcn callback


    %% Debugging 
%     triggerconfig(h.vid, 'manual');    % Should be 'hardware'
%     h.vid.TriggerRepeat = 1000;        %  keep repeating trigger infinitely
% 
%     if triggerconfig(h.vid).TriggerType == "manual"
%         trigger(h.vid)
%     end

    
end