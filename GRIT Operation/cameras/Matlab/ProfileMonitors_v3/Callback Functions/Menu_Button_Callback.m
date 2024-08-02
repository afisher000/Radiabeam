function Menu_Button_Callback(source, ~, camera)
    fprintf('---------- %s ----------\n', camera.Tag);
    
    % Lock menu button
    source.Enable='off';

    try
        open_camera(camera, source);
    catch exception
        fprintf('Error message: %s\n', exception.message)
        source.Enable = 'on';
    end

end