function My_Callback(src,event)
data = guidata(src);
data.numberOfClicks = data.numberOfClicks + 1;
guidata(src,data)
data
end