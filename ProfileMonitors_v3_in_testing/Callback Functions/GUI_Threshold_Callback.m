function GUI_Threshold_Callback(source, ~)
    h = guidata(source);
    
    input = str2double(get(source,'String'));
    if isnan(input) || input > 1024 || input < 0
        errordlg('You must enter a numeric value from 0 to 1024','Invalid Input','modal')
        uicontrol(source);
        return
    else
        set(h.camObj, 'Threshold', input);
    end        
end