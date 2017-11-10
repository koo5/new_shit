# -*- coding: utf-8 -*-



import logging
logger=logging.getLogger("root")



langs = {'cs': {
		" values:":" hodnoty:",
		"builtins":"zabudováno",
		"clipboard":"schránka",
		"intro":"úvod",
		"some program":"nějaký program",
		"library":"knihovna",
		"welcome":"vítejte",
		"Press F1 to cycle the sidebar!": "stisknete F1 pro prepnuti bocniho menu"
		}
}

def tr(x):
	print("tr(",x)
	if lang in langs:
		if x in langs[lang]:
			x = langs[lang][x]
		else:
			logger.debug('missing translation for: %s'%x)
	if type(x) == tuple:
		x = x[0]
	print("result:",x)
	return x
