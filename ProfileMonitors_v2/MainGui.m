function MainGui()

    datetime.setDefaultFormats('defaultdate','yyyy-MM-dd');
   
    % Create camera menu figure
    h.figure=figure(...
        'PaperPositionMode','auto',...
        'Toolbar','none',...
        'Menubar', 'none',...
        'NumberTitle','Off',...
        'Units','Characters',...
        'Name','PM Selector',...
        'CloseRequestFcn',{@CloseRequest_Callback}...
        );


    h.PM_n=cameraListTest;      % Call helper script to find all cameras

    % Build buttons
    buttonCount=7;
    BtnPositions=zeros(4,buttonCount);
    for j=1:buttonCount
        BtnPositions(:,j) = [0.02, 0.025+0.98*(j-1)/buttonCount ,0.95, 0.95/buttonCount ];
    end


    for j=1:buttonCount
        h.PM_n.h(j) = uicontrol(h.figure,'Style','togglebutton',...
                    'String',h.PM_n.Tag{j},...
                    'Callback',{@PM_Callback},...
                    'Units','normalized',...
                    'Position',BtnPositions(:,j));
    end
 

    %% Callback functions
    function CloseRequest_Callback(~,~)
        %called when the figure is closed. Will likely close all of the
        %cameras and serial connections
        delete(h.figure)
        
    end

    function PM_Callback(source, eventID)
        %this function would call the GUI refering to the PM_number passed
        %IBIS_4(PM_number)
        %IFW(PM_number)
        if source.Value
            j=find(strcmp(eventID.Source.String,h.PM_n.Tag));
            IBIS_5(h.PM_n.n(j), ...
                h.PM_n.pixelCalibration(j), ...
                h.PM_n.h(j), ...
                h.PM_n.Tag{j}, ...
                h.PM_n.SN{j}, ...
                h.PM_n.flip_v(j), h.PM_n.flip_h(j));
            source.Enable='off';
            % disp(h.PM_n.n(j));
            % IFW(h.PM_n.n(j))
        else
            f = msgbox('This Screen is already activated.');    
        end
    end
end