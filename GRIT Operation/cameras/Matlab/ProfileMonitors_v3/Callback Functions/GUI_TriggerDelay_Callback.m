function GUI_TriggerDelay_Callback(source, ~)
    h = guidata(source);
    
    input = str2double(get(source,'String'));
    if isnan(input)
        errordlg('You must enter a numeric value','Invalid Input','modal')
        uicontrol(source)
        return
    else
        set(h.camObj, 'TriggerDelayAbs', input);
    end
end