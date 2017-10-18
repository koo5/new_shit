#!/usr/bin/env python
import pygtk
import gtk

i = gtk.StatusIcon()
i.set_from_stock(gtk.STOCK_INFO)
i.set_visible(True)
gtk.main()
