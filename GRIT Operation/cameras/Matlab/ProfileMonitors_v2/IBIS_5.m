function IBIS_5(PM_n, pixelSize, callerHandle, PM_tag, SN, flip_v, flip_h)
% Created 24-February-2022
% This function will build a GUI to read from a single camera connected to the
% network.
% The major addition in this revision is adding more camera control buttons
% 05/16/2022 added h.AutoSave parametr instead of alwasys saving the image
% during the hardware tringgering
    
    h.PM_n = PM_n;
    h.Tag = PM_tag;
    h.SN = SN;
    h.name = append('IBIS Viewer. ', h.Tag);
    h.pixelSize=pixelSize;    %pixel size in millimeters
    h.divisor = 2;
    h.flip_v = flip_v;
    h.flip_h = flip_h;

    
%% ----------- Open Camera   
    h.vid = MakoCaller(PM_n);
    clear vidObj;
    h.camObj=get(h.vid,'Source');
    h.vid.ReturnedColorSpace='grayscale';
    h.vidRes = get(h.vid, 'VideoResolution');
    h.nBands = get(h.vid, 'NumberOfBands');
    h.autoSave = false;
    h.Threshold = 0;
    h.frameCounter = 0;
    
% triggerconfig(h.vid, 'manual');        % debug line. should be Hardware
%     h.vid.TriggerRepeat = 1000;            %   keep repeating trigger infinitely
                                    %^ move to initialization .m file
    h.vid.FramesPerTrigger = 1;       % each trigger should only give one image
            % this can't be used to configure averaging since  >1 will free
            % run after an initial trigger
              
    h.vid.FramesAcquiredFcnCount = 1;   % this can be changed to a larger number to average!
    h.vid.LoggingMode = 'memory';
    
    
    %% -------- create gui elements
    h.figure=figure(...             % first create the figure so that the handle can be passed to the m-file
        'PaperPositionMode','auto',...
        'Toolbar','figure',...
        'Menubar', 'none',...
        'NumberTitle','Off',...
        'Name', h.name,...
        'unit','pixels',...
        'Position',[100,100,200+h.vidRes(1)/h.divisor+125,280+h.vidRes(2)/h.divisor],...
        'CloseRequestFcn',{@CloseRequest_Callback}...
        );
    
    h=IBIS_initialization(h);   % calls the external script that sets up the GUI.

    % -- End of GUI element creation
    
    %% ----Set-up access to camera functions
        % Set numbers for the standard values for the shutter and gain
    
    h.CamCtrl.shutter.String=num2str(get(h.camObj,'ExposureTimeAbs'));
    h.CamCtrl.gain.String=num2str(get(h.camObj,'Gain'));
    

    
    %% ------ Specify acquisition callbacks
    h.vid.TriggerFcn = @TriggerFcn_Callback;     %called this way since it is local
                            % this is called whenever the camera is
                            % triggered
    h.vid.FramesAcquiredFcn = {@FramesAcquiredFcn_Callback,h};
                            % this will be called when all the frames are
                            % acquired. This is the best callback to use
                            % to process data
    

        start(h.vid);
        % start camera operation and gain exclusive use to to allow (but 
        % not start) for acquiring image data this also calls the video
        % object's StartFcn callback

    if triggerconfig(h.vid).TriggerType == "manual"
        trigger(h.vid)
    end


    %% ---Helper Functions
    function stampedpath=timepath(timestamp,header)
        stampstr=datestr(timestamp,'yyyymmddTHHMMSS_FFF');
        stampedpath=string([header, stampstr]);
    end

    %% ---- ALL the GUI callbacks
    function CloseRequest_Callback(~,~)
%         stoppreview(vid)        
        callerHandle.Enable='on';   % allow button interaction
        callerHandle.Value=callerHandle.Min;    %set the button to high
        stop(h.vid)
        delete(h.vid)
        clear h.vid
        delete(h.figure)
    end

%% ------Image Acquisition callbacks
    function TriggerFcn_Callback(~,~)
%         disp('triggered')
%         pause(1)
%         vid.Logging
    end
    function StartFcn(obj, event)
        disp('startFcn called')
%         trigger(h.vid)
    end

%% ------ ND Filter Wheel Callbacks
    
end