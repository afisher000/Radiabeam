function FramesAcquiredFcn_Callback(~,~,h)

try
    if  ~isrunning(h.vid)
        start(h.vid);
    end 

    %% update Frame counter
    prevCtr=h.frameCtr.String;
    set(h.frameCtr,'String', num2str(str2double(prevCtr)+1));
    bitdepth = get(h.camObj, 'BitDepth');
    
    [rawimage, ~, StackAcqTime]=getdata(h.vid);
    % rawimage = rot90(rawimage);
    if h.flip_h
        rawimage=fliplr(rawimage);
    end
    if h.flip_v
        rawimage=flipud(rawimage);
    end
    
    stacklength=size(rawimage,4);   % Get number of frames in image stack
    FrameAcqTime=StackAcqTime(end).AbsTime; % this is the timestamp of the last
                                            % frame
    %% Frame averaging
    
    threshold_value = get(h.camObj, 'Threshold');
    if h.AvgImages.Value && stacklength>1
        imageSum = rawimage(:, :, :, 1);
        for f = 2:stacklength
            imageSum = imadd(imageSum, rawimage(:, :, :, f));
        end
        image = imdivide(imageSum, stacklength);

    else
        image = rawimage;

    end

    %% Background subtracting
    if h.SubtBgnd.Value && not(isempty(h.SubtBgnd.UserData))
        % if the "subtract background button" is pushed and there is
        % background data, then subtract the background
        image=imsubtract(image,h.SubtBgnd.UserData);
    end
    

    %% Threshold
    if h.AvgImages.Value && stacklength>1
        image(image < threshold_value) = 0;
        image(rawimage(1) > 2^bitdepth-2) = 2^bitdepth-1;
    else
        image(image < threshold_value) = 0;
        image(rawimage > 2^bitdepth-2) = 2^bitdepth-1;
    end



    %% Update image display and metadata
    h.Image.CData = image;      %update the plot here.
    setappdata(h.Image,'FrameAcqTime',FrameAcqTime)
    % drawnow

%% Update profiles
    % --- get profile positions
    [nv, nh]=size(image);

    if h.ProfCtrl.track.Value   % if "Track" is selected for the profile
                                % properties, then update the centers
        findCtr(h);     % this will update the displayed centers
    end
    
    x0=str2double(h.ProfCtrl.X.String);  %read in the displayed centers from the GUI panel
    y0=str2double(h.ProfCtrl.Y.String);  


% --- Update profiles ---        

%profile along X
%     [~,Y]=worldToSubscript(h.RA,[0,0],[y0,y0]);
    [prof.x.d, ~, prof.x.p] = improfile(h.RA.XWorldLimits,h.RA.YWorldLimits,...
                                image,h.RA.XWorldLimits,[-y0,-y0],nh);
    h.plotTop.YData=prof.x.p;
    h.ProfCtrl.Xsize.String= num2str(std(prof.x.p*h.pixelSize),'%.2f');        % this is the beam "size" reported to the gui screen
    
% profile along Y
%     [X,~]=worldToIntrinsic(h.RA,[x0,x0],[0,0]);
    [~, prof.y.d, prof.y.p] = improfile(h.RA.XWorldLimits,h.RA.YWorldLimits,...
                                image,[x0,x0],h.RA.YWorldLimits,nv);
    h.plotRt.XData=flipud(prof.y.p);
    h.ProfCtrl.Ysize.String= num2str(std(prof.y.p*h.pixelSize),'%.2f');

    h.camLbl.String = strcat(h.Tag, '  RMS:  x=', ...
        num2str(std(prof.x.p*h.pixelSize*1000),'%4.0f'), ...
        '  y=',...
        num2str(std(prof.y.p*h.pixelSize*1000),'%4.0f'), ...
        '  [micron]');
    
    h.roi.Position=[x0, y0];    % draw crosshair
    %! this could probably be move elsewhere since we don't need to update
    %the crosshair position each time if there was no change, such as in
    %manual mode
    % drawnow

        % (this comment block is kept for records
        % the following portion of code was added to keep matlab from
        % collecting data faster than it can process it. Currently,
        % triggers are manual. it seems that we get stuck in the Logging
        % (isLogging=true) even though there are no frames to acquire.
        % This *always* happened with immediate triggers and was fixed
        % by manually triggering at the end of the Acquisition callback 
        % (ran overnight! at 30 Hz, but it now is happenneing after one
        % second of data collection.
        % https://www.mathworks.com/help/imaq/waiting-for-an-acquisition-to-finish.html
        % A hardware trigger will likely lead to the same kind of stack
        % up, so using a wait() command may be beneficial. however,
        % then we lose access to the command line.

% autosave
if get(h.camObj, 'AutoSave')
	 % Gets data from the main viewing axis and saves a full-depth and 8-bit
    % depth image. Filenames correspond to the frame acquisition time with
    % milliseconds.
        date = datetime('today');
        date.Format = 'yyyy-MM-dd';
        day = datestr(date);
        df = strcat('C:\Users\Marcos\Desktop\GRIT PM images\', h.Tag, '\', day);
        if ~exist(df, 'dir')
           mkdir(df);
        end
        A=h.Image.CData;
        FrameAcqTime = getappdata(h.Image,'FrameAcqTime');
        FrameAcqStr = '';
        minA = min(A(:));
        A = double(A - minA) ./ double( max(A(:)) - minA );
        for k=1:6
            FrameAcqStr = append(FrameAcqStr,num2str(FrameAcqTime(k),6));
            FrameAcqStr = append(FrameAcqStr,'-');
        end
        fname=strcat(df, '\', FrameAcqStr, 'hardware_trig', '.png');
        disp(fname);
        imwrite(A,fname,'png');%,'SignificantBits',bitdepth);
end
    
conf = triggerconfig(h.vid);
    if conf.TriggerType == "manual"
        trigger(h.vid);
    end
catch ME
    warning('The error "%s" occured during frame processing', ME.message);
    stop(h.vid);
    start(h.vid);
    conf = triggerconfig(h.vid);
    if conf.TriggerType == "manual"
        trigger(h.vid);
    end
end



   

end