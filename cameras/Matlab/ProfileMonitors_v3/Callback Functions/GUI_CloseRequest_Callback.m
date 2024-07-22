function GUI_CloseRequest_Callback(source, ~)
    h = guidata(source);
%         stoppreview(vid)     

    % Unlock button on menu
    h.source.Enable  = 'on';
    h.source.Value   = h.source.Min;

    % Close vid and figure
    stop(h.vid)
    delete(h.vid)
    clear h.vid
    delete(h.figure)
end