function GUI_Shutter_Callback(source, ~)
    h = guidata(source);
    
    input = str2double(get(source,'String'));
    if isnan(input)
        errordlg('You must enter a numeric value','Invalid Input','modal')
        uicontrol(source)
        return
    else
%            cameraObject=get(vid, 'Source');
        set(h.camObj, 'ExposureTimeAbs',input)
    end
end