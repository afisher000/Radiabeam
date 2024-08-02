function GUI_BlackLevel_Callback(source, ~)
    h = guidata(source);
    
    input = str2double(get(source,'String'));
    if isnan(input) || input > 31 || input < 0
        errordlg('You must enter a numeric value from 0 to 31','Invalid Input','modal')
        uicontrol(source)
        return
    else
        set(h.camObj, 'BlackLevel',input)
    end        
end