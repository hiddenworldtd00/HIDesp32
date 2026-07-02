"""
Module de contrôle PC pour HIDesp32
Contrôle du clavier, souris, volume, luminosité, etc.
"""

import pyautogui
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import ctypes
import os
import subprocess
import platform

class PCController:
    """Contrôleur PC complet"""
    
    def __init__(self):
        self.system = platform.system()
        self._init_audio()
    
    def _init_audio(self):
        """Initialise le contrôle audio"""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = interface.QueryInterface(IAudioEndpointVolume)
        except:
            self.volume = None
    
    # === CONTRÔLE SOURIS ===
    def mouse_move(self, x, y, duration=0.5):
        """Déplace la souris"""
        pyautogui.moveTo(x, y, duration=duration)
        return f"Souris déplacée vers ({x}, {y})"
    
    def mouse_click(self, button='left'):
        """Clique avec la souris"""
        pyautogui.click(button=button)
        return f"Clic {button} effectué"
    
    def mouse_double_click(self):
        """Double-clic"""
        pyautogui.doubleClick()
        return "Double-clic effectué"
    
    def mouse_right_click(self):
        """Clic droit"""
        pyautogui.rightClick()
        return "Clic droit effectué"
    
    def mouse_scroll(self, amount):
        """Défilement de la souris"""
        pyautogui.scroll(amount)
        return f"Défilement de {amount}"
    
    def get_mouse_position(self):
        """Retourne la position de la souris"""
        x, y = pyautogui.position()
        return f"Position: ({x}, {y})"
    
    # === CONTRÔLE CLAVIER ===
    def key_press(self, key):
        """Appuie sur une touche"""
        pyautogui.press(key)
        return f"Touche {key} pressée"
    
    def key_hotkey(self, *keys):
        """Raccourci clavier"""
        pyautogui.hotkey(*keys)
        return f"Raccourci {'+'.join(keys)} effectué"
    
    def type_text(self, text, interval=0.01):
        """Tape du texte"""
        pyautogui.typewrite(text, interval=interval)
        return f"Texte tapé: {text[:50]}..."
    
    # === CONTRÔLE VOLUME ===
    def set_volume(self, level):
        """Règle le volume (0-100)"""
        if self.volume:
            self.volume.SetMasterVolumeLevelScalar(level / 100, None)
            return f"Volume réglé à {level}%"
        return "Contrôle volume non disponible"
    
    def get_volume(self):
        """Retourne le volume actuel"""
        if self.volume:
            vol = self.volume.GetMasterVolumeLevelScalar() * 100
            return f"Volume actuel: {vol:.0f}%"
        return "N/A"
    
    def volume_mute(self):
        """Mute/Démute"""
        if self.volume:
            self.volume.SetMute(not self.volume.GetMute(), None)
            return "Mute basculé"
        return "N/A"
    
    def volume_up(self):
        """Augmente le volume"""
        if self.volume:
            current = self.volume.GetMasterVolumeLevelScalar()
            self.volume.SetMasterVolumeLevelScalar(min(1.0, current + 0.1), None)
            return "Volume augmenté"
        return "N/A"
    
    def volume_down(self):
        """Diminue le volume"""
        if self.volume:
            current = self.volume.GetMasterVolumeLevelScalar()
            self.volume.SetMasterVolumeLevelScalar(max(0.0, current - 0.1), None)
            return "Volume diminué"
        return "N/A"
    
    # === CONTRÔLE LUMINOSITÉ ===
    def set_brightness(self, level):
        """Règle la luminosité (0-100)"""
        try:
            sbc.set_brightness(level)
            return f"Luminosité réglée à {level}%"
        except:
            return "Contrôle luminosité non disponible"
    
    def get_brightness(self):
        """Retourne la luminosité actuelle"""
        try:
            brightness = sbc.get_brightness()
            return f"Luminosité: {brightness}%"
        except:
            return "N/A"
    
    def brightness_up(self):
        """Augmente la luminosité"""
        try:
            current = sbc.get_brightness()
            sbc.set_brightness(min(100, current + 10))
            return "Luminosité augmentée"
        except:
            return "N/A"
    
    def brightness_down(self):
        """Diminue la luminosité"""
        try:
            current = sbc.get_brightness()
            sbc.set_brightness(max(0, current - 10))
            return "Luminosité diminuée"
        except:
            return "N/A"
    
    # === CONTRÔLE SYSTÈME ===
    def screenshot(self, filename="screenshot.png"):
        """Capture d'écran"""
        pyautogui.screenshot(filename)
        return f"Capture sauvegardée: {filename}"
    
    def lock_screen(self):
        """Verrouille l'écran"""
        if self.system == "Windows":
            ctypes.windll.user32.LockWorkStation()
        elif self.system == "Linux":
            os.system("gnome-screensaver-command -l || loginctl lock-session")
        return "Écran verrouillé"
    
    def shutdown(self):
        """Arrête l'ordinateur"""
        if self.system == "Windows":
            os.system("shutdown /s /t 60")
        elif self.system == "Linux":
            os.system("shutdown -h +1")
        return "Arrêt programmé dans 60s"
    
    def restart(self):
        """Redémarre l'ordinateur"""
        if self.system == "Windows":
            os.system("shutdown /r /t 60")
        elif self.system == "Linux":
            os.system("shutdown -r +1")
        return "Redémarrage programmé dans 60s"
    
    def sleep(self):
        """Met en veille"""
        if self.system == "Windows":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        elif self.system == "Linux":
            os.system("systemctl suspend")
        return "Mise en veille"
    
    def open_app(self, app_name):
        """Ouvre une application"""
        try:
            if self.system == "Windows":
                os.system(f"start {app_name}")
            elif self.system == "Linux":
                os.system(f"{app_name} &")
            return f"Application {app_name} ouverte"
        except:
            return f"Impossible d'ouvrir {app_name}"
    
    def open_url(self, url):
        """Ouvre une URL"""
        import webbrowser
        webbrowser.open(url)
        return f"URL ouverte: {url}"
    
    # === CONTRÔLE MÉDIA ===
    def media_play_pause(self):
        """Lecture/Pause"""
        pyautogui.press('playpause')
        return "Lecture/Pause"
    
    def media_next(self):
        """Piste suivante"""
        pyautogui.press('nexttrack')
        return "Piste suivante"
    
    def media_previous(self):
        """Piste précédente"""
        pyautogui.press('prevtrack')
        return "Piste précédente"
    
    def media_stop(self):
        """Arrêt"""
        pyautogui.press('stop')
        return "Lecture arrêtée"
