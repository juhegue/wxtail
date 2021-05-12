;--------------------------------
;Include Modern UI

    !include "MUI2.nsh"
    !include "x64.nsh"

;-------------------------------
; Iconos del instalador

    !define MUI_ICON "wxtail.ico"
    !define MUI_HEADERIMAGE
    !define MUI_HEADERIMAGE_BITMAP "wxtail.png"
    !define MUI_HEADERIMAGE_RIGHT

;--------------------------------
;General
    !define APP "wxtail"
    !define DES "Tail gráfico"
    !define EMP "Juhegue"

    ;Name and file
    Name "${DES}"
    OutFile "${APP}_install.exe"

    ;Default installation folder.  No se usa ya que en la función .onInit se asigna
;   InstallDir "$PROGRAMFILES64\${APP}"

    ;Get installation folder from registry if available
    InstallDirRegKey HKCU "Software\${EMP}\${APP}" ""

    ;Request application privileges for Windows Vista
    RequestExecutionLevel admin

;--------------------------------
;Obtiene el path de instalacion

    Function .onInit
        ${If} $InstDir == ""
            StrCpy $InstDir "$ProgramFiles64\${EMP}\${APP}"
        ${EndIf}
    FunctionEnd

;--------------------------------
;Interface Settings

    !define MUI_ABORTWARNING

;--------------------------------
;Pages

    !insertmacro MUI_PAGE_DIRECTORY
    !insertmacro MUI_PAGE_INSTFILES

    !insertmacro MUI_UNPAGE_CONFIRM
    !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

    !insertmacro MUI_LANGUAGE "Spanish"

;--------------------------------
;Installer Sections

Section "Dummy Section" SecDummy

    SetOutPath "$INSTDIR"
    File "dist\libcrypto-1_1.dll"
    File "dist\libssl-1_1.dll"
    File "dist\wxbase315u_net_vc140_x64.dll"
    File "dist\wxbase315u_vc140_x64.dll"
    File "dist\wxmsw315u_core_vc140_x64.dll"
    File "dist\wxmsw315u_html_vc140_x64.dll"
    File "dist\wxtail.exe"
    File "wxtail.ico"

    CreateShortCut "$DESKTOP\${APP}.lnk" "$INSTDIR\${APP}.exe" "" "$INSTDIR\${APP}.ico"

    CreateDirectory "$SMPROGRAMS\${EMP}"
    CreateDirectory "$SMPROGRAMS\${EMP}\${APP}"
    CreateShortCut "$SMPROGRAMS\${EMP}\${APP}\${APP}.lnk" "$INSTDIR\${APP}.exe" "" "$INSTDIR\${APP}.ico"
    CreateShortCut "$SMPROGRAMS\${EMP}\${APP}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0

    ;Store installation folder
    WriteRegStr HKCU "Software\${EMP}\${APP}" "" $INSTDIR

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd


;--------------------------------
;Uninstaller Section

Section "Uninstall"
    Delete "libcrypto-1_1.dll"
    Delete "libssl-1_1.dll"
    Delete "wxbase315u_net_vc140_x64.dll"
    Delete "wxbase315u_vc140_x64.dll"
    Delete "wxmsw315u_core_vc140_x64.dll"
    Delete "wxmsw315u_html_vc140_x64.dll"
    Delete "wxtail.exe"
    Delete "wxtail.ico"

    DeleteRegKey /ifempty HKCU "Software\${EMP}\${APP}"

    Delete "$DESKTOP\${APP}.lnk"

    Delete "$SMPROGRAMS\${EMP}\${APP}\${APP}.lnk"
    Delete "$SMPROGRAMS\${EMP}\${APP}\Uninstall.lnk"
    RMDIR  "$SMPROGRAMS\${EMP}\${APP}"
    RMDIR  "$SMPROGRAMS\${EMP}"

    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"

SectionEnd