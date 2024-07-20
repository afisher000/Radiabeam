function findCtr(h)
% this function calls autoCentroid function to determine the center of a blob

    [x,y,CtrType] = autoCentroid(h,h.Image.CData,0.01); % x and y are in intrinsic coordinates

    [x,y]=intrinsicToWorld(h.RA,x,y);

     y=-y;
    
    if CtrType == "automatic"
        h.ProfCtrl.X.String=num2str(x,'%+.3f');
        h.ProfCtrl.Y.String=num2str(y,'%+.3f');
        h.roi.Color='green';
    elseif CtrType == "None"
        h.roi.Color='red';
    elseif CtrType == "multiple"
%             disp(strcat('Auto Profile Not found:',CtrType))
        h.ProfCtrl.X.String=num2str(x,'%+.3f');
        h.ProfCtrl.Y.String=num2str(y,'%+.3f');
        h.roi.Color='yellow';
    end
    

end