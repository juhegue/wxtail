#!/usr/bin/env python
# -*- coding: cp1252 -*-
#Juan Hevilla Guerrero 12/06/2008.

import wx, sys, os, string, time
import wx.lib.buttons as buttons
from wx.lib.wordwrap import wordwrap
import wx.lib.newevent
import thread
import datetime

MAX_LINEAS=500
LINEAS_DEFECTO=10           # 0 es todo el fichero
SLEEP_TIME=0.5              # tiempo refresco de la actualizacion / tiempo de espera para finalizar
NOMBRE_APLICACION='wxtail'
SIZE_FONT=13


def GetDataDir():
    sp = wx.StandardPaths.Get()
    return sp.GetUserDataDir()


def GetConfig():
    if not os.path.exists(GetDataDir()):
        os.makedirs(GetDataDir())
    fic = os.path.join(GetDataDir(), NOMBRE_APLICACION)
    config = wx.FileConfig(localFilename = fic)
    return config


def FicDialogo(win, fichero):
    paths = []
    
    if fichero is None:
        msg = "Elija los ficheros"
        fichero = ''
        estilo = wx.FD_MULTIPLE | wx.OPEN|wx.CHANGE_DIR
    else:
        msg = "Elija un fichero"
        estilo = wx.OPEN|wx.CHANGE_DIR
        
    dlg = wx.FileDialog(
        win, message=msg,
        defaultFile=fichero,
        wildcard="Todos los archivos (*.*)|*|Archivos log (*.log)|*.log", 
        style=estilo
        )

    if dlg.ShowModal() == wx.ID_OK:
        paths = dlg.GetPaths()
            
    return paths


def GetTailData(fichero, lineas):
    data = ""
    
    if lineas == 0:
        fichero.seek(0) 
        data = fichero.read()        
    else:
        caracterLinea = 80
        while 1:
            try: 
                fichero.seek(-1 * caracterLinea * lineas,2)
            except IOError: 
				fichero.seek(0) 
                
            ficIni = 1 if fichero.tell() == 0 else 0

            numLineas = fichero.read().split("\n")
            #si en lo reservado hay lineas suficientes termina
            if (len(numLineas) > (lineas+1)) or ficIni: break
            
            #si las lineas superan lo reservado, incrementa y reintenta
            caracterLinea = caracterLinea * 1.5 

        inicio = len(numLineas)-lineas -1 if len(numLineas) > lineas else  0
        
        for i in numLineas[inicio:len(numLineas)-1]: data = data + i + "\n"        
        
    return data


# Crea una nueva clase de evento
(ActualizaPanelEvent, EVT_ACTUALIZA_PANEL) = wx.lib.newevent.NewEvent()

class TailHilo:
    def __init__(self, win, fichero):
        self.win = win
        self.fichero = fichero
        self.mantenerCorriendo = self.corriendo = False
        
    def Inicia(self):
        self.mantenerCorriendo = self.corriendo = True
        thread.start_new_thread(self.Corre, ())

    def Para(self):
        self.mantenerCorriendo = False

    def EstaCorriendo(self):
        return self.corriendo

    def PosFinalFichero(self):
		pos = self.fichero.tell()
		self.fichero.seek(0,2)
		fin = self.fichero.tell()
		self.fichero.seek(pos)
		return fin

    def Corre(self):
        self.fichero.seek(self.win.lonFicIni)        
        while self.mantenerCorriendo:
            pos = self.fichero.tell()
            linea = self.fichero.readline()
            if not linea:
                time.sleep(SLEEP_TIME)
                if self.PosFinalFichero() < pos:
                    evt = ActualizaPanelEvent(win=self.win, valor=("RED", "<Truncado>\n"))
                    wx.PostEvent(self.win, evt)
                    self.fichero.seek(0)                					
                else:				
                    self.fichero.seek(pos)
            else:
                evt = ActualizaPanelEvent(win=self.win, valor=("BLACK", linea))
                wx.PostEvent(self.win, evt)                
        self.corriendo = False
    

