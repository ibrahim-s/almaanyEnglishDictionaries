# -*- coding: utf-8 -*-
# Copyright (C) Ibrahim Hamadeh, released under GPLv2.0
# See the file COPYING for more details.
#This module is responsible for displaying Almaany English Dictionaries dialog

import wx
import queueHandler
import config
import sys
import webbrowser
from .fetchtext import MyThread
from .getbrowsers import getBrowsers
from tones import beep
import time
import subprocess
import threading
import tempfile
import ui
import os

import addonHandler
addonHandler.initTranslation()

#browsers as dictionary with label as key, and executable path as value.
browsers= getBrowsers()

def appIsRunning(app):
	'''Checks if specific app is running or not.'''
	processes= subprocess.check_output('tasklist', shell=True).decode('mbcs')
	return app in processes

def openBrowserWindow(label, meaning, directive, default= False):
	# Translators: Title of result html page.
	title= _("Translation Result")
	html= """
	<!DOCTYPE html>
	<html><head>
	<meta charset=utf-8>
	<title>{title}</title>
	<meta name=viewport content='initial-scale=1.0'>
	</head><body>
	""".format(title= title) + meaning 
	temp= tempfile.NamedTemporaryFile(delete=False)
	path = temp.name + ".html"
	f = open(path, "w", encoding="utf-8")
	f.write(html)
	f.close()
	if default:
		webbrowser.open(path)
	else:
		subprocess.Popen(browsers[label] + directive + path)
	t=threading.Timer(30.0, os.remove, [f.name])
	t.start()

#dictionaries name and url
dictionaries_nameAndUrl= [
	("English ⇔ English", "https://www.almaany.com/en/dict/en-en/"),
	("English ⇔ French", "https://www.almaany.com/en/dict/en-fr/"),
	("English ⇔ Spanish", "https://www.almaany.com/es/dict/en-es/"),
	("English ⇔ Chinese", "https://www.almaany.com/en/dict/en-zh/"),
	("English ⇔ Russian", "https://www.almaany.com/ru/dict/en-ru/"),
	("English ⇔ Portuguese", "https://www.almaany.com/en/dict/en-pt/"),
	("English ⇔ Italian", "https://www.almaany.com/en/dict/en-it/"),
	("English ⇔ Bulgarian", "https://www.almaany.com/en/dict/en-bg/"),
	("English ⇔ Croatian", "https://www.almaany.com/en/dict/en-hr/"),
	("English ⇔ Dutch", "https://www.almaany.com/en/dict/en-nl/"),
	("English ⇔ German", "https://www.almaany.com/en/dict/en-de/"),
	("English ⇔ Greek", "https://www.almaany.com/en/dict/en-el/"),
	("English ⇔ Hebrew", "https://www.almaany.com/en/dict/en-he/"),
	("English ⇔ Hindi", "https://www.almaany.com/en/dict/en-hi/"),
	("English ⇔ Hungarian", "https://www.almaany.com/en/dict/en-hu/"),
	("English ⇔ Japanese", "https://www.almaany.com/en/dict/en-jp/"),
	("English ⇔ Korean","https://www.almaany.com/en/dict/en-kr/"),
	("English ⇔ Romanian", "https://www.almaany.com/en/dict/en-ro/"),
	("English ⇔ Swedish", "https://www.almaany.com/se/dict/en-se/"),
	("English ⇔ Turkish", "https://www.almaany.com/tr/dict/en-tr/"),
	("English ⇔ Arabic", "https://www.almaany.com/en/dict/ar-en/")
]

def getListOfDictionaryNames():
	return [name for name, url in dictionaries_nameAndUrl]

def getUrlOfDictionary(i=0, default= False):
	''' Getting the url of a specific dictionary from its index
	 i is the index of dictionary(selected in dialog).
	 if default= True, then we want the index of default dictionary.
	'''
	if default:
		# Index of default dictionary
		i= config.conf["almaanyEnglishDictionaries"]["defaultDictionary"]
	# The url is the second item in the tuple.
	dict_url= dictionaries_nameAndUrl[i][1]
	return dict_url

