function GUI_MakeMarker(source, ~)
    h = guidata(source);
    
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