class Pagina(wx.Panel):
    def __init__(self, parent, nomFichero, lineas):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.parent = parent
        self.nomFichero = nomFichero        
        self.lineas = lineas
        self.fichero = None
        self.hilo = None
        self.lonFicIni = 0
        self.actualizado = False
        self.bloqueo = thread.allocate_lock()
        
        box = wx.StaticBox(self, -1)
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        bmp1 = wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16,16))
        botonFic = buttons.GenBitmapButton(self, -1, bmp1,size=(24, 24))
        botonFic.SetToolTip(wx.ToolTip("Abrir fichero"))
        
        self.txt1 = wx.TextCtrl(self, -1, nomFichero, style=wx.TE_READONLY)
        self.txt1.SetToolTip(wx.ToolTip("Nombre del fichero"))                
        
        self.st1 = wx.StaticText(self, -1, "Modificado")

        bmp2 = wx.ArtProvider_GetBitmap(wx.ART_DELETE, wx.ART_OTHER, (16,16))
        botonCerrar = buttons.GenBitmapButton(self, -1, bmp2, size=(24, 24))
        botonCerrar.SetToolTip(wx.ToolTip("Cerrar fichero"))

        bmp3 = wx.ArtProvider_GetBitmap(wx.ART_TICK_MARK, wx.ART_OTHER, (16,16))
        botonMarca = buttons.GenBitmapButton(self, -1, bmp3, size=(24, 24))
        botonMarca.SetToolTip(wx.ToolTip("Marcar como leido"))

        bmp4 = wx.ArtProvider_GetBitmap(wx.ART_REDO, wx.ART_OTHER, (16,16))
        botonRefres = buttons.GenBitmapButton(self, -1, bmp4, size=(24, 24))
        botonRefres.SetToolTip(wx.ToolTip("Recargar fichero"))

        self.label = wx.StaticText(self, -1, "Todo el fichero", 
                                    style=wx.ALIGN_CENTER)

        self.spin = wx.SpinCtrl(self, -1)
        self.spin.SetRange(0,1000)        
        self.spin.SetValue(lineas)
        self.GetTituloSpin()
        self.spin.SetToolTip(wx.ToolTip("Lineas a mostrar al cargar/recargar"))
                                            
        self.txt2 = wx.TextCtrl(self, -1, '', 
                                    style=wx.TE_MULTILINE| \
                                        wx.TE_RICH2| \
                                        wx.TE_READONLY| \
                                        wx.TE_DONTWRAP)
        self.txt2.SetFont(wx.Font(SIZE_FONT, wx.MODERN, wx.NORMAL, wx.NORMAL, False, "", wx.FONTENCODING_SYSTEM ) )
                                                
        sizerh = wx.BoxSizer(wx.HORIZONTAL)
        sizerh.Add(botonFic, 0, wx.ALIGN_BOTTOM)
        sizerh.Add((5,5), 0, wx.ALL)

        sizerv1 = wx.BoxSizer(wx.VERTICAL)
        sizerv1.Add(self.st1, 0, wx.ALIGN_CENTER)
        sizerv1.Add(self.txt1, 1, wx.EXPAND)        

        sizerh.Add(sizerv1, 1, wx.EXPAND)
        sizerh.Add((5,5), 0, wx.ALL)        

        sizerh.Add(botonMarca, 0, wx.ALIGN_BOTTOM)
        sizerh.Add((5,5), 0, wx.ALL)
        sizerh.Add(botonRefres, 0, wx.ALIGN_BOTTOM)
        sizerh.Add((5,5), 0, wx.ALL)
        
        sizerv2 = wx.BoxSizer(wx.VERTICAL)
        sizerv2.Add(self.label, 0, wx.ALIGN_CENTER)
        sizerv2.Add(self.spin, 0, wx.ALIGN_CENTER)        

        sizerh.Add(sizerv2, 0, wx.ALL)
        sizerh.Add((5,5), 0, wx.ALL)
        sizerh.Add(botonCerrar, 0, wx.ALIGN_BOTTOM)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sizerh, 0, wx.EXPAND)
        sizer.Add((10,10), 0, wx.ALL)
        sizer.Add(self.txt2, 1, wx.EXPAND)
        
        bsizer.Add(sizer, 1, wx.EXPAND)

        self.buscaData = wx.FindReplaceData()
        self.buscaData.SetFlags(wx.FR_DOWN)
        self.buscaDialogo = None
        
        #Eventos
        self.Bind(wx.EVT_BUTTON, self.OnClick, botonFic)
        self.Bind(wx.EVT_BUTTON, self.OnMarcaClick, botonMarca)
        self.Bind(wx.EVT_BUTTON, self.OnRefresClick, botonRefres)
        self.Bind(wx.EVT_BUTTON, self.OnCerrarClick, botonCerrar)                                                                
        self.Bind(wx.EVT_SPINCTRL, self.OnSpinClick, self.spin)
        self.Bind(wx.EVT_TEXT, self.OnSpinClick, self.spin)

        #Eventos del hilo
        self.Bind(EVT_ACTUALIZA_PANEL, self.OnPagActualiza)

        #Eventos dialogo buscar
        self.Bind(wx.EVT_FIND, self.OnBusca)
        self.Bind(wx.EVT_FIND_NEXT, self.OnBusca)
        self.Bind(wx.EVT_FIND_CLOSE, self.OnCierraBusqueda)

        self.SetSizer(bsizer)
        self.Layout()

    def OnBusca(self, event):
        editor = self.txt2
        
        fin = editor.GetLastPosition()
        texto = editor.GetRange(0, fin).lower()
        cadenaBusqueda = self.buscaData.GetFindString().lower()
        atras = not (self.buscaData.GetFlags() & wx.FR_DOWN)
        if atras:
            inicio = editor.GetSelection()[0]
            pos = texto.rfind(cadenaBusqueda, 0, inicio)
        else:
            inicio = editor.GetSelection()[1]
            pos = texto.find(cadenaBusqueda, inicio)
        if pos == -1 and inicio != 0:
            # no se ha encontrada la cadena
            wx.Bell()
            if atras:
                inicio = fin
                pos = texto.rfind(cadenaBusqueda, 0, inicio)
            else:
                inicio = 0
                pos = texto.find(cadenaBusqueda, inicio)
        if pos == -1:
            dlg = wx.MessageDialog(self, 'Cadena no encontrada',
                          'Cadena no encontrada',
                          wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        if self.buscaDialogo:
            if pos == -1:
                self.buscaDialogo.SetFocus()
                return
            else:
                self.buscaDialogo.Destroy()
                self.buscaDialogo = None
        editor.ShowPosition(pos)
        editor.SetSelection(pos, pos + len(cadenaBusqueda))

    def OnCierraBusqueda(self, event):
        event.GetDialog().Destroy()
        self.buscaDialogo = None

    def OnClick(self, event):
        self.AbreFichero()

    def OnMarcaClick(self, event):
        self.Marca(self.parent.CogePagActual())
        
    def OnRefresClick(self, event):
        self.Inicia()
        
    def OnCerrarClick(self, event):
        self.parent.BorraPagina()
        
    def OnSpinClick(self, event):
        self.lineas = self.spin.GetValue()
        self.GetTituloSpin()

    def OnPagActualiza(self, event):        
        color, texto = event.valor
        self.SetActualizado(True)
        
        self.txt2.Freeze()
        
        lineas = self.txt2.GetNumberOfLines()
        if lineas > MAX_LINEAS:
            self.txt2.Remove(0, lineas - MAXLINEAS)

        try:
            self.txt2.SetDefaultStyle(wx.TextAttr(color, wx.NullColour))
            self.txt2.AppendText(texto.decode('utf-8', 'ignore'))                    
        except UnicodeDecodeError, detalle:
            self.txt2.SetDefaultStyle(wx.TextAttr("RED", wx.NullColour))
            self.txt2.AppendText(u"%s\n" % detalle)           
             
        self.txt2.Thaw()

    def GetActualizado(self):
        return self.actualizado

    def SetActualizado(self, estado):
        self.bloqueo.acquire()        
        self.actualizado = estado        
        self.bloqueo.release()

    def GetTituloSpin(self):        
        if self.lineas == 0:
            self.label.SetLabel("Todo el fichero")
        elif self.lineas == 1:
            self.label.SetLabel("Utima linea")
        else:
            self.label.SetLabel("Ultimas %d lineas" % self.lineas)   
    
    def Inicia(self):
        if self.fichero is not None:
            self.Para()

        self.txt2.SetDefaultStyle(wx.TextAttr("BLUE", wx.NullColour))

        self.parent.Info("...")
        self.parent.SetPageText(self.parent.CogePagActual(), os.path.basename(self.nomFichero))

        try:
            self.fichero = open(self.nomFichero, 'r')

            data = GetTailData(self.fichero, self.lineas)
            self.lonFicIni = self.fichero.tell() 
            
            self.txt2.SetValue(data.decode('utf-8', 'ignore'))
            pos = self.txt2.GetLastPosition()
            self.txt2.SetStyle(0, pos, wx.TextAttr("BLUE", wx.NullColour))
            
            self.hilo = TailHilo(self, self.fichero)
            self.hilo.Inicia()
            
            self.EstadoFichero()
            
        except IOError, detalle:
            wx.MessageBox("Error al leer: %s\n\n%s" % (self.nomFichero, detalle), NOMBRE_APLICACION)

        except UnicodeDecodeError, detalle:
            wx.MessageBox("Error al decodificar: %s\n\n%s" % (self.nomFichero, detalle), NOMBRE_APLICACION)
    
        finally:
            self.txt2.SetDefaultStyle(wx.TextAttr("BLACK", wx.NullColour))
        
    def Para(self):
        if self.hilo is not None:
            wx.Yield()
            self.hilo.Para()

            corriendo = 1
            while corriendo:
                corriendo = self.hilo.EstaCorriendo()
                time.sleep(SLEEP_TIME)
        
        if self.fichero is not None:    
            self.fichero.close()
            self.fichero = None

    def Marca(self, pagina):
        data = self.txt2.GetValue()
        pos = self.txt2.GetLastPosition()
        self.txt2.SetStyle(0, pos, wx.TextAttr("BLUE", wx.NullColour))
        self.parent.SetPageText(pagina, os.path.basename(self.nomFichero))
        self.parent.Info("...")

    def AbreFichero(self):
        actual = self.txt1.GetValue()
        nuevo = FicDialogo(self, actual)
        try:
            self.nomFichero = nuevo[0] # esta linea da error ...
            self.txt1.SetValue(self.nomFichero)
            pag = self.parent.CogePagActual()
            self.parent.SetPageText(pag, os.path.basename(self.nomFichero))
            self.Inicia()
        except IndexError: # ...cuando no selecciona ningun fichero
            pass
        
    def EstadoFichero(self):
        try:
            statinfo = os.stat(self.nomFichero)
            t = statinfo.st_mtime
            b = statinfo.st_size        
            txt = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(t))            
            self.st1.SetLabel("Modificado: %s   bytes: %d" % (txt, b))
        except OSError:
            pass


class Notebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, wx.ID_ANY, style= wx.BK_DEFAULT)
        self.parent = parent
        
        #Eventos
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPagChanged)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def OnPagChanged(self, event):
        event.Skip(True)
        
    def OnCloseWindow(self, evt):
        self.BorraTodasPaginas()
        self.Destroy()

    def SumaPagina(self, ficheros, lineas=LINEAS_DEFECTO):
        for fichero in ficheros:
            panel = Pagina(self, fichero, lineas)
            self.AddPage(panel, os.path.basename(fichero), True)
            panel.Inicia()
                
    def BorraPagina(self):
        if self.GetPageCount() > 0:
            panel = self.GetPage(self.CogePagActual())
            panel.Para()            
            self.DeletePage(self.CogePagActual())

    def BorraTodasPaginas(self):
        busy = wx.BusyInfo("Un momento, miestras mueren los hilos...")
        wx.Yield()

        for i in range(self.GetPageCount()):
            panel = self.GetPage(i)
            if panel.hilo is not None:
                panel.hilo.Para()            

        corriendo = 1
        while corriendo:
            corriendo = 0
            for i in range(self.GetPageCount()):
                panel = self.GetPage(i)
                if panel.hilo is not None:
                    corriendo = corriendo + panel.hilo.EstaCorriendo()
            time.sleep(SLEEP_TIME)

        self.DeleteAllPages()

    def Info(self, txt):
        self.parent.Info(txt)

    def CogePagActual(self):
        return self.GetSelection()
    
    def Refresca(self):
        for i in range(self.GetPageCount()):
            pagina = self.GetPage(i)
            if pagina.GetActualizado():
                pagina.SetActualizado(False)
                #actualiza estado fichero
                pagina.EstadoFichero()
                #actualiza la pestaña
                txt = self.GetPageText(i)
                if txt[0] <> '*': self.SetPageText(i, "*%s" % txt)
                #actualiza barra de estado
                self.Info("Actualiza: %s" % pagina.nomFichero)
                #posiciona
                pos = pagina.txt2.GetLastPosition() 
                pagina.txt2.ShowPosition(pos)


