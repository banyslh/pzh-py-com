import wx
import sys, os
import win
import formatter
import serial
import serial.tools.list_ports
import threading

s_serialPort = serial.Serial()
s_recvInterval = 0.5

s_recvStatusFieldIndex = 0
s_sendStatusFieldIndex = 1
s_infoStatusFieldIndex = 2

s_recvStatusStr = 'Recv: '
s_recvTotalBytes = 0
s_sendStatusStr = 'Send: '
s_sendTotalBytes = 0

s_formatter = formatter.formatter()
s_lastRecvFormat = None
s_lastSendFormat = None

class mainWin(win.com_win):

    def __init__(self, parent):
        win.com_win.__init__(self, parent)
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap( u"../img/pzh-com.ico", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)
        self.m_bitmap_led.SetBitmap(wx.Bitmap( u"../img/led_black.png", wx.BITMAP_TYPE_ANY ))
        self.refreshComPort(None)
        self.m_choice_comPort.SetSelection( 0 )

    def refreshComPort( self, event ):
        comports = list(serial.tools.list_ports.comports())
        ports = [None] * len(comports)
        for i in range(len(comports)):
            comport = list(comports[i])
            # example comport = [u'COM3', u'Intel(R) Active Management Technology - SOL (COM3)', u'PCI\\VEN_8086&DEV_9D3D&SUBSYS_06DC1028&REV_21\\3&11583659&0&B3']
            ports[i] = comport[0] + ' - ' + comport[1]
        self.m_choice_comPort.Clear()
        self.m_choice_comPort.SetItems(ports)

    def setPort ( self ):
        index = self.m_choice_comPort.GetSelection()
        comPort = self.m_choice_comPort.GetString(index)
        comPort = comPort.split(' - ')
        s_serialPort.port = comPort[0]

    def setBaudrate ( self ):
        index = self.m_choice_baudrate.GetSelection()
        s_serialPort.baudrate = int(self.m_choice_baudrate.GetString(index))

    def setDatabits ( self ):
        index = self.m_choice_dataBits.GetSelection()
        m_dataBits = int(self.m_choice_dataBits.GetString(index))
        if m_dataBits == 5:
            s_serialPort.bytesizes = serial.FIVEBITS
        elif m_dataBits == 6:
            s_serialPort.bytesizes = serial.SIXBITS
        elif m_dataBits == 7:
            s_serialPort.bytesizes = serial.SEVENBITS
        elif m_dataBits == 8:
            s_serialPort.bytesizes = serial.EIGHTBITS
        else:
            pass

    def setStopbits ( self ):
        index = self.m_choice_stopBits.GetSelection()
        m_stopBits = self.m_choice_stopBits.GetString(index)
        if m_stopBits == '1':
            s_serialPort.stopbits = serial.STOPBITS_ONE
        elif m_stopBits == '1.5':
            s_serialPort.stopbits = serial.STOPBITS_ONE_POINT_FIVE
        elif m_stopBits == '2':
            s_serialPort.stopbits = serial.STOPBITS_TWO
        else:
            pass

    def setParitybits ( self ):
        index = self.m_choice_parityBits.GetSelection()
        m_parityBits = self.m_choice_parityBits.GetString(index)
        if m_parityBits == 'None':
            s_serialPort.parity = serial.PARITY_NONE
        elif m_parityBits == 'Odd':
            s_serialPort.parity = serial.PARITY_ODD
        elif m_parityBits == 'Even':
            s_serialPort.parity = serial.PARITY_EVEN
        elif m_parityBits == 'Mark':
            s_serialPort.parity = serial.PARITY_MARK
        elif m_parityBits == 'Space':
            s_serialPort.parity = serial.PARITY_SPACE
        else:
            pass

    def openClosePort( self, event ):
        if s_serialPort.isOpen():
            s_serialPort.close()
            self.m_button_openClose.SetLabel('Open')
            self.m_bitmap_led.SetBitmap(wx.Bitmap( u"../img/led_black.png", wx.BITMAP_TYPE_ANY ))
            self.statusBar.SetStatusText(s_serialPort.name + ' is closed', s_infoStatusFieldIndex)
        else:
            self.statusBar.SetFieldsCount(3)
            self.statusBar.SetStatusWidths([150, 150, 400])
            self.setPort()
            self.setBaudrate()
            self.setDatabits()
            self.setStopbits()
            self.setParitybits()
            try:
                s_serialPort.open()
            except Exception, e:
                self.statusBar.SetStatusText(s_serialPort.name + ' doesn\'t exist !!!', s_infoStatusFieldIndex)
                return
            self.m_button_openClose.SetLabel('Close')
            self.m_bitmap_led.SetBitmap(wx.Bitmap( u"../img/led_green.png", wx.BITMAP_TYPE_ANY ))
            self.statusBar.SetStatusText(s_recvStatusStr + str(s_recvTotalBytes), s_recvStatusFieldIndex)
            self.statusBar.SetStatusText(s_sendStatusStr + str(s_sendTotalBytes), s_sendStatusFieldIndex)
            self.statusBar.SetStatusText(s_serialPort.name + ' is open, ' +
                                               str(s_serialPort.baudrate) + ', ' +
                                               str(s_serialPort.bytesizes) + ', ' +
                                               s_serialPort.parity + ', ' +
                                               str(s_serialPort.stopbits), s_infoStatusFieldIndex)
            s_serialPort.reset_input_buffer()
            s_serialPort.reset_output_buffer()
            threading.Timer(s_recvInterval, self.recvData).start()

    def clearSendDisplay( self, event ):
        self.m_textCtrl_send.Clear()

    def setSendFormat( self, event ):
        lines = self.m_textCtrl_send.GetNumberOfLines()
        if lines != 0:
            m_sendFormat = self.m_choice_sendFormat.GetString(self.m_choice_sendFormat.GetSelection())
            global s_lastSendFormat
            if s_lastSendFormat == m_sendFormat:
                return
            else:
                s_lastSendFormat = m_sendFormat
            # Get existing data from textCtrl_send
            data = ''
            for i in range(0, lines):
                data += str(self.m_textCtrl_send.GetLineText(i))
            # Convert data format according to choice_sendFormat
            if m_sendFormat == 'Char':
                status, data = s_formatter.hexToChar(data)
                if not status:
                    self.m_textCtrl_send.Clear()
                    self.m_textCtrl_send.write('Invalid format! Correct example: 12 34 56 ab cd ef')
                    return
            elif m_sendFormat == 'Hex':
                data = s_formatter.charToHex(data)
            # Re-show converted data in textCtrl_send
            self.m_textCtrl_send.Clear()
            self.m_textCtrl_send.write(data)

    def sendData( self, event ):
        if s_serialPort.isOpen():
            lines = self.m_textCtrl_send.GetNumberOfLines()
            if lines != 0:
                # Get existing data from textCtrl_send
                data = ''
                for i in range(0, lines):
                    data += str(self.m_textCtrl_send.GetLineText(i))
                # Make sure data is always in 'Char' format
                m_sendFormat = self.m_choice_sendFormat.GetString(self.m_choice_sendFormat.GetSelection())
                if m_sendFormat == 'Hex':
                    status, data = s_formatter.hexToChar(data)
                    if not status:
                        self.m_textCtrl_send.Clear()
                        self.m_textCtrl_send.write('Invalid format! Correct example: 12 34 56 ab cd ef')
                        return
                # Send out data via Port
                s_serialPort.write(data)
                # Update send info in status bar
                global s_sendTotalBytes
                s_sendTotalBytes += len(data)
                self.statusBar.SetStatusText(s_sendStatusStr + str(s_sendTotalBytes), s_sendStatusFieldIndex)
        else:
            self.statusBar.SetStatusText(s_serialPort.name + ' is not open !!!', s_infoStatusFieldIndex)

    def clearRecvDisplay( self, event ):
        self.m_textCtrl_recv.Clear()

    def setRecvFormat( self, event ):
        lines = self.m_textCtrl_recv.GetNumberOfLines()
        if lines != 0:
            m_recvFormat = self.m_choice_recvFormat.GetString(self.m_choice_recvFormat.GetSelection())
            global s_lastRecvFormat
            if s_lastRecvFormat == m_recvFormat:
                return
            else:
                s_lastRecvFormat = m_recvFormat
            # Get existing data from textCtrl_recv
            data = ''
            for i in range(0, lines):
                data += str(self.m_textCtrl_recv.GetLineText(i))
            # Convert data format according to choice_recvFormat
            if m_recvFormat == 'Char':
                status, data = s_formatter.hexToChar(data)
            elif m_recvFormat == 'Hex':
                data = s_formatter.charToHex(data)
            # Re-show converted data in textCtrl_recv
            self.m_textCtrl_recv.Clear()
            self.m_textCtrl_recv.write(data)

    def recvData( self ):
        if s_serialPort.isOpen():
            num = s_serialPort.inWaiting()
            if num != 0:
                # Receive new data from Port
                data = s_serialPort.read(num)
                # Note: Assume that data is always in 'Char' format
                # Convert data format if dispaly format is 'Hex'
                m_recvFormat = self.m_choice_recvFormat.GetString(self.m_choice_recvFormat.GetSelection())
                if m_recvFormat == 'Hex':
                    data = s_formatter.charToHex(data)
                # Show new data in textCtrl_recv
                self.m_textCtrl_recv.write(data)
                # Update recv info in status bar
                global s_recvTotalBytes
                s_recvTotalBytes += len(data)
                self.statusBar.SetStatusText(s_recvStatusStr + str(s_recvTotalBytes), s_recvStatusFieldIndex)
            threading.Timer(s_recvInterval, self.recvData).start()

    def showHomepageMessage( self, event ):
        messageText = (('Code: \n    https://github.com/JayHeng/pzh-py-com.git \n') +
                       ('Doc: \n    https://www.cnblogs.com/henjay724/p/9416096.html \n'))
        wx.MessageBox(messageText, "Homepage", wx.OK | wx.ICON_INFORMATION)

    def showAboutMessage( self, event ):
        messageText = (('Author: Jay Heng \n') +
                       ('Email: hengjie1989@foxmail.com \n'))
        wx.MessageBox(messageText, "About", wx.OK | wx.ICON_INFORMATION)

if __name__ == '__main__':
    app = wx.App()

    main_win = mainWin(None)
    main_win.SetTitle(u"pzh-com v1.0.0")
    main_win.Show()

    app.MainLoop()
