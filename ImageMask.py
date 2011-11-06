def buildPixmap(pixmapMaskList):
	basepm, basemask = pixmapMaskList[0]
	# don't bother compositing if just one pixmap.
	if len(pixmapMaskList) == 1:
		return basepm, basemask

	win = gtk.GtkWindow()
	newpm = gtk.create_pixmap(win, basepm.width, basepm.height, basepm.depth)
	tempgc = basepm.new_gc(clip_mask=basemask, clip_x_origin=0, clip_y_origin=0)
	gtk.draw_pixmap(newpm, tempgc, basepm, 0, 0, 0, 0, basepm.width, basepm.height)
	gc = newpm.new_gc()

	i = 1
	while i < len(pixmapMaskList):
		pm, mask = pixmapMaskList[i]
		# create a new gc using this pixmaps mask, for now assume the origin
		# of all the pixmaps is the same
		tempgc = newpm.new_gc(clip_mask=mask, clip_x_origin=0, clip_y_origin=0)
		# and draw into the base pixmap.
		gtk.draw_pixmap(newpm, tempgc, pm, 0, 0, 0, 0, pm.width, pm.height)
		# also update the base mask with the bits from this mask
		tempgc = basemask.new_gc(clip_mask=mask, clip_x_origin=0, clip_y_origin=0)
		gtk.draw_pixmap(basemask, tempgc, mask, 0, 0, 0, 0, pm.width, pm.height)
		i = i + 1

	return newpm, basemask