# Enumeracion barra de estado
SB_INFO, SB_HORA = 0, 1

class Frame(wx.Frame):
    def __init__(self, app):
        self.LeeConfig()

        wx.Frame.__init__(self, None, -1, NOMBRE_APLICACION, 
                            size=(self.ancho,self.alto))        

        icon = wx.ArtProvider_GetIcon(wx.ART_FIND, wx.ART_OTHER, (16,16))
        self.SetIcon(icon)

        self.CreaMenu()
        self.CreaToolBar()

        sb = self.CreateStatusBar(2)
        sb.SetStatusWidths([-1, 200])
            
        self.notebook = Notebook(self)
        
        self.Info("...")
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        
        #carga inicial segun config       
        try:
            for i in self.listaFic:
                nomFic, lineas = i                
                fichero = os.path.normpath(nomFic)
                self.notebook.SumaPagina([fichero], lineas)
            self.notebook.SetSelection(self.pagSelec)
        except:
            pass
        #redireccion de stdio y stderr a una ventana
        app = wx.GetApp()
        app.RedirectStdio()        
        #timer de actualización
        self.timer = wx.PyTimer(self.Temporizador)
        self.timer.Start(1000*SLEEP_TIME*2)
        self.Temporizador()         
        #Eventos del frame
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
        self.SetSizer(sizer)
        self.Layout()

    def CreaToolBar(self):
        self.tbID1 = wx.NewId()
        self.tbID2 = wx.NewId()
        self.tbID3 = wx.NewId()
        self.tbID4 = wx.NewId()
        self.tbID5 = wx.NewId()
        self.tbID6 = wx.NewId()
        self.tbID7 = wx.NewId()
        
        tsize = (24,24)
        self.tb = self.CreateToolBar(style= wx.TB_HORIZONTAL |wx.TB_FLAT)
        self.tb.SetToolBitmapSize(tsize)
        
        self.tb.AddSeparator()
        bmp1 = wx.ArtProvider_GetBitmap(wx.ART_QUIT, wx.ART_OTHER, (16,16))
        self.tb.AddLabelTool(self.tbID1, "Salir", bmp1, shortHelp="Salir", longHelp="Cierra la ventana")
        self.tb.AddSeparator()
        bmp2 = wx.ArtProvider_GetBitmap(wx.ART_NEW, wx.ART_OTHER, (16,16))
        self.tb.AddLabelTool(self.tbID2, "Nuevo", bmp2, shortHelp="Nuevo", longHelp=u"Añade página al visor")
        self.tb.AddSeparator()
        bmp3 = wx.ArtProvider_GetBitmap(wx.ART_DELETE, wx.ART_OTHER, (16,16))
        self.tb.AddLabelTool(self.tbID3, "Cerrar todo", bmp3, shortHelp="Cerrar todo", longHelp=u"Cierra todas las páginas")
        bmp4 = wx.ArtProvider_GetBitmap(wx.ART_TICK_MARK, wx.ART_OTHER, (16,16))
        self.tb.AddLabelTool(self.tbID4, "Marca todo", bmp4, shortHelp="Marca todo", longHelp=u"Marca texto de todas las páginas como leido")
        bmp5 = wx.ArtProvider_GetBitmap(wx.ART_REDO, wx.ART_OTHER, (16,16))
        self.tb.AddLabelTool(self.tbID5, "Recargar todo", bmp5, shortHelp="Recargar todo", longHelp=u"Vuelve a cargar el fichero de todas las páginas")
        self.tb.AddSeparator()

        bmp6 = wx.ArtProvider_GetBitmap(wx.ART_FIND, wx.ART_OTHER, (16,16))
        self.tb.AddLabelTool(self.tbID6, "Buscar", bmp6, shortHelp="Buscar", longHelp="Buscar cadena")
        self.tb.AddSeparator()

        bmp7 = wx.ArtProvider_GetBitmap(wx.ART_FIND_AND_REPLACE, wx.ART_OTHER, (16,16))
        self.tb.AddLabelTool(self.tbID7, "Buscar siguiente", bmp7, shortHelp="Buscar siguiente", longHelp="Buscar cadena siguiente")
        self.tb.AddSeparator()

        self.tb.Realize()
        
        self.Bind(wx.EVT_MENU, self.OnCierra, id=self.tbID1)
        self.Bind(wx.EVT_MENU, self.OnNuevo, id=self.tbID2)
        self.Bind(wx.EVT_MENU, self.OnCerrarTodo, id=self.tbID3)        
        self.Bind(wx.EVT_MENU, self.OnMarcarTodo, id=self.tbID4)        
        self.Bind(wx.EVT_MENU, self.OnRecargarTodo, id=self.tbID5)        
        self.Bind(wx.EVT_MENU, self.OnBuscaCadena, id=self.tbID6)        
        self.Bind(wx.EVT_MENU, self.OnBuscaCadenaSiguiente, id=self.tbID7)
        
    def CreaMenu(self):
        self.menuID1 = wx.NewId()
        self.menuID2 = wx.NewId()
        self.menuID3 = wx.NewId()
        self.menuID4 = wx.NewId()
        self.menuID5 = wx.NewId()
        self.menuID6 = wx.NewId()
        self.menuID7 = wx.NewId()
        self.menuID8 = wx.NewId()
        self.menuID9 = wx.NewId()
        self.menuID10 = wx.NewId()
        
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        
        menu = wx.Menu()

        item1 = wx.MenuItem(menu, self.menuID1,"&Nuevo", u"Añade página al visor")
        bmp1 = wx.ArtProvider_GetBitmap(wx.ART_NEW, wx.ART_OTHER, (16,16))
        item1.SetBitmap(bmp1)
        menu.AppendItem(item1)

        item2 = wx.MenuItem(menu, self.menuID2,"&Abrir", u"Abre fichero en la página actual")
        bmp2 = wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16,16))
        item2.SetBitmap(bmp2)
        menu.AppendItem(item2)

        item3 = wx.MenuItem(menu, self.menuID3,"&Cerrar", u"Cierra página actual")
        bmp3 = wx.ArtProvider_GetBitmap(wx.ART_DELETE, wx.ART_OTHER, (16,16))
        item3.SetBitmap(bmp3)
        menu.AppendItem(item3)

        menu.AppendSeparator()
        
        item4 = wx.MenuItem(menu, self.menuID4,"&Marcar", "Marca texto como leido")
        bmp4 = wx.ArtProvider_GetBitmap(wx.ART_TICK_MARK, wx.ART_OTHER, (16,16))
        item4.SetBitmap(bmp4)
        menu.AppendItem(item4)
        
        item5 = wx.MenuItem(menu, self.menuID5,"&Recargar", "Vuelve a cargar el fichero")
        bmp5 = wx.ArtProvider_GetBitmap(wx.ART_REDO, wx.ART_OTHER, (16,16))
        item5.SetBitmap(bmp5)
        menu.AppendItem(item5)

        menu.AppendSeparator()
        
        item6 = wx.MenuItem(menu, self.menuID6,"&Cerrar todo", u"Cierra todas las páginas")
        bmp6 = wx.ArtProvider_GetBitmap(wx.ART_DELETE, wx.ART_OTHER, (16,16))
        item6.SetBitmap(bmp6)
        menu.AppendItem(item6)

        item7 = wx.MenuItem(menu, self.menuID7,"&Marca todo", u"Marca texto de todas las páginas como leido")
        bmp7 = wx.ArtProvider_GetBitmap(wx.ART_TICK_MARK, wx.ART_OTHER, (16,16))
        item7.SetBitmap(bmp7)
        menu.AppendItem(item7)

        item8 = wx.MenuItem(menu, self.menuID8,"&Recargar todo", u"Vuelve a cargar el fichero de todas las páginas")
        bmp8 = wx.ArtProvider_GetBitmap(wx.ART_REDO, wx.ART_OTHER, (16,16))
        item8.SetBitmap(bmp8)
        menu.AppendItem(item8)

        menu.AppendSeparator()
        
        item9 = wx.MenuItem(menu, self.menuID9,"&Salir", "Cierra la ventana")
        bmp9 = wx.ArtProvider_GetBitmap(wx.ART_QUIT, wx.ART_OTHER, (16,16))
        item9.SetBitmap(bmp9)
        menu.AppendItem(item9)

        self.menuBar.Append(menu, "&Fichero")
        
        menu1 = wx.Menu()
       
        self.menuBar.Append(menu1, "&Acerca de...")

        item10 = wx.MenuItem(menu, self.menuID10,"&Acerca de " + NOMBRE_APLICACION, '')
        menu1.AppendItem(item10)
        
        #Eventos del menu
        self.Bind(wx.EVT_MENU_OPEN, self.OnMenuOpen)
        self.Bind(wx.EVT_MENU, self.OnNuevo, id=self.menuID1)
        self.Bind(wx.EVT_MENU, self.OnAbrir, id=self.menuID2)
        self.Bind(wx.EVT_MENU, self.OnCerrar, id=self.menuID3)        
        self.Bind(wx.EVT_MENU, self.OnMarcar, id=self.menuID4)        
        self.Bind(wx.EVT_MENU, self.OnRecargar, id=self.menuID5)        
        self.Bind(wx.EVT_MENU, self.OnCerrarTodo, id=self.menuID6)        
        self.Bind(wx.EVT_MENU, self.OnMarcarTodo, id=self.menuID7)        
        self.Bind(wx.EVT_MENU, self.OnRecargarTodo, id=self.menuID8)        
        self.Bind(wx.EVT_MENU, self.OnCierra, id=self.menuID9)
        self.Bind(wx.EVT_MENU, self.OnAcerca, id=self.menuID10)
    
    def OnMenuOpen(self, event):
        nb = self.notebook
        if nb.CogePagActual() < 0: activo = False
        else: activo = True
        self.menuBar.Enable(self.menuID2, activo)
        self.menuBar.Enable(self.menuID3, activo)
        self.menuBar.Enable(self.menuID4, activo)
        self.menuBar.Enable(self.menuID5, activo)
        self.menuBar.Enable(self.menuID6, activo)       
        self.menuBar.Enable(self.menuID7, activo)       
        self.menuBar.Enable(self.menuID8, activo)

    def OnBuscaCadena(self, event):
        nb = self.notebook
        if nb.CogePagActual() < 0: return
        
        panel = nb.GetPage(nb.CogePagActual())
        
        panel.txt2.SetFocus()

        if  panel.buscaDialogo == None: 
            panel.buscaDialogo = wx.FindReplaceDialog(panel, panel.buscaData, "Buscar",
                wx.FR_NOMATCHCASE | wx.FR_NOWHOLEWORD)
            panel.buscaDialogo.Show(True)
    
    def OnBuscaCadenaSiguiente(self, event):
        nb = self.notebook
        if nb.CogePagActual() < 0: return
        
        panel = nb.GetPage(nb.CogePagActual())
        panel.txt2.SetFocus()
        
        if panel.buscaData.GetFindString():
            panel.OnBusca(event)
        else:
            self.OnBuscaCadena(event)

    def OnNuevo(self, event):
        ficheros = FicDialogo(self, None)
        self.notebook.SumaPagina(ficheros)

    def OnAbrir(self, event):
        nb = self.notebook
        if nb.CogePagActual() >= 0:
            panel = nb.GetPage(nb.CogePagActual())
            panel.AbreFichero()

    def OnCerrar(self, event):
        self.notebook.BorraPagina()

    def OnCerrarTodo(self, event):
        self.notebook.BorraTodasPaginas()

    def OnMarcar(self, event):
        nb = self.notebook
        if nb.CogePagActual() >= 0:
            panel = nb.GetPage(nb.CogePagActual())
            panel.Marca(nb.CogePagActual())

    def OnRecargar(self, event):        
        nb = self.notebook
        if nb.CogePagActual() >= 0:
            panel = nb.GetPage(nb.CogePagActual())
            panel.Inicia()

    def OnCierra(self, event):
        self.Close()

    def OnAcerca(self, event):
        info = wx.AboutDialogInfo()
        info.Name = NOMBRE_APLICACION
        info.Version = "0.0.1"
        info.Copyright = u"(C) 2008 Software de dominio público"
        info.Description = wordwrap(
            u"\nEste progama es un tail gráfico."
            
            "\n\n(Un ejemplo de thread.)\n",
            350, wx.ClientDC(self))
        info.WebSite = ("http://es.wikipedia.org/wiki/Tail", u"Definición")
        info.Developers = [ u"Juan Hevilla Guerreo (Coín, Málaga, España)", ]        
        #info.License = wordwrap(licenciaTxt, 500, wx.ClientDC(self))

        wx.AboutBox(info)

    def OnMarcarTodo(self, event):
        nb = self.notebook
        for i in range(nb.GetPageCount()):
            panel = nb.GetPage(i)
            panel.Marca(i)

    def OnRecargarTodo(self, event):        
        nb = self.notebook
        lis = []

        for i in range(nb.GetPageCount()):
            panel = nb.GetPage(i)
            lis.append([panel.nomFichero, panel.lineas])
            
        nb.BorraTodasPaginas()
        
        for nomFichero, lineas in lis:            
            nb.SumaPagina([nomFichero], lineas)
        
    def OnCloseWindow(self, event):
        self.GrabaConfig()
        self.notebook.Close()
        event.Skip(True)

    def OnSize(self, event):
        self.ancho, self.alto = self.GetSizeTuple()
        event.Skip(True)

    def LeeConfig(self):
        self.alto, self.ancho = 480, 640
        self.listaFic = []
        self.pagSelec = -1
        self.config = GetConfig()
        try:
            val = self.config.Read('AnchoAlto')
            if val: self.ancho, self.alto = eval(val)    

            val = self.config.Read('Ficheros')
            if val: self.listaFic = eval(val)

            val = self.config.Read('Seleccionada')
            if val: self.pagSelec = eval(val)
        except:
            self.config.DeleteAll()
            
    def GrabaConfig(self):
        lis = []        
        for i in range(self.notebook.GetPageCount()):
            panel = self.notebook.GetPage(i)
            nomFic = panel.nomFichero
            lineas = panel.lineas
            lis.append([nomFic, lineas])
            
        self.config.Write('Ficheros', str(lis))
        self.config.Write('Seleccionada', str(self.notebook.CogePagActual()))
        self.config.Write('AnchoAlto', str([self.ancho,self.alto]))

    def Info(self, txt):
        self.SetStatusText(txt, SB_INFO)

    def Temporizador(self):
        t = time.localtime(time.time())
        txt = time.strftime("(%b) %d/%m/%Y %H:%M", t)        
        self.SetStatusText(txt, SB_HORA)
        
        if self.notebook:
            self.notebook.Refresca()

    def __del__(self):
        self.timer.stop()
        del self.timer


class MyApp(wx.App):    
    def __init__(self, redirect=False):        
        wx.App.__init__(self, redirect)    
        
    def OnInit(self):
        self.SetAppName(NOMBRE_APLICACION)     
     
        frame = Frame(self)
        frame.Show()
        return True
    
    def OnExit(self):        
        pass


def main():
    try:
        path = os.path.dirname(__file__)
        os.chdir(path)
    except:
        pass

    app = MyApp()
    app.MainLoop()
    
if __name__ == '__main__':
    main()



