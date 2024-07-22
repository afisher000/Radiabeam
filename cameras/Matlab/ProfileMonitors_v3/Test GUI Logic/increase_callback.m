function increase_callback(src, event)
h = guidata(src);
h.numberOfClicks = h.numberOfClicks + 1;
guidata(src, h);
h.numberOfClicks
end