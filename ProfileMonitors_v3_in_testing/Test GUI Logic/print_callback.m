function print_callback(src,event)
h = guidata(src);
disp(h.numberOfClicks);
end