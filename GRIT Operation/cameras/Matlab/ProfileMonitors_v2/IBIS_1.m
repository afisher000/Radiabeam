function IBIS_1(varargin)
    
    divisor=2.0;

%     h.camSelect = uicontrol(h.figure,'Style','popupmenu',...
%                 'Tag','selectCamera',...
%                 'Callback',{@selectCamera_Callback},...
%                 'String',{},...
%                 'Position',[1*20+0*80 20 80 25]);
    
    %----------- Open Camera   

    
    vid=videoinput('gentl',1,'mono8');
    vid.ReturnedColorSpace='grayscale';
    vidRes = get(vid, 'VideoResolution');
    nBands = get(vid, 'NumberOfBands');  
    
    triggerconfig(vid, 'Immediate');        %debug line. 'should be Hardware
    vid.TriggerRepeat = Inf;            %get an infinite number of lines
    vid.FramesPerTrigger = 1;                 % each trigger should only give one image
%     vid.FramesAcquiredFcnCount=4;
    vid.TriggerFcn = {'util_imaverage', framesPerTrigger};  %sets the callback fcn name. Will be called when a trigger is received

    
    
    %-------- create figure
    h.figure=figure(...
            'PaperPositionMode','auto',...
            'Toolbar','figure',...
            'Menubar', 'none',...
            'NumberTitle','Off',...
            'Name','IBIS Viewer',...
            'unit','pixels',...
            'Position',[20,20,1200+vidRes(1)/divisor,1200+vidRes(2)/divisor],...
            'CloseRequestFcn',{@CloseRequest_Callback}...
            );
    
    %------- create buttons
    h.takeImage = uicontrol(h.figure,'Style','pushbutton',...
                    'Tag','takeImage',...
                    'Callback',{@takeImage_Callback},...
                    'String','Take Image',...
                    'Position',[1*20+0*80 20 80 25]);
                
    h.profile= uicontrol(h.figure,'Style','pushbutton',...
                    'Tag','profileImage',...
                    'Callback',{@profileImage_Callback},...
                    'String','Profile Image',...
                    'Position',[2*20+1*80 20 80 25]);

    h.rect= uicontrol(h.figure,'Style','pushbutton',...
                    'Tag','rectImage',...
                    'Callback',{@rectImage_Callback},...
                    'String','Draw ROI',...
                    'Position',[3*20+2*80 20 80 25]);
                
    %---------- Create Axes
    corner=[50,60];
    h.axes = axes('Units','pixels',...
                'PositionConstraint', 'InnerPosition',...
                'Position',[corner(1),corner(2),vidRes(1)/divisor,vidRes(2)/divisor]);
    hImage = image( zeros(vidRes(2), vidRes(1), nBands) );
    
    
    %------ Create profile axes
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
    
            
    h.Image=preview(vid, hImage);
    
    set(h.figure,'CurrentAxes',h.axes)
    h.cbar = colorbar('west');
    colormap('jet')
    setappdata(h.Image,'UpdatePreviewWindowFcn',@NewFrameFcn);
    
    
    function rectImage_Callback(source, eventdata)
       h.rpos=imrect(h.axes);
%        rectposvec=wait(h.rpos);
    end

    function takeImage_Callback(source,eventdata)
        A=getsnapshot(vid);
        imwrite(A,[timepath('ima-') '.bmp']);
    end

    function profileImage_Callback(source,eventdata)
        stoppreview(vid)
        h.rpos=imrect(h.axes);
        rpv=wait(h.rpos);
        rpv=round(rpv);
        [prof.cx prof.cy prof.c]=improfile;
        delete(h.rpos)

        A=getimage(h.axes);

        xspan=rpv(1):rpv(1)+rpv(3);
        yspan=rpv(2):rpv(2)+rpv(4);
%         C=imadjust(A,stretchlim(A(yspan,xspan)));
%         [prof.cx prof.cy prof.c]=improfile(C,prof.cx,prof.cy);
        B=A(yspan,xspan);
        hlocfig=figure(...
            'Visible','off',...
            'PaperPositionMode','auto'...
            );
        
        subplot(10,1,1:6);
%         maxVal=max(max(B));
%         minVal=min(min(B));
        cm=gray(256);cm(end,2:3)=0;cm(end,1)=1;
                        cm(1:2,[1,3])=0;cm(1,2)=1;
                colormap(cm)
            imagesc([min(xspan) max(xspan)],[min(yspan) max(yspan)],...
                    B,[0,255]);hold on;colorbar
            line([prof.cx(1) prof.cx(end)],[prof.cy(1) prof.cy(end)]);
            axis image;
%             axis([0.5 0.5+vidRes(1) 0.5 0.5+vidRes(2)])
            grid on
            elespan=sqrt((prof.cx(end)-prof.cx(1)).^2 + (prof.cy(end)-prof.cy(1))^2);
            
            subplot(10,1,8:10);
            maxnum=elespan/length(prof.c);
%             plot((1:length(prof.c))*maxnum,prof.c/255);ylim([0,1]);
            set(gca,'YTick',[0 .2 .5 .8 1])
            grid on
%         saveas(hlocfig,timepath('FIGprof-'),'bmp')
%         imwrite(B,[timepath('prof-') '.bmp']);
%         save(timepath('profdata-'), 'prof', 'B');
        preview(vid);
        set(hlocfig,'Visible','on')
    end
    function stampedpath=timepath(header)
        timestamp=fix(clock); 
        stamp=[ num2str(timestamp(1)) '-' ...
                num2str(timestamp(2)) '-' ...
                num2str(timestamp(3)) '-' ...
                num2str(timestamp(4)) '-' ...
                num2str(timestamp(5)) '-' ...
                num2str(timestamp(6))];
        stampedpath=[header, stamp];
    end
    % --- figure close callback
    function CloseRequest_Callback(source,eventdata)
        stoppreview(vid)        
        delete(vid)
        clear vid
        delete(h.figure)
    end
    function NewFrameFcn(obj,event,himage)
        % --- Update profiles ---
%         [x0, y0]=floor(fliplr(event.Resolution)); %stand in for the profile location
%         data=event.Data;
%         [nx, ny]=size(data);
%         % profile along X
%         [prof.x.d, ~, prof.x.p] = improfile(data,[1,nx],[y0,y0]);
%         plot(h.AxesTop,[0 nx], prof.x.d,prof.x.p)
%         % profile along Y
%         [prof.y.d, ~, prof.y.p] = improfile(data,[x0, x0],[1,ny]);
%         plot(h.AxesRt,prof.y.p,prof.y.d,[0, ny])
%         
%         drawnow
        himage.CData = event.Data;
    end
        


end