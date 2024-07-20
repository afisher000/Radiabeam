function GUI_proftype(source, event)
    h = guidata(source);
    
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