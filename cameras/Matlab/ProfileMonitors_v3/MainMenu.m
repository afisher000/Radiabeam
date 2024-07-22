function MainMenu()
    % Last edited July 19-2024
    % This function sets up a menu of buttons that when clicked, open guis
    % for individual cameras.

    %% ToDo
    % Why is colorfilter tag set to "clear" before saving images?

    %% Defaults and add paths
    addpath( fullfile(pwd, 'Callback Functions') );
    addpath( fullfile(pwd, 'Calculation Functions') );
    datetime.setDefaultFormats('defaultdate','yyyy-MM-dd');

    %% Connect to cameras
    % Reset any existing connections
    if not(isempty(imaqfind))
        imaqreset
    end

    % Connect and read camera settings
    vids    = imaqhwinfo('gige');
    nvids   = length(vids.DeviceInfo);
    for i=1:nvids
        vid             = videoinput('gige', i);
        h.cameras(i)    = get_camera_settings(vid);
    end
    
    %% Create Menu figure and buttons
    h.figure=figure(...
        'PaperPositionMode','auto',...
        'Toolbar','none',...
        'Menubar', 'none',...
        'NumberTitle','Off',...
        'Units','Characters',...
        'Name','PM Selector'...
        );

    buttonCount = 7; %specify number of menu buttons
    for j=1:nvids
        % button index (1 is top, N is bottom)
        button_index    = buttonCount-h.cameras(j).GUIpos+1;
        button_position = [0.02, 0.025+0.98*(button_index-1)/buttonCount ,0.95, 0.95/buttonCount ];

        h.camera_buttons(j) = uicontrol(h.figure,...
            'Style','togglebutton',...
            'String',h.cameras(j).Tag,...
            'Units','normalized',...
            'Position',button_position);
    end

    %% Define Callback Functions
    % Do last so h fields have been defined.
    set(h.figure, 'CloseRequestFcn', @(source, eventID) Menu_CloseRequest_Callback(source, eventID, h));

    for j=1:nvids
        set(h.camera_buttons(j), 'Callback', @(source, eventID) Menu_Button_Callback(source, eventID, h.cameras(j)));
    end
 

end