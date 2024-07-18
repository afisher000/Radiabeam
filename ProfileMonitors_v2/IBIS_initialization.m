
function h=IBIS_initialization(h)
% Created 7-April-2021, modified 25-Feb-2022. Only works with _v4 and
% beyond of IBIS
% This m-file sets up the GUI items, such as buttons, etc.
    
    h.roordir = 'C:\Users\Marcos\Desktop\GRIT PM images\'; % This is the root directory for saving images
    date = datetime('today','Format','uuuu-MM-dd');
    disp(date);
    day = datestr(date,'yyyy-mmmm-dd');
    disp(day);
    h.df = strcat(h.roordir, h.Tag, '\', day);
    h.dfc = strcat(h.roordir, h.Tag, '\', day, '\Color');
    disp(h.df);
    if ~exist(h.df, 'dir')
       mkdir(h.df);
    end
    if ~exist(h.dfc, 'dir')
        mkdir(h.dfc);
    end
    
    try
        objIFW = IFW_2(h.PM_n, h.Tag);
%         objIFW = IFW(h.PM_n);
%         objIFW = IFW(h.filter_port);
        objIFW.filterTAG = 'Clear';
    catch exception
        fprintf('Exception Stack:\n')
        for j=1:length(exception.stack)
            fprintf('\tScript = %s\n', exception.stack(j).name);
            fprintf('\tLine = %d\n', exception.stack(j).line);
        end

        disp('Failed to connect to Filter Wheel');
    end

    bitdepth=get(h.camObj, 'BitDepth') ;
    custom_cmap = false;

    temp = int16(get(h.camObj, 'DeviceTemperature'));
    fprintf('Temperature: %d C.\n',temp);
    
    %% --Image Axes
    corner=[50,100];
    h.axes = axes('Units','pixels',...
                'Tag', 'MainImageView',...
                'PositionConstraint', 'InnerPosition',...
                'Position',[corner(1),corner(2),h.vidRes(1)/h.divisor,h.vidRes(2)/h.divisor]);
    h.X_worldLimit=h.pixelSize*h.vidRes(1)/2 *[-1, 1];
    h.Y_worldLimit=h.pixelSize*h.vidRes(2)/2 *[-1, 1];
    
    h.RA = imref2d([h.vidRes(2), h.vidRes(1)],h.X_worldLimit,h.Y_worldLimit);
%     h.RA
    h.Image = imshow(2^bitdepth*ones(h.vidRes(2), h.vidRes(1), h.nBands),...
                    h.RA,'Parent',h.axes);
    h.Image.YData=-1*h.Image.YData;
    set(h.axes,'YDir','normal','XAxisLocation','Top','YAxisLocation','Right');
    
    %--Create profile axes
    axis_size=100;
    pos = get(h.axes,'Position');
    posRt= [pos(1)+pos(3)+20, pos(2)          , axis_size   , pos(4)];
    posTop=[pos(1)          , pos(2)+pos(4)+20, pos(3), axis_size];

    %--Create marker counter
    h.markerX = double.empty;
    h.markerY = double.empty;
    h.markerCounter = 0;
    h.marker = images.roi.Point.empty;
    
    h.axesRt =axes('Units','pixels',...
                'PositionConstraint', 'InnerPosition',...
                'Position',posRt,...
                'Units','pixels',...
                'NextPlot','add',...
                'YAxisLocation','Right');
    
    h.axesTop=axes('Units','pixels',...
                'PositionConstraint', 'InnerPosition',...
                'Position',posTop,...
                'NextPlot','add',...
                'Units','pixels',...
                'XAxisLocation','Top');


%% -- Camera Label 
    info = strcat(h.Tag, '   RMS:  x=0  y=0');
    h.camLbl = uicontrol(h.figure,'Style','text',...
        'Units', 'pixels', ...
        'Position',[10,750,720,50],'String',info,'FontSize',24);


            
%% -- Camera controls and labels
    i = 0;  
    h.CamCtlPanel = uipanel(h.figure,'Title','Camera Properties',...
            'Units','pixels',...
            'Position',[(posRt(1)+posRt(3)+25), corner(2)-120, 120, 230]);
    i=i+1;  
    h.CamCtrl.shutter=uicontrol(h.CamCtlPanel,'Style','edit',...
        'Units', 'Characters',...
        'Position',[1,i*2,8,1.5],...  % [Left, Bottomm Width, Height]
        'Tag','Shutter',...
        'Callback',@Shutter_Callback);
    
     h.CamCtrl.l_shutter=uicontrol(h.CamCtlPanel,'Style','text',...
        'Units', 'Characters',...
        'Position',[10,i*2,8,1.5],...
        'Tag','Lbl_Shutter',...
        'String','Shutter');

     i=i+1;
     h.CamCtrl.trg_delay=uicontrol(h.CamCtlPanel,'Style','edit',...
        'Units', 'Characters',...
        'Position',[1,i*2,8,1.5],...
        'Tag','TriggerDelay',...
        'Enable', 'on', ...
        'Callback',@TriggerDelay_Callback, 'Value',get(h.camObj, 'Gain'));
    
     h.CamCtrl.l_trg_delay=uicontrol(h.CamCtlPanel,'Style','text',...
        'Units', 'Characters',...
        'Position',[10,i*2,8,1.5],...
        'Tag','Lbl_TirggerDelay',...
       'String','Delay');

    
    i = i+1;
    h.CamCtrl.autoGain = uicontrol(h.CamCtlPanel,'Style','togglebutton',...
                'Tag','autoGain',...
                'Callback',{@autoGain_Callback},...
                'String','autoGain',...
                'Units','Characters',...
                'Position',[1,i*2,20,2]);

    i=i+1;

    h.CamCtrl.gainsl = uicontrol(h.CamCtlPanel, Style="slider", ...
        Units="characters", ...
        Position=[1,i*2,20,1.5], ...
        Tag="GainSlider", ...
        Callback=@Gain_Callback, ...
        Value=0, ...
        Min=0,Max=24);

     i=i+1;   
     h.CamCtrl.gain=uicontrol(h.CamCtlPanel,'Style','edit',...
        'Units', 'Characters',...
        'Position',[1,i*2,8,1.5],...
         'Tag','GainEdit',...
        'Callback',@Gain_Callback,'Value',0);

     h.CamCtrl.l_gain=uicontrol(h.CamCtlPanel,'Style','text',...
        'Units', 'Characters',...
        'Position',[10,i*2,10,1.5],...
        'Tag','Lbl_Gain',...
        'String','Gain');
    i=i+1;
    h.CamCtrl.BlackLevel=uicontrol(h.CamCtlPanel,'Style','edit',...
        'Units', 'Characters',...
        'Position',[1,i*2,8,1.5],...
        'Tag','BlackLevel',...
        'Callback',@BlackLevel_Callback,'Value',get(h.camObj, 'Gain'));
    
     h.CamCtrl.l_blackLevel=uicontrol(h.CamCtlPanel,'Style','text',...
        'Units', 'Characters',...
        'Position',[10,i*2,8,1.5],...
        'Tag','Lbl_BlackLevel',...
        'String','BlckLvl');

     i=i+1;
     h.CamCtrl.Threshold=uicontrol(h.CamCtlPanel,'Style','edit',...
        'Units', 'Characters',...
        'Position',[1,i*2,8,1.5],...
        'Tag','Threshold',...
        'Enable', 'off', ...
        'Callback',@Threshold_Callback, 'Value',get(h.camObj, 'Gain'));
    
     h.CamCtrl.l_blackLevel=uicontrol(h.CamCtlPanel,'Style','text',...
        'Units', 'Characters',...
        'Position',[10,i*2,8,1.5],...
        'Tag','Lbl_Threshold',...
       'String','Thrshld');



    
    %% --Interaction Panel buttons
    B.nv = 10;
    BtnPositions=zeros(4,B.nv);
        %button sizes are normalized to their parent panel.
    for i=0:B.nv
        BtnPositions(:,i+1) = [0.05, 0.025+0.98*i/B.nv ,0.95, 0.95/B.nv ];
    end
    i=1;
    
    h.ButtonPanel = uipanel(h.figure,'Title','Interaction Panel',...
                    'Units','pixels',...
                    'Position', [(posRt(1)+posRt(3)+25), corner(2)+120, 120, posRt(4)-70]);
            
    h.frameCtr= uicontrol(h.ButtonPanel,'Style','text',...
                    'Tag','frameCounter',...
                    'Callback',{@frameCounter_Callback},...
                    'String','0',...
                    'Units','normalized',...
                    'Position',BtnPositions(:,i));
        i=i+1;

    h.AutoSave = uicontrol(h.ButtonPanel,'Style','togglebutton',...
                'Tag','AutoSave',...
                'Callback',{@AutoSave},...
                'String','AutoSave OFF',...
                'Units','normalized',...
                'Position',BtnPositions(:,i));

        i=i+1;
    h.saveImage = uicontrol(h.ButtonPanel,'Style','pushbutton',...
                    'Tag','takeImage',...
                    'Callback',{@saveImage_Callback},...
                    'String','Save Raw Image',...
                    'Units','normalized',...
                    'Position',BtnPositions(:,i));
    %    i=i+1;
    %h.profile= uicontrol(h.ButtonPanel,'Style','togglebutton',...
    %                'Tag','profileImage',...
    %                'Callback',{@profileImage_Callback,h},...
    %                'String','Profile Image',...
    %                'Units','normalized',...
    %                'Position',BtnPositions(:,i));

        i=i+1;
    h.marker= uicontrol(h.ButtonPanel,'Style','pushbutton',...
                    'Tag','SetMarker',...
                    'Callback',{@MakeMarker},...
                    'String','SetMarker',...
                    'Units','normalized',...
                    'Position',BtnPositions(:,i));

    %    i=i+1;
    % h.rect= uicontrol(h.ButtonPanel,'Style','pushbutton',...
    %                'Tag','ManualCenter',...
    %                'Callback',{@rectImage_Callback},...
    %                'String','Manual Center',...
    %                'Units','normalized',...
    %                'Position',BtnPositions(:,i));

        i=i+1;
    h.GetBgnd=uicontrol(h.ButtonPanel,'Style','pushbutton',...
                    'Tag','Take Bkgd',...
                    'Callback',{@TakeBgnd_Callback},...
                    'String','getBackground',...
                    'Units','normalized',...
                    'Position',BtnPositions(:,i));
        i=i+1;
    h.SubtBgnd=uicontrol(h.ButtonPanel,'Style','togglebutton',...
                    'Tag','SubtBgnd',...
                    'Callback',{@SubtBgnd_Callback},...
                    'String','Subtract Background',...
                    'Units','normalized',...
                    'Position',BtnPositions(:,i));
        i=i+1;  
    h.AvgImages=uicontrol(h.ButtonPanel,'Style','togglebutton',...
                    'Tag','AverageImages',...
                    'Callback',{@AvgImageToggle},...
                    'String','Average Images',...
                    'Units','normalized',...
                    'Position',BtnPositions(:,i));

        i=i+1;  
    h.Pause=uicontrol(h.ButtonPanel,'Style','togglebutton',...
                    'Tag','Pause',...
                    'Callback',{@PauseAcq},...
                    'String','Pause Acquisition',...
                    'Units','normalized',...
                    'Position',BtnPositions(:,i), ...
                    BackgroundColor='green');
        i=i+1;

    h.LEDswitch = uicontrol(h.ButtonPanel,'Style','togglebutton',...
                    'Tag','LEDswitch',...
                    'Callback',{@LEDswitch},...
                    'String','LED on/off',...
                    'Units','normalized',...
                    'Position',BtnPositions(:,i));
         i=i+1;
        
    h.RunMode = uicontrol(h.ButtonPanel,'Style','togglebutton',...
                'Tag','RunMode',...
                'Callback',{@RunMode},...
                'String','Hardware trg',...
                'Units','normalized',...
                'Position',BtnPositions(:,i), BackgroundColor='green');

  

%% Filter Wheel 
    h.IFW.group = uibuttongroup(h.figure,'Title','Filter wheel',...
            'Units','pixels',...
            'SelectionChangedFcn',{@IFW_position},...
            'Position',[pos(1)+pos(3)+20, pos(2)+pos(4)+20, axis_size, 1.3*axis_size]);

    h.IFW.p1=uicontrol(h.IFW.group,'Style','radiobutton',...
        'Units', 'Characters',...
        'Position',[0,6.5,18,1.5],...
        'String','Clear');

    h.IFW.p2=uicontrol(h.IFW.group,'Style','radiobutton',...
        'Units', 'Characters',...
        'Position',[0,5,18,1.5],...
        'String','Trans 50 %');

    h.IFW.p3=uicontrol(h.IFW.group,'Style','radiobutton',...
        'Units', 'Characters',...
        'Position',[0,3.5,18,1.5],...
        'String','Trans 10 %');
    
    h.IFW.p4=uicontrol(h.IFW.group,'Style','radiobutton',...
        'Units', 'Characters',...
        'Position',[0,2,18,1.5],...
        'String','Trans 1 %');

    h.IFW.p5=uicontrol(h.IFW.group,'Style','radiobutton',...
        'Units', 'Characters',...
        'Position',[0,0.5,18,1.5],...
        'String','540 nm BP');
    
    

    %% Profile Center controls and labels
    h.ProfCtlPanel = uipanel(h.figure,'Title','Profile Properties',...
            'Units','pixels',...
            'Position',[posRt(1)+posRt(3)+25, pos(2)+pos(4)+50, 120, 1.3*axis_size]);

    butBot=0.2;
    
    butHt=1.5;
    
% Display the Centroid
    h.ProfCtrl.X=uicontrol(h.ProfCtlPanel,'Style','edit',...
        'Units', 'Characters',...
        'Position',[0,butBot,7.5,butHt],...  % [Left, Bottom, Width, Height]
        'Tag','ProfPosX',...
        'String','0');
%         'Callback',{@UpdateProfileCenter});
        
    h.ProfCtrl.Y=uicontrol(h.ProfCtlPanel,'Style','edit',...
        'Units', 'Characters',...
        'Position',[8,butBot,7.5,butHt],...  % [Left, Bottom, Width, Height]
        'Tag','ProfPosY',...
        'String','0');
%         'Callback',{@UpdateProfileCenter});
    
     h.ProfCtrl.posLbl=uicontrol(h.ProfCtlPanel,'Style','text',...
            'Units', 'Characters',...
            'Position',[15,butBot,9,butHt],...
            'Tag','Lbl_position',...
            'String','Center');
        butBot=butBot+butHt+0.0;

