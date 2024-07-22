function vid=IBIS_2(varargin)
% This function will build a GUI to read from a single camera connected to the
% network. The major change in this revision is to switch over from the
% "preview-based" data acquisition since that is not appropriate for our
% methods

    divisor=2.0;

   
    %% ----------- Open Camera   

    
%     vid=videoinput('winvideo',1,'RGB24_1280x960');

    vid = MakoTester_20210319_Mono10_10Hz;
    camObj=get(vid,'Source');
    vid.ReturnedColorSpace='grayscale';
    vidRes = get(vid, 'VideoResolution');
    nBands = get(vid, 'NumberOfBands');  
    
% triggerconfig(vid, 'manual');        % debug line. should be Hardware
%     vid.TriggerRepeat = 1000;            %   keep repeating trigger infinitely
                                    %^ move to initialization .m file
    vid.FramesPerTrigger = 1;       % each trigger should only give one image
                                    % this can later be wired to the number
                                    % of frames to average
    vid.FramesAcquiredFcnCount = vid.FramesPerTrigger;
    vid.LoggingMode = 'memory';
  
    
    %% -------- create gui elements
    h.figure=figure(...
            'PaperPositionMode','auto',...
            'Toolbar','figure',...
            'Menubar', 'none',...
            'NumberTitle','Off',...
            'Name','IBIS Viewer',...
            'unit','pixels',...
            'Position',[20,20,200+vidRes(1)/divisor,200+vidRes(2)/divisor],...
            'CloseRequestFcn',{@CloseRequest_Callback}...
            );
    
    %% --buttons
    B.width  = 50;
    B.hpitch = 5+B.width;
    
    B.height = 15;
    B.vpitch = 5+B.height;
    
    uipanel(
    
    h.takeImage = uicontrol(h.figure,'Style','pushbutton',...
                    'Tag','takeImage',...
                    'Callback',{@takeImage_Callback},...
                    'String','Take Image',...
                    'Position',[1*20+0*80 20 80 25]);
                
    h.profile= uicontrol(h.figure,'Style','togglebutton',...
                    'Tag','profileImage',...
                    'Callback',{@profileImage_Callback},...
                    'String','Profile Image',...
                    'Position',[2*20+1*80 20 80 25]);

    h.rect= uicontrol(h.figure,'Style','pushbutton',...
                    'Tag','rectImage',...
                    'Callback',{@rectImage_Callback},...
                    'String','Manual Center',...
                    'Position',[3*20+2*80 20 80 25]);
    h.frameCtr= uicontrol(h.figure,'Style','text',...
                    'Tag','frameCounter',...
                    'Callback',{@frameCounter_Callback},...
                    'String','0',...
                    'Position',[4*20+4*80 20 80 25]);
                    
    %% --Image Axes
    corner=[50,60];
    h.axes = axes('Units','pixels',...
                'Tag', 'MainImageView',...
                'PositionConstraint', 'InnerPosition',...
                'Position',[corner(1),corner(2),vidRes(1)/divisor,vidRes(2)/divisor]);
    bitdepth=10;
    h.Image = imshow( 2^bitdepth*ones(vidRes(2), vidRes(1), nBands) );
    
    
    %--Create profile axes
    pos = get(h.axes,'Position');
    posRt= [pos(1)+pos(3)+20, pos(2), 100, pos(4)];
    posTop=[pos(1), pos(2)+pos(4)+20, pos(3), 100];
    
    h.axesRt =axes('Units','pixels',...
                'PositionConstraint', 'InnerPosition',...
                'Position',posRt,...
                'Units','pixels');
    
    h.axesTop=axes('Units','pixels',...
                'PositionConstraint', 'InnerPosition',...
                'Position',posTop,...
                'Units','pixels');
            
    %% -- Camera controls
    h.CamCtlPanel = uipanel(h.figure,'Title','Camera Properties',...
            'Units','pixels',...
            'Position',[pos(1)+pos(3)+20, pos(2)+pos(4)+20, 100, 100]);
        
    get(camObj,'ExposureTimeAbs')
    
    h.CamCtrl.shutter=uicontrol(h.CamCtlPanel,'Style','edit',...
        'Units', 'Characters',...
        'Position',[0,0,8,1.5],...  % [Left, Bottomm Width, Height]
        'Tag','Shutter',...
        'String',num2str(get(camObj,'ExposureTimeAbs')),...
        'Callback',@Shutter_Callback);
     h.CamCtrl.l_shutter=uicontrol(h.CamCtlPanel,'Style','text',...
        'Units', 'Characters',...
        'Position',[10,0,8,1.5],...
        'Tag','Lbl_Shutter',...
        'String','Shutter');
    
    h.CamCtrl.gain=uicontrol(h.CamCtlPanel,'Style','edit',...
        'Units', 'Characters',...
        'Position',[0,2,8,1.5],...
        'Tag','Gain',...
        'String',num2str(get(camObj,'Gain')),...
        'Callback',@Gain_Callback);
     h.CamCtrl.l_gain=uicontrol(h.CamCtlPanel,'Style','text',...
        'Units', 'Characters',...
        'Position',[10,2,8,1.5],...
        'Tag','Lbl_Gain',...
        'String','Gain');
        
    %% Set graph limits
    h.plotRt=plot(h.axesRt,1:1:vidRes(2), 1:1:vidRes(2));
    set(h.axesRt,'YDir','reverse')
    xlim(h.axesRt,[0,2^bitdepth-1])
    ylim(h.axesRt,[0,vidRes(2)]);
    xlim manual
    ylim manual
    
    h.plotTop=plot(h.axesTop,1:1:vidRes(1), 1:1:vidRes(1));
    xlim(h.axesTop,[0,vidRes(1)])
    ylim(h.axesTop,[0,2^bitdepth-1]);
    xlim manual
    ylim manual
   
    h.Image.CDataMapping='direct';
%     set(h.figure,'CurrentAxes',h.axes)
    h.cbar = colorbar(h.axes,'west');
    colormap(h.axes,jet(2^bitdepth-1))

    
    %% -- End of GUI element creation


    
    %% -- Specify acquisition callbacks
    vid.TriggerFcn = @TriggerFcn_Callback;     %called this way since it is local
                            % this is called whenever the camera is
                            % triggered
    vid.FramesAcquiredFcn = {@FramesAcquiredFcn_Callback,h};
                            % this will be called when all the frames are
                            % acquired. This is the best callback to use
                            % for then processing data
    
    % -- main runtime execution here
        start(vid);     % start camera operation and gain exclusive use to
                        % to allow (but not start) for acquiring image data
                        % this also calls the video objects StartFcn
                        % callback
%      disp('lets go!');
     trigger(vid)
    % -- end of main runtime execution

    %% ---Helper Functions
    function stampedpath=timepath(timestamp,header)
        stampstr=datestr(timestamp,'yyyymmddTHHMMSS_FFF');
        stampedpath=string([header, stampstr]);
    end
    %% ---- ALL the GUI callbacks
    function CloseRequest_Callback(~,~)
%         stoppreview(vid)        
        stop(vid)
        delete(vid)
        clear vid
        delete(h.figure)
    end

    function rectImage_Callback(source, eventdata)
       h.rpos=imrect(h.axes);
%        rectposvec=wait(h.rpos);
    end

    function takeImage_Callback(source,eventdata)
    % Gets data from the main viewing axis and saves a full-depth and 8-bit
    % depth image. Filenames correspond to the frame acquisition time with
    % milliseconds.
        dname='';
        A=h.Image.CData;
        FrameAcqTime=getappdata(h.Image,'FrameAcqTime');
        FrameAcqStr=timepath(FrameAcqTime,'');
        imwrite(A,strcat(dname, FrameAcqStr, '.png'),'png',...
            'SignificantBits',bitdepth);
%             'CreationTime',FrameAcqStr,...
        % png allows for grayscale images of 8 or 16 bit depth. Matlab will
        % automatically choose 8 bit for uint8 data (mono 8) or 16 bit for
        % uint16 (mono10, mono12, etc.). this should be pretty robust.        
        
        A(end,end)=2^bitdepth-1;    % make the corner pixel maximum
                                    % brightness for the given bit=depth to
                                    % ensure proper scaling
        A(end,end-1)=0;         % make the adjacent pixel minimum
                                %brightness to ensure proper scaling
        A=rescale(A,0,255,'InputMin',0,'InputMax',2^bitdepth-1);
        imwrite(A,strcat(dname, FrameAcqStr, '-8bit','.bmp'),'bmp');
            % save an 8-bit BMP. use a built-in function to make
            % the transfer.

    end

    function profileImage_Callback(source,eventdata)
%         stoppreview(vid)
        h.rpos=imrect(h.axes);
        rpv=wait(h.rpos);
        rpv=round(rpv);
        [prof.cx prof.cy prof.c]=improfile;
        delete(h.rpos)
        
            xspan=rpv(1):rpv(1)+rpv(3);
            yspan=rpv(2):rpv(2)+rpv(4);
%         C=imadjust(A,stretchlim(A(yspan,xspan)));
%         [prof.cx prof.cy prof.c]=improfile(C,prof.cx,prof.cy);

        hlocfig=figure('PaperPositionMode','auto');

%         while h.profile.Value==1
            
            A=getimage(h.axes);
            B=A(yspan,xspan);
            subplot(10,1,1:6);
%         maxVal=max(max(B));
%         minVal=min(min(B));
%             cm=gray(256);cm(end,2:3)=0;cm(end,1)=1;
%                         cm(1:2,[1,3])=0;cm(1,2)=1;
%             colormap(cm)
        colormap('jet')
            imagesc([min(xspan) max(xspan)],[min(yspan) max(yspan)],...
                    B,[0,255]);hold on;colorbar
            line([prof.cx(1) prof.cx(end)],[prof.cy(1) prof.cy(end)]);
            axis image;
%             axis([0.5 0.5+vidRes(1) 0.5 0.5+vidRes(2)])
            grid on
            elespan=sqrt((prof.cx(end)-prof.cx(1)).^2 + (prof.cy(end)-prof.cy(1))^2);
            
            subplot(10,1,8:10);
            maxnum=elespan/length(prof.c);
            plot((1:length(prof.c))*maxnum,prof.c/255);ylim([0,1]);
            set(gca,'YTick',[0 .2 .5 .8 1])
            grid on
        
%         set(hlocfig,'Visible','on')
    end


%% ------Image Acquisition callbacks
    function TriggerFcn_Callback(obj,event)
%         disp('triggered')
%         pause(1)
%         vid.Logging

    end

    function FramesAcquiredFcn_Callback(obj,event,h)
        
        
        %update Frame counter
        prevCtr=h.frameCtr.String;
        num2str(str2double(prevCtr)+1);
        set(h.frameCtr,'String',num2str(str2double(prevCtr)+1));
        
%         disp('Frame Acquired')
        
        [rawimage, ~, StackAcqTime]=getdata(vid);
        stacklength=size(rawimage,4);   % Get number of frames in image stack
        FrameAcqTime=StackAcqTime(end).AbsTime; % this is the timestamp of the last
                                                % frame

        if stacklength>1
            for f = 1:stacklength
                imageSum = imadd(average, rawimage(:, :, :, f));
            end
            image = imdivide(imageSum, stacklength);
        else
            image = rawimage;
        end
        h.Image.CData = image;
        setappdata(h.Image,'FrameAcqTime',FrameAcqTime)
%         drawnow

    % Initial calls to set-up limits
    % Initiate. This block should only be run the first frame of a given ROI!
    % It should be moved to another function, perhaps a FramesAcquiredFcn
    % callback such as "FramesAcquiredFcn_Initiation_CB". We could then set
    % vid.FramesAcquiredFcn=@{FramesAcquiredFcn_Callback(obj,event,h)
    % after so that this subfunction runs without the initiation work.
        [nv, nh]=size(image);


%Get profile cross hair center
        x0=floor(nh/2); %stand in for profile selection function
        y0=floor(nv/2);

% --- Update profiles ---        
    %profile along X
        [prof.x.d, ~, prof.x.p] = improfile(image,[1,nh],[y0,y0]);
%         plot(h.axesTop,prof.x.d,prof.x.p)
%         h.plotTop.XData=prof.x.d;
        h.plotTop.YData=prof.x.p;
        
    % profile along Y
        [~, prof.y.d, prof.y.p] = improfile(image,[x0, x0],[1,nv]);
%         prof.y.p=flipud(prof.y.p);
        h.plotRt.XData=prof.y.p;
%         plot(h.axesRt,prof.y.p, prof.y.d) % this is a "sideways" graph, so
                                            % we are putting the profile
                                            % data on the "X-axis"
            % (this comment block is kept for records
            % the following portion of code was added to keep matlab from
            % collecting data faster than it can process it. Currently,
            % triggers are manual. it seems that we get stuck in the Logging
            % (isLoggin=true) even though there are no frames to acquire.
            % This *always* happened with immediate triggers and was fixed
            % by mnually triggering at the end of the Acquisition callback 
            % (ran overnight! at 30 Hz, but it now is happenneing after one
            % second of data collection.
            % https://www.mathworks.com/help/imaq/waiting-for-an-acquisition-to-finish.html
            % A hardware trigger will likely lead to the same kind of stack
            % up, so usign a wait() command may be beneficial. however,
            % then we lose access to the command line. What we want is to 
                        
%     islogging(vid)
    trigger(vid)
    end

%% ------Camera Control Callbacks
    function Shutter_Callback(source,eventdata)
        input = str2double(get(source,'String'));
        if isnan(input)
            errordlg('You must enter a numeric value','Invalid Input','modal')
            uicontrol(source)
            return
        else
%             cameraObject=get(vid, 'Source');
            set(camObj, 'ExposureTimeAbs',input)
        end
    end

    function Gain_Callback(source, eventdata)
        input = str2double(get(source,'String'));
        if isnan(input)
            errordlg('You must enter a numeric value from 0 to 24','Invalid Input','modal')
            uicontrol(source)
            return
        else
%             cameraObject=get(vid, 'Source');
            set(camObj, 'Gain',input)
        end        
    end
%     function StartFcn(obj, event)
%         disp('startFcn called')
%         trigger(vid)
%     end

%% ------ ND Filter Wheel Callbacks

end