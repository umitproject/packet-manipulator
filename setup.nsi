!define py2exeOutputDir 'dist'
!define exe 'PacketManipulator.exe'
!define icon 'C:\PacketManipulator\PM\share\pixmaps\umit\pm-icon48.ico'

!include "MUI.nsh"

;==============================================================================
; General section
;==============================================================================

!ifdef compressor
	SetCompressor ${compressor}
!else
	SetCompress Off
!endif

Name "PacketManipulator"
OutFile "${exe}-installer.exe"
InstallDir "$PROGRAMFILES\PacketManipulator"

!ifdef icon
	Icon ${icon}
!endif

; Get installation folder from registry if avaiable
InstallDirRegKey HKCU "Software\PacketManipulator" ""

;==============================================================================
; Interface Settings
;==============================================================================

!define MUI_ABORTWARNING

;==============================================================================
; Pages
;==============================================================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "COPYING"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;==============================================================================
; Languages
;==============================================================================

!insertmacro MUI_LANGUAGE "English"

Section
	SetOutPath '$INSTDIR'
	File /r '${py2exeOutputDir}\*.*'

	; Store installation folder
	WriteRegStr HKCU "Software\PacketManipulator" "" $INSTDIR

	; Create uninstaller
	WriteUninstaller "$INSTDIR\Uninstall.exe"

	SetOutPath "$SMPROGRAMS\PacketManipulator\"
	CreateShortCut "$SMPROGRAMS\PacketManipulator\PacketManipulator.lnk" "$INSTDIR\PacketManipulator.exe"
	CreateShortCut "$SMPROGRAMS\PacketManipulator\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
	RMDir /r "$SMPROGRAMS\PacketManipulator\"
	RMDir /r "$INSTDIR"

	DeleteRegKey /ifempty HKCU "Software\PacketManipulator"
SectionEnd