% Display stdDev values
    h.ProfCtrl.Xsize=uicontrol(h.ProfCtlPanel,'Style','text',...
        'Units', 'Characters',...
        'Position',[0,butBot,7,butHt],...  % [Left, Bottom, Width, Height]
        'Tag','ProfPosX',...
        'String','-');
%         'Callback',{@UpdateProfileCenter});
        
    h.ProfCtrl.Ysize=uicontrol(h.ProfCtlPanel,'Style','text',...
        'Units', 'Characters',...
        'Position',[8,butBot,7,butHt],...  % [Left, Bottom, Width, Height]
        'Tag','ProfPosY',...
        'String','-');
%         'Callback',{@UpdateProfileCenter});
    
     h.ProfCtrl.sizeLbl=uicontrol(h.ProfCtlPanel,'Style','text',...
            'Units', 'Characters',...
            'Position',[16,butBot,7,butHt],...
            'Tag','Lbl_position',...
            'String','σ (x,y)');
        butBot=butBot+butHt+0.2;
        
%layout the profile center buttons in a panel
    h.profCtrl.group = uibuttongroup(h.ProfCtlPanel,...
        'Units', 'Characters',...
        'Position',[0,butBot,19,5],...
        'Tag','ProfGroup',...
        'SelectionChangedFcn',{@proftype});
    
    h.ProfCtrl.manual=uicontrol(h.profCtrl.group,'Style','radiobutton',...
        'Units', 'Characters',...
        'Position',[0,0,18,1.5],...
        'String','Manual');
    
    h.ProfCtrl.auto=uicontrol(h.profCtrl.group,'Style','radiobutton',...
        'Units', 'Characters',...
        'Position',[0,1.5,18,1.5],...
        'String','Auto Once');

    h.ProfCtrl.track=uicontrol(h.profCtrl.group,'Style','radiobutton',...
        'Units', 'Characters',...
        'Position',[0,3,18,1.5],...
        'String','Track');
            
    %% Set graph limits
    h.plotRt=plot(h.axesRt,1:h.vidRes(2),-h.pixelSize*(-h.vidRes(2)/2:(h.vidRes(2)/2-1)));
    set(h.axesRt,'YDir','reverse')
    xlim(h.axesRt,[0,2^bitdepth-1])
    ylim(h.axesRt,h.pixelSize*[-h.vidRes(2)/2,h.vidRes(2)/2]);
    xlim manual
    ylim manual
    
    h.plotTop=plot(h.axesTop,h.pixelSize*(-h.vidRes(1)/2:h.vidRes(1)/2-1), 1:1:h.vidRes(1));
    xlim(h.axesTop,h.pixelSize*[-h.vidRes(1)/2,h.vidRes(1)/2-1])
    ylim(h.axesTop,[0,2^bitdepth-1]);
    xlim manual
    ylim manual

    set(h.axes,'FontSizeMode','manual','FontSize',8)
        % place ROI dot to show profile center
    x0= str2double(h.ProfCtrl.X.String);
    y0= str2double(h.ProfCtrl.Y.String);
    h.roi=images.roi.Crosshair(h.axes, 'Position',[x0, y0],...
                'Deletable', 0,...
                'InteractionsAllowed','none',...
                'Color','g', LabelAlpha=0.1, LineWidth=1, Visible='on');
   
    h.Image.CDataMapping='direct';
