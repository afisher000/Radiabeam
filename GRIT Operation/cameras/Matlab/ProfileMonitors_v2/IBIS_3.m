function vid=IBIS_3(varargin)
% Created 19-March-2021
% This function will build a GUI to read from a single camera connected to the
% network.
% The major addition in this revision is adding more camera control buttons

    h.divisor = 3;
%% ----------- Open Camera   
    
%     vid=videoinput('winvideo',1,'RGB24_1280x960');
    
    h.vid = MakoTester_20210319_Mono10_10Hz;
    h.camObj=get(h.vid,'Source');
    h.vid.ReturnedColorSpace='grayscale';
    h.vidRes = get(h.vid, 'VideoResolution');
    h.nBands = get(h.vid, 'NumberOfBands');  
    
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
        'Name','IBIS Viewer',...
        'unit','pixels',...
        'Position',[5,5,200+h.vidRes(1)/h.divisor+100,200+h.vidRes(2)/h.divisor],...
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
    
    % -- main runtime execution here
        start(h.vid);     % start camera operation and gain exclusive use to
                        % to allow (but not start) for acquiring image data
                        % this also calls the video objects StartFcn
                        % callback
%      disp('lets go!');
     trigger(h.vid)
    % -- end of main runtime execution

    %% ---Helper Functions
    function stampedpath=timepath(timestamp,header)
        stampstr=datestr(timestamp,'yyyymmddTHHMMSS_FFF');
        stampedpath=string([header, stampstr]);
    end

    %% ---- ALL the GUI callbacks
    function CloseRequest_Callback(~,~)
%         stoppreview(vid)        
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