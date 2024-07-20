    function GUI_rectImage_Callback(source, ~)
        h = guidata(source);
        
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