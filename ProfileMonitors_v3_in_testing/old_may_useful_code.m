    function stampedpath=timepath(timestamp,header)
        stampstr=datestr(timestamp,'yyyymmddTHHMMSS_FFF');
        stampedpath=string([header, stampstr]);
    end


    function StartFcn(obj, event)
        disp('startFcn called')
%         trigger(h.vid)
    end