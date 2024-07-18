function MainGui()

    %% Defaults
    datetime.setDefaultFormats('defaultdate','yyyy-MM-dd');

    %% Create main window
    h.figure=figure(...
        'PaperPositionMode','auto',...
        'Toolbar','none',...
        'Menubar', 'none',...
        'NumberTitle','Off',...
        'Units','Characters',...
        'Name','PM Selector',...
        'CloseRequestFcn',{@CloseRequest_Callback}...
        );

    %% Connect to cameras
    if not(isempty(imaqfind))
        disp('cameras already connected. Resetting all cameras')
        imaqreset
    end

    vids    = imaqhwinfo('gige');
    nvids   = length(vids.DeviceInfo);

    for i=1:nvids
        vid             = videoinput('gige', i);
        h.cameras(i)    = get_camera_settings(vid);
    end
    
    %% Create buttons in main gui with callback
    buttonCount = 7;

    % Positions are normalized to parent window
    BtnPositions=zeros(4,buttonCount);
    for i=1:buttonCount
        BtnPositions(:,i) = [0.02, 0.025+0.98*(i-1)/buttonCount ,0.95, 0.95/buttonCount ];
    end

    for j=1:nvids
        h.guis(j) = uicontrol(h.figure,...
            'Style','togglebutton',...
            'String',h.cameras(j).Tag,...
            'Callback',@(source, eventID) PM_Callback(source, eventID, j), ...
            'Units','normalized',...
            'Position',BtnPositions(:,buttonCount-h.cameras(j).GUIpos+1 ));
    end
 

    %% Callbacks
    function CloseRequest_Callback(~,~)
        % Called when menu figure closed
        delete(h.figure)
        imaqreset;
    end

    
    function PM_Callback(source, ~, j)
        % Called when buttons clicked
        camera  = h.cameras(j);
        gui     = h.guis(j); 
        fprintf('%s\n', camera.Tag);
        
        if source.Value
            IBIS_6(camera, gui);
            source.Enable='off';
        else
            msgbox('This Screen is already activated.');    
        end
    end
end