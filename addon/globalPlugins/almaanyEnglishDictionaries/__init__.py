# -*- coding: utf-8 -*-
# Copyright (C) 2022 Ibrahim Hamadeh, released under GPLv2.0
# See the file COPYING for more details.
# This addon is aimed to get meaning of words using almaany.com English dictionaries.
# This addon does not have a default gesture, you have to assign one to it from input gestures dialog.

import gui, wx
import api
import textInfos
import config
import globalVars
import globalPluginHandler
from gui import guiHelper
from scriptHandler import script
from .myDialog import MyDialog
from .myDialog import getListOfDictionaryNames, getUrlOfDictionary
from logHandler import log

import addonHandler
addonHandler.initTranslation()

#the function that specifies if a certain text is selected or not
#and if it is, returns text selected
def isSelectedText():
	obj=api.getFocusObject()
	treeInterceptor=obj.treeInterceptor
	if hasattr(treeInterceptor,'TextInfo') and not treeInterceptor.passThrough:
		obj=treeInterceptor
	try:
		info=obj.makeTextInfo(textInfos.POSITION_SELECTION)
	#except (RuntimeError, NotImplementedError):
	except:
		info=None
	if not info or info.isCollapsed:
		return False
	else:
		return info.text

#default configuration 
configspec={
	"defaultDictionary": "integer(default=0)",
	"windowType": "integer(default=0)",
	"closeDialogAfterRequiringTranslation": "boolean(default= False)"
}
config.conf.spec["almaanyEnglishDictionaries"]= configspec

# Ensure one instance of Almaany english Dictionaries dialog is running.
DIALOG_INSTANCE= None

# Disable the addon on secure screen.
def disableInSecureMode(decoratedCls):
	if globalVars.appArgs.secure:
		return globalPluginHandler.GlobalPlugin
	return decoratedCls

@disableInSecureMode
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: Category in input gestures dialog.
	scriptCategory= _("Almaany English Dictionaries")

	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)

		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(AlmaanyEnglishDictionariesSettings)

	def terminate(self):
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(AlmaanyEnglishDictionariesSettings)

	def showAlmaanyDictionariesDialog(self):
		global DIALOG_INSTANCE
		if not DIALOG_INSTANCE:
			d= MyDialog(gui.mainFrame)
#			log.info('after creating object')
			d.postInit()
			d.Raise()
			d.Show()
			DIALOG_INSTANCE= d
		else:
			DIALOG_INSTANCE.Raise()

	@script(
		# Translators: Message displayed in input help mode.
		description= _("Open Almaany english dictionaries dialog, and if word is selected access meaning directly using default dictionary.")
	)
	def script_almaanyEnglishDictionaries(self, gesture):
		text= isSelectedText()
		if text and not text.isspace():
			text= text.strip()
			# We need to get the url of default dictionary.
			url= getUrlOfDictionary(default= True)
			MyDialog.getMeaning(text, url)
			return
		# Open Almaany Dictionaries dialog
		self.showAlmaanyDictionariesDialog()

#make  SettingsPanel  class
class AlmaanyEnglishDictionariesSettings(gui.SettingsPanel):
	# Translators: title of the dialog
	title= _("Almaany English Dictionaries")

	def makeSettings(self, sizer):
		settingsSizerHelper = guiHelper.BoxSizerHelper(self, sizer=sizer)

		self.availableDictionariesComboBox= settingsSizerHelper.addLabeledControl(
		# Translators: label of cumbo box to choose default dictionary.
		_("Choose default dictionary:"), 
		wx.Choice, choices= getListOfDictionaryNames()
		)
		self.availableDictionariesComboBox.SetSelection(config.conf["almaanyEnglishDictionaries"]["defaultDictionary"])

		windowTypes= [
			# Translators: Type of windows to display translation result.
			_("Default full browser"), 
			# Translators: Type of windows to display translation result.
			_("Browser window only"), 
			# Translators: Type of windows to display translation result.
			_("NVDA browseable message box(choose it after testing)")
		]
		self.resultWindowComboBox= settingsSizerHelper.addLabeledControl(
		# Translators: label of cumbo box to choose type of window to display result.
		_("Choose type of window To Display Result:"), 
		wx.Choice, choices= windowTypes)
		self.resultWindowComboBox.SetSelection(config.conf["almaanyEnglishDictionaries"]["windowType"])

		# Translators: label of the check box 
		self.closeDialogCheckBox=wx.CheckBox(self,label=_("Close Almaany Dictionaries Dialog after requesting translation"))
		self.closeDialogCheckBox.SetValue(config.conf["almaanyEnglishDictionaries"]["closeDialogAfterRequiringTranslation"])
		settingsSizerHelper.addItem(self.closeDialogCheckBox)

	def onSave(self):
		config.conf["almaanyEnglishDictionaries"]["defaultDictionary"]= self.availableDictionariesComboBox.GetSelection()
		config.conf["almaanyEnglishDictionaries"]["windowType"]= self.resultWindowComboBox.GetSelection()
		config.conf["almaanyEnglishDictionaries"]["closeDialogAfterRequiringTranslation"]= self.closeDialogCheckBox.IsChecked() 
