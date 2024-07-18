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
        vid         = videoinput('gige', i);
        h.cameras(i)  = get_camera_settings(vid);
    end
    
    %% Create buttons in main gui with callback
    buttonCount = 7;

    % Positions are normalized to parent window
    BtnPositions=zeros(4,buttonCount);
    for i=1:buttonCount
        BtnPositions(:,i) = [0.02, 0.025+0.98*(i-1)/buttonCount ,0.95, 0.95/buttonCount ];
    end

    for i=1:nvids
        h.guis(i) = uicontrol(h.figure,...
            'Style','togglebutton',...
            'String',h.cameras(i).Tag,...
            'Callback',@(source, eventID) PM_Callback(source, eventID, h.cameras(i)), ...
            'Units','normalized',...
            'Position',BtnPositions(:,buttonCount-h.cameras(i).GUIpos+1 ));
    end
 

    %% Callbacks
    function CloseRequest_Callback(~,~)
        % Called when menu figure closed
        delete(h.figure)
        imaqreset;
    end

    function PM_Callback(source, ~, camera)
        fprintf('%s\n', camera.Tag);
        
        if source.Value
            IBIS_6(camera);
            source.Enable='off';
        else
            msgbox('This Screen is already activated.');    
        end

        %this function would call the GUI refering to the PM_number passed
        %IBIS_4(PM_number)
        %IFW(PM_number)
%         if source.Value
%             j=find(strcmp(eventID.Source.String,h.PM_n.Tag));
%             IBIS_5(h.PM_n.n(j), ...
%                 h.PM_n.pixelCalibration(j), ...
%                 h.PM_n.h(j), ...
%                 h.PM_n.Tag{j}, ...
%                 h.PM_n.SN{j}, ...
%                 h.PM_n.flip_v(j), h.PM_n.flip_h(j));
%             source.Enable='off';
%         else
%             f = msgbox('This Screen is already activated.');    
%         end
    end
end