%     set(h.figure,'CurrentAxes',h.axes)
    

    % setting a custom version of "jet" color map with black color at 0 and
    % white at 1
    cmap = jet(2^bitdepth-1);
    if custom_cmap
        cmap(1,:) = 0;
        cmap(end,:) = 1;
    end    
    colormap(h.axes, cmap);

    h.cbar = colorbar(h.axes,'Location','manual',...
                        'Units','pixels','Position',[30,100,15,pos(4)],...
                        'FontSize',8);
    

    function rectImage_Callback(~, ~)
        stop(h.vid)
        set(h.figure,'currentaxes',h.axes)
        [x,y]=ginput(1);
        start(h.vid);
        h.ProfCtrl.X.String=num2str(x);
        h.ProfCtrl.Y.String=num2str(y);
%        [x,y]=worldToSubscript(h.RA,x,y);
        h.roi.Color='g';
        if (get(h.RunMode, 'String') == 'Free run')
            trigger(h.vid);
        end        
        % [x0,y0]=ginput(1);
        % h.rpos=imrect(h.axes);
        % rectposvec=wait(h.rpos);
    end

    function saveImage_Callback(~,~)
    % Gets data from the main viewing axis and saves a full-depth and 8-bit
    % depth image. Filenames correspond to the frame acquisition time with
    % milliseconds.
        gainStr = int2str(get(h.camObj, 'Gain'));
        A=h.Image.CData;
        FrameAcqTime = getappdata(h.Image,'FrameAcqTime');
        h.FrameAcqStr = '';
        minA = min(A(:));
        A = (double(A - minA) ./ double( max(A(:)) - minA )) ;
        for k=1:6
            h.FrameAcqStr = append(h.FrameAcqStr,num2str(FrameAcqTime(k),6));
            h.FrameAcqStr = append(h.FrameAcqStr,'-');
        end
        objIFW.filterTAG = 'clear';
        fname=strcat(h.df, '\', h.FrameAcqStr, objIFW.filterTAG, '_gain_',gainStr,'.png');
        % fnamec=strcat(h.dfc, '\', h.FrameAcqStr, objIFW.filterTAG, '_gain_',gainStr,'.jpg');
        disp(fname);
        imwrite(A,fname,'png' ,'BitDepth',16);% 'CreationTi
    end
    
    %% IFW action control

    function IFW_position(~, event)
        currentposition = objIFW.getFilterID;
        switch event.NewValue.String
            case 'Clear'
                objIFW.filterID = 1;
                objIFW.filterTAG = 'Clear';
                objIFW.turnWheel();
                set(h.IFW.p1, 'Enable', 'off')
                set(h.IFW.p2, 'Enable', 'off')
                set(h.IFW.p3, 'Enable', 'off')
                set(h.IFW.p4, 'Enable', 'off')
                set(h.IFW.p5, 'Enable', 'off')
                % pause(3*(abs(currentposition - objIFW.filterID)))
            case 'Trans 50 %'
                objIFW.filterID = 2;
                objIFW.filterTAG = 'Trans 50 %';
                objIFW.turnWheel();
                set(h.IFW.p1, 'Enable', 'off')
                set(h.IFW.p2, 'Enable', 'off')
                set(h.IFW.p3, 'Enable', 'off')
                set(h.IFW.p4, 'Enable', 'off')
                set(h.IFW.p5, 'Enable', 'off')
                % pause(5*(abs(currentposition - objIFW.filterID)))
            case 'Trans 10 %'
                objIFW.filterID = 3;
                objIFW.filterTAG = 'Trans 10 %';
                objIFW.turnWheel();
                set(h.IFW.p1, 'Enable', 'off')
                set(h.IFW.p2, 'Enable', 'off')
                set(h.IFW.p3, 'Enable', 'off')
                set(h.IFW.p4, 'Enable', 'off')
                set(h.IFW.p5, 'Enable', 'off')
                % pause(5*(abs(currentposition - objIFW.filterID)))
            case 'Trans 1 %'
                objIFW.filterID = 4;
                objIFW.filterTAG = 'Trans 1 %';
                objIFW.turnWheel();
                set(h.IFW.p1, 'Enable', 'off')
                set(h.IFW.p2, 'Enable', 'off')
                set(h.IFW.p3, 'Enable', 'off')
                set(h.IFW.p4, 'Enable', 'off')
                set(h.IFW.p5, 'Enable', 'off')
                % pause(5*(abs(currentposition - objIFW.filterID)))
            case '540 nm BP'
                objIFW.filterID = 5;
                objIFW.filterTAG = '540 nm BP';
                objIFW.turnWheel();
                set(h.IFW.p1, 'Enable', 'off')
                set(h.IFW.p2, 'Enable', 'off')
                set(h.IFW.p3, 'Enable', 'off')
                set(h.IFW.p4, 'Enable', 'off')
                set(h.IFW.p5, 'Enable', 'off')
                % pause(5*(abs(currentposition - objIFW.filterID)))
        end
        set(h.IFW.p1, 'Enable', 'on')
        set(h.IFW.p2, 'Enable', 'on')
        set(h.IFW.p3, 'Enable', 'on')
        set(h.IFW.p4, 'Enable', 'on')
        set(h.IFW.p5, 'Enable', 'on')

    end

    function proftype(~, event)
        x0 = str2double(h.ProfCtrl.X.String);
        y0 = str2double(h.ProfCtrl.Y.String);    
        switch event.NewValue.String
            case 'Manual'
                stop(h.vid)
                set(h.figure,'currentaxes',h.axes)
                [x,y]=ginput(1);
                if  ~isrunning(h.vid)
                    start(h.vid);
                end 
                h.ProfCtrl.X.String=num2str(x);
                h.ProfCtrl.Y.String=num2str(y);
%                 [x,y]=worldToSubscript(h.RA,x,y);
                h.roi.Color='g';
                if (get(h.RunMode, 'String') == 'Free run')
                    trigger(h.vid);
                end 
            case 'Auto Once'
                findCtr(h);
                h.ProfCtrl.manual.Value=1;
            case 'track'
                findCtr(h);
         end
    end
    
    function MakeMarker(~,~)
        stop(h.vid)
        set(h.figure,'currentaxes',h.axes)
        [x,y]=ginput(1);
        h.markerCounter = h.markerCounter + 1;
        h.markerX(h.markerCounter) = x;
        h.markerY(h.markerCounter) = y;
%         [x,y]=worldToSubscript(h.RA,x,y);
        lbl = strcat(num2str(x),';',num2str(y));
        h.marker(h.markerCounter) = images.roi.Point( ...
            h.axes, "Position",[x,y], ...
            "Deletable",true, ...
            "Color",'w', ...
            'Label',lbl, ...
            "Visible",'on');
        if  ~isrunning(h.vid)
            start(h.vid);
        end 
        if (get(h.RunMode, 'String') == 'Free run')
            trigger(h.vid);
        end 
    end


    function TakeBgnd_Callback(~,~)
        set(h.SubtBgnd,'UserData',h.Image.CData)
    end
    
    function SubtBgnd_Callback(source,eventdata)
        
        if source.Value     % if button is depressed, then execture command
           
            if isempty(source.UserData)   %check if the user data where the background image is stored is missing
                warndlg('Please create a background image first, then try again',...
                        'Invalid','modal');
                source.Value=source.Min;   % set the toggle button to off
                return
            end
            source.String='Subtracting Bkgnd';
            set(h.CamCtrl.shutter, 'Enable', 'off');
            set(h.CamCtrl.gain, 'Enable', 'off');
            set(h.CamCtrl.BlackLevel, 'Enable', 'off');
            set(h.CamCtrl.Threshold, 'Enable', 'on');
            set(h.CamCtrl.autoGain, 'Enable', 'off');
        else
            source.String='Subtract Background';
            set(h.CamCtrl.shutter, 'Enable', 'on');
            set(h.CamCtrl.gain, 'Enable', 'on');
            set(h.CamCtrl.BlackLevel, 'Enable', 'on');
            set(h.CamCtrl.Threshold, 'Enable', 'off');
            set(h.camObj, 'Threshold', 0);
            set(h.CamCtrl.Threshold, 'String', '0');
            set(h.CamCtrl.autoGain, 'Enable', 'on');
        end
        
    end

%% ------Camera Control Callbacks
    function Shutter_Callback(source,eventdata)
        input = str2double(get(source,'String'));
        if isnan(input)
            errordlg('You must enter a numeric value','Invalid Input','modal')
            uicontrol(source)
            return
        else
%            cameraObject=get(vid, 'Source');
            set(h.camObj, 'ExposureTimeAbs',input)
        end
    end

    function Gain_Callback(source, eventdata)          
        if source.Tag == "GainSlider"
            input = get(source, 'Value');
            input = int16(input);
            set(h.CamCtrl.gain, 'String', num2str(input));
        end
        if source.Tag == "GainEdit"
            input = get(source, 'String');
            input = str2double(input);
            set(h.CamCtrl.gainsl, 'Value', int16(input)); % double(input)
        end
        if isnan(input) || input > 24
            errordlg('You must enter a numeric value from 0 to 24','Invalid Input','modal')
            uicontrol(source)
            return
        else
            set(h.camObj, 'Gain',input)
        end

    end

    function autoGain_Callback(source, eventdata)
        if source.Value     % if button is depressed, then execute command
            set(h.camObj, 'GainAuto', 'Once');
            source.String='autoGain';
        else
            set(h.camObj, 'GainAuto', 'Off');
            source.String='autoGain';
        end    
    end
    
    function BlackLevel_Callback(source, eventdata)
        input = str2double(get(source,'String'));
        if isnan(input) || input > 31 || input < 0
            errordlg('You must enter a numeric value from 0 to 31','Invalid Input','modal')
            uicontrol(source)
            return
        else
            set(h.camObj, 'BlackLevel',input)
        end        
    end

    function Threshold_Callback(source, eventdata)
        input = str2double(get(source,'String'));
        if isnan(input) || input > 1024 || input < 0
            errordlg('You must enter a numeric value from 0 to 1024','Invalid Input','modal')
            uicontrol(source);
            return
        else
            set(h.camObj, 'Threshold', input);
        end        
    end

    function AvgImageToggle(source, eventdata)
        stop(h.vid);
        if source.Value     % if button is depressed, then execture command
            set(h.vid, 'FramesPerTrigger', 5);
            source.String='Averaging';
        else
            set(h.vid, 'FramesPerTrigger', 1);
            source.String='AverageImages';            
        end
        if  ~isrunning(h.vid)
            start(h.vid);
        end 
        if triggerconfig(h.vid).TriggerType == "manual"
            trigger(h.vid);
        end
    end

    function PauseAcq(source, eventdata)
        if source.Value     % if button is depressed, then execute command
            if isrunning(h.vid)
                stop(h.vid);
                source.String='Acquisition Paused';
                source.BackgroundColor='red';
            end
        else
            if  ~isrunning(h.vid)
                start(h.vid);
            end 
            if triggerconfig(h.vid).TriggerType == "manual"
                trigger(h.vid);
            end
            source.String='Pause Acquisition';
            source.BackgroundColor='green';
        end    
    end
    
    function LEDswitch(source, eventdata)
        if source.Value     % if button is depressed, then execute command
            source.String='LED is on';
            set(h.camObj, 'SyncOutLevels', 1);
        else            
            source.String='LED is off';
            set(h.camObj, 'SyncOutLevels', 0);
        end    
    end

    function RunMode(source, eventdata)
        if source.Value
            source.String='Free run';
            stop(h.vid);            
            triggerconfig(h.vid,'manual');
            set(h.camObj, 'TriggerMode', 'Off');
            set(h.camObj, 'TriggerSource', 'Freerun');
            set(h.camObj, 'TriggerSelector', 'AcquisitionStart');
            set(h.vid, 'TriggerRepeat', Inf); 
            % set(h.camObj, 'TriggerDelayAbs', 100);
            if  ~isrunning(h.vid)
                start(h.vid);
                set(h.Pause, 'BackgroundColor', 'green');
                set(h.Pause, 'String', 'Pause Acquisition');
                set(h.Pause, 'Value', 0)
            end 
            trigger(h.vid);
            source.BackgroundColor='red';
        else
            source.String='Hardware trg'; 
            stop(h.vid);
            triggerconfig(h.vid,'hardware'); 
			set(h.camObj, 'TriggerOverlap', 'Off');	
            set(h.camObj, 'TriggerSelector', 'FrameStart');
            set(h.camObj, 'TriggerSelector', 'FrameStart'); % AcquisitionRecord FrameStart
            set(h.vid, 'FramesPerTrigger', 1); % test line. Consider to delete it
            set(h.camObj, 'TriggerMode', 'On');
            set(h.camObj, 'TriggerSource', 'Line1');
            set(h.camObj, 'TriggerActivation', 'RisingEdge');
            % set(h.camObj, 'TriggerDelayAbs', 0);	
    		set(h.vid, 'TriggerRepeat', Inf)
            source.BackgroundColor='green';
            if  ~isrunning(h.vid)
                start(h.vid);
                set(h.Pause, 'BackgroundColor', 'green');
                set(h.Pause, 'String', 'Pause Acquisition');
                set(h.Pause, 'Value', 0)
            end            
        end
    end
    
    function TriggerDelay_Callback(source, eventdata)
        input = str2double(get(source,'String'));
        if isnan(input)
            errordlg('You must enter a numeric value','Invalid Input','modal')
            uicontrol(source)
            return
        else
            set(h.camObj, 'TriggerDelayAbs', input);
        end
    end


    function AutoSave(source, eventdata)
    stop(h.vid);
        if source.Value     % if button is depressed, then execute command
            source.String='AutoSave ON';
            set(h.camObj, 'AutoSave', true);
        else            
            source.String='AutoSave OFF';            
            h.autoSave = false; 
            set(h.camObj, 'AutoSave', false);
        end
    if  ~isrunning(h.vid)
        start(h.vid);
    end
    trigger(h.vid);
    end


 end  
