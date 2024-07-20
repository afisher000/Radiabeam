function GUI_IFW_position(source, event)
    h = guidata(source);

    currentposition = h.objIFW.getFilterID;
    switch event.NewValue.String
        case 'Clear'
            h.objIFW.filterID = 1;
            h.objIFW.filterTAG = 'Clear';
            h.objIFW.turnWheel();
            set(h.IFW.p1, 'Enable', 'off')
            set(h.IFW.p2, 'Enable', 'off')
            set(h.IFW.p3, 'Enable', 'off')
            set(h.IFW.p4, 'Enable', 'off')
            set(h.IFW.p5, 'Enable', 'off')
            % pause(3*(abs(currentposition - objIFW.filterID)))
        case 'Trans 50 %'
            h.objIFW.filterID = 2;
            h.objIFW.filterTAG = 'Trans 50 %';
            h.objIFW.turnWheel();
            set(h.IFW.p1, 'Enable', 'off')
            set(h.IFW.p2, 'Enable', 'off')
            set(h.IFW.p3, 'Enable', 'off')
            set(h.IFW.p4, 'Enable', 'off')
            set(h.IFW.p5, 'Enable', 'off')
            % pause(5*(abs(currentposition - objIFW.filterID)))
        case 'Trans 10 %'
            h.objIFW.filterID = 3;
            h.objIFW.filterTAG = 'Trans 10 %';
            h.objIFW.turnWheel();
            set(h.IFW.p1, 'Enable', 'off')
            set(h.IFW.p2, 'Enable', 'off')
            set(h.IFW.p3, 'Enable', 'off')
            set(h.IFW.p4, 'Enable', 'off')
            set(h.IFW.p5, 'Enable', 'off')
            % pause(5*(abs(currentposition - objIFW.filterID)))
        case 'Trans 1 %'
            h.objIFW.filterID = 4;
            h.objIFW.filterTAG = 'Trans 1 %';
            h.objIFW.turnWheel();
            set(h.IFW.p1, 'Enable', 'off')
            set(h.IFW.p2, 'Enable', 'off')
            set(h.IFW.p3, 'Enable', 'off')
            set(h.IFW.p4, 'Enable', 'off')
            set(h.IFW.p5, 'Enable', 'off')
            % pause(5*(abs(currentposition - objIFW.filterID)))
        case '540 nm BP'
            h.objIFW.filterID = 5;
            h.objIFW.filterTAG = '540 nm BP';
            h.objIFW.turnWheel();
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
    fprintf('Filter Position: %s\n', h.objIFW.filterTAG)
    guidata(source, h);
end