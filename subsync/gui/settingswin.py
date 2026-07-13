import subsync.gui.layout.settingswin
from subsync.gui.components.filedlg import showSaveFileDlg
from subsync.gui.suspendlock import SuspendBlocker
from subsync.settings import settings, Settings
from subsync.data import descriptions
from subsync import config
import wx


class SettingsWin(subsync.gui.layout.settingswin.SettingsWin):
    def __init__(self, parent):
        super().__init__(parent)
        self.m_outputCharEnc.SetString(0, _('same as input subtitles'))

        self.m_buttonMaxPointDistInfo.message = descriptions.maxPointDistInfo
        self.m_buttonMinPointsNoInfo.message = descriptions.minPointsNoInfo
        self.m_buttonMinWordLenInfo.message = descriptions.minWordLenInfo
        self.m_buttonMinWordSimInfo.message = descriptions.minWordSimInfo
        self.m_buttonMinCorrelationInfo.message = descriptions.minCorrelationInfo
        self.m_buttonMinWordProbInfo.message = descriptions.minWordProbInfo
        self.m_buttonOutTimeOffsetInfo.message = descriptions.outTimeOffset
        self.m_buttonJobsNoInfo.message = descriptions.jobsNoInfo
        self.m_buttonPreventSystemSuspend.message = descriptions.preventSystemSuspendInfo
        self.m_panelSynchro.GetSizer().AddGrowableCol(1)

        if not SuspendBlocker.hasLock():
            self.m_preventSystemSuspend.Hide()
            self.m_buttonPreventSystemSuspend.Hide()

        if not config.assetupd:
            self.m_textUpdates.Hide()
            self.m_autoUpdate.Hide()
            self.m_askForUpdate.Hide()

        # Segment M: speech-engine selector (added programmatically so the
        # generated layout file stays untouched). Named 'm_choiceSpeechEngine'
        # so it is NOT auto-handled by settingsFieldsGen (wx.Choice has no
        # Get/SetValue) - it is handled explicitly in get/setSettings.
        self._speechEngines = ['sphinx', 'vosk', 'whisper']
        synchroSizer = self.m_panelSynchro.GetSizer()  # wxGridBagSizer
        self.m_labelSpeechEngine = wx.StaticText(self.m_panelSynchro,
                label=_('Speech recognition engine:'))
        self.m_choiceSpeechEngine = wx.Choice(self.m_panelSynchro,
                choices=[_('PocketSphinx (classic)'), _('Vosk (recommended)'),
                    _('Whisper (most accurate)')])

        row = 0
        for child in synchroSizer.GetChildren():
            try:
                pos = child.GetPos()
                span = child.GetSpan()
                row = max(row, pos.GetRow() + span.GetRowspan())
            except Exception:
                pass
        synchroSizer.Add(self.m_labelSpeechEngine, wx.GBPosition(row, 0),
                wx.GBSpan(1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        synchroSizer.Add(self.m_choiceSpeechEngine, wx.GBPosition(row, 1),
                wx.GBSpan(1, 1), wx.EXPAND | wx.ALL, 5)

        # #165(b): default launch view (basic / batch). Added to the General panel.
        self._startViews = ['basic', 'batch']
        # #165(c): dark theme (best-effort, opt-in).
        self._darkModes = ['light', 'dark', 'system']

        # App interface language.
        from subsync import translations
        self._langCodes = translations.listLanguages()
        _langNames = {'en': 'English', 'hr': 'Croatian', 'de': 'German',
                      'pl': 'Polish', 'sv': 'Swedish', 'no': 'Norwegian',
                      'it': 'Italian'}
        _langLabels = [_langNames.get(c, c) for c in self._langCodes]
        self.m_labelLanguage = wx.StaticText(self.m_panelGeneral,
                label=_('Interface language:'))
        self.m_choiceLanguage = wx.Choice(self.m_panelGeneral, choices=_langLabels)

        genSizer = self.m_panelGeneral.GetSizer()
        self.m_labelStartView = wx.StaticText(self.m_panelGeneral,
                label=_('Start view:'))
        self.m_choiceStartView = wx.Choice(self.m_panelGeneral,
                choices=[_('Basic'), _('Batch')])
        self.m_labelDarkMode = wx.StaticText(self.m_panelGeneral,
                label=_('Theme:'))
        self.m_choiceDarkMode = wx.Choice(self.m_panelGeneral,
                choices=[_('Light'), _('Dark (experimental)'), _('System')])

        # Output translation (optional): "off" + one entry per known language.
        from subsync.data import languages as _languages
        self._translateCodes = [None] + [l.code3 for l in _languages.languages]
        _translateLabels = [_('Off (no translation)')] + [
                _languages.getName(l.code3) for l in _languages.languages]
        self.m_labelTranslate = wx.StaticText(self.m_panelGeneral,
                label=_('Also translate output to:'))
        self.m_choiceTranslate = wx.Choice(self.m_panelGeneral, choices=_translateLabels)
        self._translateEngines = ['google', 'deepl']
        self.m_labelTranslateEngine = wx.StaticText(self.m_panelGeneral,
                label=_('Translation engine:'))
        self.m_choiceTranslateEngine = wx.Choice(self.m_panelGeneral,
                choices=[_('Google Translate'), _('DeepL')])

        from subsync.synchro import styling
        _styleLabels = styling.presetLabels()
        self._styleIds = [''] + list(_styleLabels.keys())
        self._styleNames = [_('(none)')] + [
                '%s (%s)' % (_styleLabels[k], k) for k in self._styleIds[1:]]
        self.m_labelStyle = wx.StaticText(self.m_panelGeneral,
                label=_('ASS subtitle position:'))
        self.m_choiceStyle = wx.Choice(self.m_panelGeneral, choices=self._styleNames)
        self.m_checkStyleBox = wx.CheckBox(self.m_panelGeneral,
                label=_('Opaque background box'))
        self.m_checkAiPolish = wx.CheckBox(self.m_panelGeneral,
                label=_('AI polish translated output'))
        try:
            grow = 0
            for child in genSizer.GetChildren():
                try:
                    grow = max(grow, child.GetPos().GetRow() + child.GetSpan().GetRowspan())
                except Exception:
                    pass
            genSizer.Add(self.m_labelLanguage, wx.GBPosition(grow, 0),
                    wx.GBSpan(1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            genSizer.Add(self.m_choiceLanguage, wx.GBPosition(grow, 1),
                    wx.GBSpan(1, 1), wx.EXPAND | wx.ALL, 5)
            genSizer.Add(self.m_labelStartView, wx.GBPosition(grow + 1, 0),
                    wx.GBSpan(1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            genSizer.Add(self.m_choiceStartView, wx.GBPosition(grow + 1, 1),
                    wx.GBSpan(1, 1), wx.EXPAND | wx.ALL, 5)
            genSizer.Add(self.m_labelDarkMode, wx.GBPosition(grow + 2, 0),
                    wx.GBSpan(1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            genSizer.Add(self.m_choiceDarkMode, wx.GBPosition(grow + 2, 1),
                    wx.GBSpan(1, 1), wx.EXPAND | wx.ALL, 5)
            genSizer.Add(self.m_labelTranslate, wx.GBPosition(grow + 3, 0),
                    wx.GBSpan(1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            genSizer.Add(self.m_choiceTranslate, wx.GBPosition(grow + 3, 1),
                    wx.GBSpan(1, 1), wx.EXPAND | wx.ALL, 5)
            genSizer.Add(self.m_labelTranslateEngine, wx.GBPosition(grow + 4, 0),
                    wx.GBSpan(1, 1), wx.EXPAND | wx.ALL, 5)
            genSizer.Add(self.m_choiceTranslateEngine, wx.GBPosition(grow + 4, 1),
                    wx.GBSpan(1, 1), wx.EXPAND | wx.ALL, 5)
            genSizer.Add(self.m_labelStyle, wx.GBPosition(grow + 5, 0),
                    wx.GBSpan(1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            genSizer.Add(self.m_choiceStyle, wx.GBPosition(grow + 5, 1),
                    wx.GBSpan(1, 1), wx.EXPAND | wx.ALL, 5)
            genSizer.Add(self.m_checkStyleBox, wx.GBPosition(grow + 6, 1),
                    wx.GBSpan(1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            genSizer.Add(self.m_checkAiPolish, wx.GBPosition(grow + 7, 1),
                    wx.GBSpan(1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        except Exception:
            # General panel sizer is not a GridBagSizer - append at the end
            for w in (self.m_labelLanguage, self.m_choiceLanguage,
                    self.m_labelStartView, self.m_choiceStartView,
                    self.m_labelDarkMode, self.m_choiceDarkMode,
                    self.m_labelTranslate, self.m_choiceTranslate,
                    self.m_labelTranslateEngine, self.m_choiceTranslateEngine,
                    self.m_labelStyle, self.m_choiceStyle, self.m_checkStyleBox,
                    self.m_checkAiPolish):
                genSizer.Add(w, 0, wx.ALL, 5)

        self.setSettings(settings())

        self.m_panelSynchro.Fit()
        self.Fit()

        from subsync.gui import theme
        theme.apply(self)

    def setSettings(self, settings):
        self.settings = Settings(settings)

        self.m_jobsNo.SetValue(settings.getJobsNo())

        engine = settings.get('speechEngine') or 'sphinx'
        self.m_choiceSpeechEngine.SetSelection(
                self._speechEngines.index(engine) if engine in self._speechEngines else 0)

        lang = settings.get('language') or 'en'
        self.m_choiceLanguage.SetSelection(
                self._langCodes.index(lang) if lang in self._langCodes else self._langCodes.index('en'))

        startView = settings.get('startView') or 'basic'
        self.m_choiceStartView.SetSelection(
                self._startViews.index(startView) if startView in self._startViews else 0)

        darkMode = settings.get('darkMode') or 'light'
        self.m_choiceDarkMode.SetSelection(
                self._darkModes.index(darkMode) if darkMode in self._darkModes else 0)

        translateTo = settings.get('translateTo')
        self.m_choiceTranslate.SetSelection(
                self._translateCodes.index(translateTo) if translateTo in self._translateCodes else 0)
        translateEngine = settings.get('translateEngine') or 'google'
        self.m_choiceTranslateEngine.SetSelection(
                self._translateEngines.index(translateEngine) if translateEngine in self._translateEngines else 0)

        subtitleStyle = settings.get('subtitleStyle') or ''
        self.m_choiceStyle.SetSelection(
                self._styleIds.index(subtitleStyle) if subtitleStyle in self._styleIds else 0)
        self.m_checkStyleBox.SetValue(not not settings.get('subtitleStyleBox'))
        self.m_checkAiPolish.SetValue(not not settings.get('aiPolish'))

        for field, key, val in self.settingsFieldsGen():
            if val != None:
                field.SetValue(val)

        self.m_appendLangCode2.SetValue(settings.appendLangCode == 2)
        self.m_appendLangCode3.SetValue(settings.appendLangCode in [3, True])

        jobsNo = self.settings.jobsNo
        self.m_checkAutoJobsNo.SetValue(jobsNo == None)
        self.m_jobsNo.Enable(jobsNo != None)

        logLevel = int(self.settings.logLevel // 10)
        if logLevel >= 0 and logLevel < self.m_choiceLogLevel.GetCount():
            self.m_choiceLogLevel.SetSelection(logLevel)

        logFile = self.settings.logFile
        self.m_checkLogToFile.SetValue(logFile != None)
        self.m_textLogFilePath.Enable(logFile != None)
        self.m_buttonLogFileSelect.Enable(logFile != None)
        self.m_textLogFilePath.SetValue(logFile if logFile else '')

        logBlacklist = self.settings.logBlacklist
        if logBlacklist == None:
            logBlacklist = []
        self.m_textLogBlacklist.SetValue('\n'.join(logBlacklist))

    def getSettings(self):
        for field, key, val in self.settingsFieldsGen():
            setattr(self.settings, key, field.GetValue())

        sel = self.m_choiceSpeechEngine.GetSelection()
        if sel != wx.NOT_FOUND:
            self.settings.speechEngine = self._speechEngines[sel]

        selv = self.m_choiceStartView.GetSelection()
        if selv != wx.NOT_FOUND:
            self.settings.startView = self._startViews[selv]

        seld = self.m_choiceDarkMode.GetSelection()
        if seld != wx.NOT_FOUND:
            self.settings.darkMode = self._darkModes[seld]

        sell = self.m_choiceLanguage.GetSelection()
        if sell != wx.NOT_FOUND:
            self.settings.language = self._langCodes[sell]
            from subsync import translations
            translations.setLanguage(self._langCodes[sell])

        selt = self.m_choiceTranslate.GetSelection()
        if selt != wx.NOT_FOUND:
            self.settings.translateTo = self._translateCodes[selt]
        sele = self.m_choiceTranslateEngine.GetSelection()
        if sele != wx.NOT_FOUND:
            self.settings.translateEngine = self._translateEngines[sele]

        sels = self.m_choiceStyle.GetSelection()
        if sels != wx.NOT_FOUND:
            val = self._styleIds[sels]
            self.settings.subtitleStyle = val if val else None
        self.settings.subtitleStyleBox = self.m_checkStyleBox.GetValue()
        self.settings.aiPolish = self.m_checkAiPolish.GetValue()

        self.settings.appendLangCode = False
        if self.m_appendLangCode2.IsChecked():
            self.settings.appendLangCode = 2
        elif self.m_appendLangCode3.IsChecked():
            self.settings.appendLangCode = 3

        if self.m_checkAutoJobsNo.IsChecked():
            self.settings.jobsNo = None

        logLevel = self.m_choiceLogLevel.GetSelection()
        if logLevel != wx.NOT_FOUND:
            self.settings.logLevel = logLevel * 10

        if self.m_checkLogToFile.IsChecked():
            self.settings.logFile = self.m_textLogFilePath.GetValue()
        else:
            self.settings.logFile = None

        logBlacklist = self.m_textLogBlacklist.GetValue().split()
        if len(logBlacklist) > 0:
            self.settings.logBlacklist = logBlacklist
        else:
            self.settings.logBlacklist = None

        return self.settings

    def settingsFieldsGen(self):
        for key in self.settings.keys():
            field = 'm_' + key
            if hasattr(self, field):
                yield getattr(self, field), key, self.settings.get(key)

    def onAppendLangCode2Check(self, event):
        if self.m_appendLangCode2.IsChecked():
            self.m_appendLangCode3.SetValue(False)

    def onAppendLangCode3Check(self, event):
        if self.m_appendLangCode3.IsChecked():
            self.m_appendLangCode2.SetValue(False)

    def onCheckAutoJobsNoCheck(self, event):
        auto = self.m_checkAutoJobsNo.IsChecked()
        self.m_jobsNo.Enable(not auto)

    def onCheckLogToFileCheck(self, event):
        enabled = self.m_checkLogToFile.IsChecked()
        self.m_textLogFilePath.Enable(enabled)
        self.m_buttonLogFileSelect.Enable(enabled)
        if not self.m_textLogFilePath.GetValue():
            if not self.selectLogFile():
                self.m_checkLogToFile.SetValue(False)

    def onButtonLogFileSelectClick(self, event):
        self.selectLogFile()

    def selectLogFile(self):
        path = showSaveFileDlg(self)
        if path:
            self.m_textLogFilePath.SetValue(path)
        return path

    def onButtonRestoreDefaultsClick(self, event):
        dlg = wx.MessageDialog(
                self,
                _('Are you sure you want to reset settings to defaults?'),
                _('Restore defaults'),
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

        if dlg.ShowModal() == wx.ID_YES:
            self.setSettings(Settings())
