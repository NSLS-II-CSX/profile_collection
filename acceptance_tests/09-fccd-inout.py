from bluesky.plans import rel_scan
#from bluesky.callbacks import LiveTable, LivePlot

# fccd.connected shows as False, but does not prevent running the scans below. 
# assert fccd.connected

#ct_dark is fccd tests 3 gain modes
RE(bpp.pchain(count([fccd], num=2), beam_show(), ct_dark_all(2), beam_block()))