class MyDialog(wx.Dialog):
	''' Almaany Dictionaries dialog, contains an edit field to enter a word, and a combo box to choose dictionary.
	It pops up only if no selection found.'''

	def __init__(self, parent):
		# Translators: Title of dialog.
		title= _("Almaany English Dictionaries")
		super(MyDialog, self).__init__(parent, title = title, size = (300, 500))

		panel = wx.Panel(self, -1)
		# Translators: Label of text control.
		editTextLabel= wx.StaticText(panel, -1, _("Enter a word or a phrase"))
		editBoxSizer =  wx.BoxSizer(wx.HORIZONTAL)
		editBoxSizer.Add(editTextLabel, 0, wx.ALL, 5)
		self.editTextControl= wx.TextCtrl(panel)
		editBoxSizer.Add(self.editTextControl, 1, wx.ALL|wx.EXPAND, 5)

		cumboSizer= wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Label of cumbo box to choose a dictionary.
		cumboLabel= wx.StaticText(panel, -1, _("Choose Dictionary"))
		cumboSizer.Add(cumboLabel, 0, wx.ALL, 5)
		self.cumbo= wx.Choice(panel, -1, choices= getListOfDictionaryNames())
		cumboSizer.Add(self.cumbo, 1, wx.EXPAND|wx.ALL, 5)

		buttonSizer = wx.BoxSizer(wx.VERTICAL)
		# Translators: Label of OK button.
		self.ok= wx.Button(panel, -1, _('OK'))
		self.ok.SetDefault()
		self.ok.Bind(wx.EVT_BUTTON, self.onOk)
		buttonSizer.Add(self.ok, 0,wx.ALL, 10)
		# Translators: Label of Cancel button.
		self.cancel = wx.Button(panel, wx.ID_CANCEL, _('cancel'))
		self.cancel.Bind(wx.EVT_BUTTON, self.onCancel)
		buttonSizer.Add(self.cancel, 0, wx.EXPAND|wx.ALL, 10)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		mainSizer.Add(editBoxSizer, 1, wx.EXPAND|wx.ALL, 10)
		mainSizer.Add(cumboSizer, 1, wx.EXPAND|wx.ALL,10)
		mainSizer.Add(buttonSizer, 0, wx.EXPAND|wx.ALL, 5)
		panel.SetSizer(mainSizer)

	def postInit(self):
		indexOfDefault= config.conf["almaanyEnglishDictionaries"]["defaultDictionary"]
		self.cumbo.SetSelection(indexOfDefault)
		self.editTextControl.SetFocus()

	@staticmethod
	def getMeaning(text, base_url):
	# text is the word or phrase to get translation for.
		t= MyThread(text, base_url)
		t.start()
		while not t.meaning and not t.error and t.is_alive():
			beep(500, 100)
			time.sleep(0.5)
		t.join()

		title= _('Translation Result')
		#title= u''
		useDefaultFullBrowser= config.conf["almaanyEnglishDictionaries"]["windowType"]== 0
		useBrowserWindowOnly= config.conf["almaanyEnglishDictionaries"]["windowType"]== 1
		useNvdaMessageBox= config.conf["almaanyEnglishDictionaries"]["windowType"]== 2
		if t.meaning and useDefaultFullBrowser:
			openBrowserWindow('default', t.meaning, directive= '', default= True)
		elif t.meaning and useBrowserWindowOnly:
			if 'Firefox' in browsers and not appIsRunning('firefox.exe'):
				openBrowserWindow('Firefox', t.meaning, directive= ' --kiosk ')
			elif 'Google Chrome' in browsers and not appIsRunning('chrome.exe'):
				openBrowserWindow('Google Chrome', t.meaning, directive= ' -kiosk ')
			elif 'Internet Explorer' in browsers:
				openBrowserWindow('Internet Explorer', t.meaning, directive= ' -k -private ')
		elif t.meaning and useNvdaMessageBox:
			queueHandler.queueFunction(queueHandler.eventQueue, ui.browseableMessage, t.meaning, title=title, isHtml=True)
			return
		elif t.error:
			if t.error== "HTTP Error 410: Gone":
				msg= "No meaning found"
			elif t.error== "<urlopen error [Errno 11001] getaddrinfo failed>":
				msg= "Most likely no internet connection"
			else:
				msg= t.error
			queueHandler.queueFunction(queueHandler.eventQueue, ui.message, _("Sorry, An Error Happened({})".format(msg)))

	def onOk(self, e):
		# word or phrase to be translated.
		word= self.editTextControl.GetValue()
		# stripping white spaces.
		word= word.strip()
		if not word:
			# Return focus to edit control.
			self.editTextControl.SetFocus()
			return
		else:
			# Selecting the dictionary.
			i= self.cumbo.GetSelection()
			# The url is the second item in the tuple.
			dict_url= dictionaries_nameAndUrl[i][1]
			self.getMeaning(word, dict_url)
			closeDialogAfterRequiringTranslation= config.conf["almaanyEnglishDictionaries"]["closeDialogAfterRequiringTranslation"]
			if closeDialogAfterRequiringTranslation:
				wx.CallLater(4000, self.Destroy)

	def onCancel (self, e):
		self.Destroy()
