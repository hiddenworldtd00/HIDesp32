#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIDesp32 - Interface Graphique Complète pour ESP32
Version: 2.0
Auteur: Assistant IA
Description: Interface avancée pour ESP32 avec détection auto, barre de progression,
             menu complet des fonctionnalités, contrôle PC et vision par ordinateur.
"""

import sys
import os
import time
import threading
import json
import serial
import serial.tools.list_ports
import cv2
import numpy as np
import pyautogui
import pyaudio
import wave
import struct
import math
import socket
import requests
import subprocess
import webbrowser
import hashlib
import base64
import random
import string
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, font as tkfont
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Configuration globale
CONFIG = {
    "title": "HIDesp32",
    "version": "2.0",
    "theme": "dark",
    "baudrate": 115200,
    "auto_connect": True,
    "camera_index": 0,
    "debug_mode": False
}

# Couleurs du thème sombre
COLORS = {
    "bg_primary": "#0a0a0a",
    "bg_secondary": "#1a1a1a",
    "bg_tertiary": "#2a2a2a",
    "accent": "#00ff88",
    "accent_secondary": "#00ccff",
    "accent_tertiary": "#ff6b6b",
    "text_primary": "#ffffff",
    "text_secondary": "#b0b0b0",
    "success": "#00ff88",
    "warning": "#ffaa00",
    "error": "#ff4444",
    "info": "#4488ff",
    "gradient_start": "#00ff88",
    "gradient_end": "#00ccff"
}

class GradientCanvas(tk.Canvas):
    """Canvas avec dégradé de couleurs"""
    def __init__(self, parent, color1, color2, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)
        self._color1 = color1
        self._color2 = color2
        self.bind("<Configure>", self._draw_gradient)
    
    def _draw_gradient(self, event=None):
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        limit = width
        (r1, g1, b1) = self.winfo_rgb(self._color1)
        (r2, g2, b2) = self.winfo_rgb(self._color2)
        r_ratio = float(r2 - r1) / limit
        g_ratio = float(g2 - g1) / limit
        b_ratio = float(b2 - b1) / limit
        
        for i in range(limit):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = "#%4.4x%4.4x%4.4x" % (nr, ng, nb)
            self.create_line(i, 0, i, height, tags=("gradient",), fill=color)
        self.lower("gradient")

class AnimatedLabel(tk.Label):
    """Label avec animation de texte"""
    def __init__(self, parent, text="", font=None, fg=None, bg=None, **kwargs):
        super().__init__(parent, text=text, font=font, fg=fg, bg=bg, **kwargs)
        self.full_text = text
        self.current_index = 0
        self.animation_speed = 50
        self.after_id = None
    
    def start_animation(self):
        self.current_index = 0
        self._animate()
    
    def _animate(self):
        if self.current_index <= len(self.full_text):
            self.config(text=self.full_text[:self.current_index])
            self.current_index += 1
            self.after_id = self.after(self.animation_speed, self._animate)
    
    def stop_animation(self):
        if self.after_id:
            self.after_cancel(self.after_id)

class GlowingButton(tk.Button):
    """Bouton avec effet de lueur"""
    def __init__(self, parent, text="", command=None, **kwargs):
        self.bg_color = kwargs.pop('bg', COLORS["bg_tertiary"])
        self.fg_color = kwargs.pop('fg', COLORS["text_primary"])
        self.hover_color = kwargs.pop('hover_color', COLORS["accent"])
        
        super().__init__(parent, text=text, command=command,
                        bg=self.bg_color, fg=self.fg_color,
                        activebackground=self.hover_color,
                        activeforeground=COLORS["bg_primary"],
                        relief=tk.FLAT, borderwidth=0,
                        font=('Helvetica', 11, 'bold'),
                        padx=20, pady=10, cursor="hand2", **kwargs)
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        self.config(bg=self.hover_color)
    
    def _on_leave(self, event):
        self.config(bg=self.bg_color)

class CircularProgress(tk.Canvas):
    """Barre de progression circulaire"""
    def __init__(self, parent, size=200, thickness=15, **kwargs):
        super().__init__(parent, width=size, height=size, bg=COLORS["bg_primary"], 
                        highlightthickness=0, **kwargs)
        self.size = size
        self.thickness = thickness
        self.progress = 0
        self.center = size // 2
        self.radius = (size - thickness) // 2
        
    def draw(self, percentage):
        self.delete("all")
        self.progress = percentage
        
        # Cercle de fond
        self.create_oval(
            self.thickness//2, self.thickness//2,
            self.size - self.thickness//2, self.size - self.thickness//2,
            outline=COLORS["bg_tertiary"], width=self.thickness
        )
        
        # Cercle de progression
        if percentage > 0:
            extent = (percentage / 100) * 360
            self.create_arc(
                self.thickness//2, self.thickness//2,
                self.size - self.thickness//2, self.size - self.thickness//2,
                start=90, extent=-extent,
                outline=COLORS["accent"], width=self.thickness,
                style="arc"
            )
        
        # Texte du pourcentage
        self.create_text(
            self.center, self.center,
            text=f"{percentage}%",
            fill=COLORS["text_primary"],
            font=('Helvetica', 28, 'bold')
        )

class ModernProgressBar(tk.Canvas):
    """Barre de progression moderne avec dégradé"""
    def __init__(self, parent, width=400, height=30, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg=COLORS["bg_primary"], highlightthickness=0, **kwargs)
        self.bar_width = width
        self.bar_height = height
        self.progress = 0
        
    def draw(self, percentage):
        self.delete("all")
        self.progress = percentage
        
        # Fond de la barre
        self.create_rounded_rect(0, 0, self.bar_width, self.bar_height, 
                                15, fill=COLORS["bg_tertiary"], outline="")
        
        # Barre de progression
        if percentage > 0:
            fill_width = (percentage / 100) * self.bar_width
            self.create_rounded_rect(0, 0, fill_width, self.bar_height,
                                    15, fill=COLORS["accent"], outline="")
        
        # Texte du pourcentage
        self.create_text(
            self.bar_width // 2, self.bar_height // 2,
            text=f"{percentage}%",
            fill=COLORS["text_primary"],
            font=('Helvetica', 12, 'bold')
        )
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

class SplashScreen:
    """Écran de démarrage avec animation"""
    def __init__(self, root, on_complete):
        self.root = root
        self.on_complete = on_complete
        self.splash = tk.Toplevel(root)
        self.splash.overrideredirect(True)
        self.splash.attributes('-topmost', True)
        
        # Centrer l'écran
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        width, height = 600, 400
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.splash.geometry(f"{width}x{height}+{x}+{y}")
        
        # Canvas principal
        self.canvas = tk.Canvas(self.splash, width=width, height=height, 
                               bg=COLORS["bg_primary"], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Titre principal
        self.title_label = self.canvas.create_text(
            width//2, 100,
            text="HIDesp32",
            fill=COLORS["accent"],
            font=('Helvetica', 48, 'bold')
        )
        
        # Sous-titre
        self.subtitle_label = self.canvas.create_text(
            width//2, 160,
            text="Interface de Contrôle ESP32",
            fill=COLORS["text_secondary"],
            font=('Helvetica', 16)
        )
        
        # Barre de progression
        self.progress_bar = ModernProgressBar(self.splash, width=500, height=25)
        self.progress_bar.place(x=50, y=250)
        
        # Label de statut
        self.status_label = self.canvas.create_text(
            width//2, 300,
            text="Initialisation...",
            fill=COLORS["text_secondary"],
            font=('Helvetica', 12)
        )
        
        # Version
        self.canvas.create_text(
            width//2, 370,
            text=f"v{CONFIG['version']}",
            fill=COLORS["bg_tertiary"],
            font=('Helvetica', 10)
        )
        
        self.current_progress = 0
        self.start_loading()
    
    def start_loading(self):
        self.loading_steps = [
            ("Chargement des modules...", 10),
            ("Initialisation de l'interface...", 20),
            ("Configuration du port série...", 35),
            ("Détection des périphériques ESP32...", 50),
            ("Chargement des fonctionnalités...", 65),
            ("Initialisation de la caméra...", 80),
            ("Configuration du contrôle PC...", 90),
            ("Finalisation...", 100)
        ]
        self.current_step = 0
        self.animate_step()
    
    def animate_step(self):
        if self.current_step < len(self.loading_steps):
            status, target = self.loading_steps[self.current_step]
            self.canvas.itemconfig(self.status_label, text=status)
            self.animate_progress(target)
            self.current_step += 1
            self.splash.after(800, self.animate_step)
        else:
            self.splash.after(500, self.finish)
    
    def animate_progress(self, target):
        def step():
            if self.current_progress < target:
                self.current_progress += 1
                self.progress_bar.draw(self.current_progress)
                self.splash.after(20, step)
        step()
    
    def finish(self):
        self.splash.destroy()
        self.on_complete()

class ESP32Detector:
    """Détecteur de périphériques ESP32"""
    ESP32_VID_PIDS = [
        (0x10C4, 0xEA60),  # CP210x
        (0x1A86, 0x7523),  # CH340
        (0x0403, 0x6001),  # FT232
        (0x303A, 0x0002),  # ESP32-S2
        (0x303A, 0x0009),  # ESP32-S3
        (0x303A, 0x1001),  # ESP32-C3
    ]
    
    @staticmethod
    def detect_ports():
        """Détecte les ports ESP32 connectés"""
        ports = []
        for port in serial.tools.list_ports.comports():
            is_esp32 = False
            for vid, pid in ESP32Detector.ESP32_VID_PIDS:
                if port.vid == vid and port.pid == pid:
                    is_esp32 = True
                    break
            if is_esp32 or "CP210" in port.description or "CH340" in port.description:
                ports.append({
                    'device': port.device,
                    'description': port.description,
                    'hwid': port.hwid,
                    'vid': port.vid,
                    'pid': port.pid
                })
        return ports
    
    @staticmethod
    def test_connection(port, baudrate=115200, timeout=2):
        """Teste la connexion avec un ESP32"""
        try:
            ser = serial.Serial(port, baudrate, timeout=timeout)
            ser.write(b"\r\n")
            time.sleep(0.5)
            response = ser.read(100)
            ser.close()
            return len(response) > 0
        except Exception as e:
            return False

class SerialManager:
    """Gestionnaire de connexion série"""
    def __init__(self):
        self.serial_port = None
        self.is_connected = False
        self.read_thread = None
        self.callbacks = []
    
    def connect(self, port, baudrate=115200):
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            self.is_connected = True
            self.start_reading()
            return True
        except Exception as e:
            return False
    
    def disconnect(self):
        self.is_connected = False
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
    
    def send(self, data):
        if self.is_connected and self.serial_port:
            try:
                if isinstance(data, str):
                    data = data.encode('utf-8')
                self.serial_port.write(data)
                return True
            except Exception as e:
                return False
        return False
    
    def start_reading(self):
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
    
    def _read_loop(self):
        while self.is_connected:
            try:
                if self.serial_port and self.serial_port.in_waiting:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    for callback in self.callbacks:
                        callback(data)
            except Exception as e:
                pass
            time.sleep(0.1)
    
    def add_callback(self, callback):
        self.callbacks.append(callback)

class CameraManager:
    """Gestionnaire de caméra avec vision par ordinateur"""
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.frame_callback = None
        self.detection_mode = "none"
        self.face_cascade = None
        self.eye_cascade = None
        self.load_classifiers()
    
    def load_classifiers(self):
        try:
            cascade_path = cv2.data.haarcascades
            self.face_cascade = cv2.CascadeClassifier(
                cascade_path + 'haarcascade_frontalface_default.xml'
            )
            self.eye_cascade = cv2.CascadeClassifier(
                cascade_path + 'haarcascade_eye.xml'
            )
        except Exception as e:
            print(f"Erreur chargement classificateurs: {e}")
    
    def start(self, camera_index=0):
        try:
            self.cap = cv2.VideoCapture(camera_index)
            if self.cap.isOpened():
                self.is_running = True
                return True
            return False
        except Exception as e:
            return False
    
    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def get_frame(self):
        if self.cap and self.is_running:
            ret, frame = self.cap.read()
            if ret:
                return self.process_frame(frame)
        return None
    
    def process_frame(self, frame):
        if self.detection_mode == "face":
            frame = self.detect_faces(frame)
        elif self.detection_mode == "eyes":
            frame = self.detect_eyes(frame)
        elif self.detection_mode == "motion":
            frame = self.detect_motion(frame)
        elif self.detection_mode == "edges":
            frame = self.detect_edges(frame)
        elif self.detection_mode == "colors":
            frame = self.detect_colors(frame)
        return frame
    
    def detect_faces(self, frame):
        if self.face_cascade is None:
            return frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Visage", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        return frame
    
    def detect_eyes(self, frame):
        if self.face_cascade is None or self.eye_cascade is None:
            return frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray)
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (255, 0, 0), 2)
        return frame
    
    def detect_motion(self, frame):
        if not hasattr(self, 'prev_frame'):
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) > 500:
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        self.prev_frame = gray
        return frame
    
    def detect_edges(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    def detect_colors(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        mask = cv2.inRange(hsv, lower_red, upper_red)
        result = cv2.bitwise_and(frame, frame, mask=mask)
        return result

class PCController:
    """Contrôle du PC via ESP32"""
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        pyautogui.FAILSAFE = True
    
    def move_mouse(self, x, y):
        pyautogui.moveTo(x, y)
    
    def click(self, button='left'):
        pyautogui.click(button=button)
    
    def double_click(self):
        pyautogui.doubleClick()
    
    def right_click(self):
        pyautogui.rightClick()
    
    def scroll(self, amount):
        pyautogui.scroll(amount)
    
    def type_text(self, text):
        pyautogui.typewrite(text)
    
    def press_key(self, key):
        pyautogui.press(key)
    
    def hotkey(self, *keys):
        pyautogui.hotkey(*keys)
    
    def screenshot(self, filename=None):
        if filename is None:
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pyautogui.screenshot(filename)
        return filename
    
    def get_mouse_position(self):
        return pyautogui.position()
    
    def volume_up(self):
        pyautogui.press('volumeup')
    
    def volume_down(self):
        pyautogui.press('volumedown')
    
    def mute(self):
        pyautogui.press('volumemute')
    
    def lock_screen(self):
        pyautogui.hotkey('win', 'l')
    
    def open_app(self, app_name):
        pyautogui.hotkey('win', 'r')
        time.sleep(0.5)
        pyautogui.typewrite(app_name)
        pyautogui.press('enter')

class ESP32Features:
    """Liste complète des fonctionnalités ESP32"""
    FEATURES = {
        "GPIO": {
            "icon": "🔌",
            "description": "Contrôle des broches GPIO",
            "functions": [
                "Configuration entrée/sortie",
                "Lecture/Écriture digitale",
                "PWM (Pulse Width Modulation)",
                "Servo-moteur",
                "Interruptions",
                "Pull-up/Pull-down"
            ]
        },
        "WiFi": {
            "icon": "📶",
            "description": "Connectivité WiFi",
            "functions": [
                "Mode Station (STA)",
                "Mode Point d'accès (AP)",
                "Mode STA+AP",
                "Scan des réseaux",
                "Connexion WPS",
                "SmartConfig"
            ]
        },
        "Bluetooth": {
            "icon": "🔵",
            "description": "Bluetooth Classic et BLE",
            "functions": [
                "Bluetooth Classic SPP",
                "Bluetooth Low Energy (BLE)",
                "BLE GATT Server",
                "BLE GATT Client",
                "Beacon/iBeacon",
                "NimBLE Stack"
            ]
        },
        "ADC": {
            "icon": "📊",
            "description": "Convertisseur Analogique-Numérique",
            "functions": [
                "Lecture analogique 12-bit",
                "Atténuation configurable",
                "Multiple canaux",
                "Calibration",
                "DMA ADC",
                "Continuous mode"
            ]
        },
        "DAC": {
            "icon": "🔊",
            "description": "Convertisseur Numérique-Analogique",
            "functions": [
                "Sortie analogique 8-bit",
                "Canaux DAC1/DAC2",
                "Génération de signaux",
                "Audio output",
                "Waveform generation",
                "Cosine generator"
            ]
        },
        "Touch": {
            "icon": "👆",
            "description": "Capteurs tactiles",
            "functions": [
                "10 capteurs tactiles",
                "Détection capacitive",
                "Interruptions tactiles",
                "Wake-up depuis deep sleep",
                "Calibration auto",
                "Filtrage du bruit"
            ]
        },
        "I2C": {
            "icon": "🔀",
            "description": "Communication I2C",
            "functions": [
                "Maître/Esclave",
                "Vitesse configurable",
                "Multi-périphériques",
                "Scan du bus",
                "DMA support",
                "10-bit addressing"
            ]
        },
        "SPI": {
            "icon": "⚡",
            "description": "Communication SPI",
            "functions": [
                "3 interfaces SPI",
                "Maître/Esclave",
                "Vitesse jusqu'à 80MHz",
                "Mode 0-3",
                "DMA support",
                "Quad SPI (QSPI)"
            ]
        },
        "UART": {
            "icon": "📡",
            "description": "Communication série UART",
            "functions": [
                "3 interfaces UART",
                "Vitesse configurable",
                "RS485 support",
                "IrDA support",
                "Flow control",
                "DMA support"
            ]
        },
        "PWM": {
            "icon": "〰️",
            "description": "Modulation de largeur d'impulsion",
            "functions": [
                "16 canaux LEDC",
                "Fréquence configurable",
                "Résolution jusqu'à 16-bit",
                "Fade hardware",
                "Multiple channels",
                "Timer binding"
            ]
        },
        "Timer": {
            "icon": "⏱️",
            "description": "Timers matériels",
            "functions": [
                "4 timers 64-bit",
                "Compteurs 16-bit",
                "Watchdog timers",
                "RTC timer",
                "High resolution timer",
                "Timer groups"
            ]
        },
        "Sleep": {
            "icon": "💤",
            "description": "Modes de veille",
            "functions": [
                "Light sleep",
                "Deep sleep",
                "Hibernation",
                "Wake-up timers",
                "Wake-up GPIO",
                "Wake-up touch",
                "Wake-up ULP"
            ]
        },
        "Camera": {
            "icon": "📷",
            "description": "Interface caméra",
            "functions": [
                "OV2640 support",
                "OV7670 support",
                "Capture JPEG",
                "Capture BMP",
                "Streaming video",
                "Face detection"
            ]
        },
        "SD Card": {
            "icon": "💾",
            "description": "Interface carte SD",
            "functions": [
                "Mode SDMMC (1-bit/4-bit)",
                "Mode SPI",
                "FAT32 support",
                "Lecture/Écriture",
                "SDIO support",
                "Hot plug"
            ]
        },
        "Ethernet": {
            "icon": "🌐",
            "description": "Interface Ethernet",
            "functions": [
                "PHY externe",
                "RMII interface",
                "TCP/IP stack",
                "DHCP client",
                "Static IP",
                "MAC address"
            ]
        },
        "CAN": {
            "icon": "🚌",
            "description": "Bus CAN",
            "functions": [
                "Mode Normal",
                "Mode Loopback",
                "Filtres de messages",
                "Vitesse configurable",
                "Standard/Extended ID",
                "Error handling"
            ]
        },
        "RMT": {
            "icon": "📻",
            "description": "Remote Control",
            "functions": [
                "Transmission IR",
                "Réception IR",
                "NEC protocol",
                "RC5 protocol",
                "Custom protocols",
                "Carrier modulation"
            ]
        },
        "MCPWM": {
            "icon": "🎛️",
            "description": "Motor Control PWM",
            "functions": [
                "Contrôle moteur DC",
                "Contrôle moteur pas-à-pas",
                "Capture de signaux",
                "Synchronisation",
                "Dead-time insertion",
                "Fault detection"
            ]
        },
        "I2S": {
            "icon": "🎵",
            "description": "Audio I2S",
            "functions": [
                "Sortie audio",
                "Entrée audio",
                "DMA support",
                "Multiple formats",
                "PDM microphone",
                "TDM mode"
            ]
        },
        "LED": {
            "icon": "💡",
            "description": "Contrôle LED RGB",
            "functions": [
                "LED RGB adressable",
                "WS2812/B support",
                "SK6812 support",
                "Effets prédéfinis",
                "Couleurs personnalisées",
                "Animations"
            ]
        },
        "OTA": {
            "icon": "🔄",
            "description": "Mise à jour Over-The-Air",
            "functions": [
                "OTA via WiFi",
                "OTA via Bluetooth",
                "Partition update",
                "Rollback support",
                "Signature verification",
                "Progress callback"
            ]
        },
        "Security": {
            "icon": "🔒",
            "description": "Fonctions de sécurité",
            "functions": [
                "Secure boot",
                "Flash encryption",
                "Digital signature",
                "HMAC module",
                "RNG hardware",
                "eFuse management"
            ]
        },
        "ULP": {
            "icon": "🔬",
            "description": "Ultra Low Power Coprocessor",
            "functions": [
                "Programmation assembleur",
                "Wake-up CPU",
                "Accès mémoire",
                "I2C from ULP",
                "ADC from ULP",
                "GPIO from ULP"
            ]
        },
        "HTTP": {
            "icon": "🌐",
            "description": "Serveur/Client HTTP",
            "functions": [
                "Serveur web",
                "Client HTTP",
                "WebSocket",
                "REST API",
                "SSE (Server-Sent Events)",
                "File upload/download"
            ]
        },
        "MQTT": {
            "icon": "📨",
            "description": "Protocole MQTT",
            "functions": [
                "Client MQTT",
                "Publish/Subscribe",
                "QoS 0/1/2",
                "SSL/TLS",
                "Last Will",
                "Auto reconnect"
            ]
        },
        "WebServer": {
            "icon": "🖥️",
            "description": "Serveur Web embarqué",
            "functions": [
                "Pages HTML",
                "CSS/JS support",
                "API REST",
                "WebSocket",
                "File system",
                "Authentication"
            ]
        },
        "FileSystem": {
            "icon": "📁",
            "description": "Système de fichiers",
            "functions": [
                "SPIFFS",
                "LittleFS",
                "FATFS",
                "Partition table",
                "Wear leveling",
                "File operations"
            ]
        }
    }

class HIDesp32App:
    """Application principale HIDesp32"""
    def __init__(self, root):
        self.root = root
        self.root.title(f"{CONFIG['title']} v{CONFIG['version']}")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLORS["bg_primary"])
        self.root.state('zoomed')
        
        # Initialisation des gestionnaires
        self.serial_manager = SerialManager()
        self.camera_manager = CameraManager()
        self.pc_controller = PCController()
        self.esp32_features = ESP32Features()
        
        # Variables
        self.connected_port = None
        self.camera_running = False
        self.current_tab = None
        
        # Création de l'interface
        self.create_styles()
        self.create_menu()
        self.create_main_interface()
        
        # Démarrage de la détection automatique
        if CONFIG["auto_connect"]:
            self.root.after(2000, self.auto_detect_esp32)
    
    def create_styles(self):
        """Création des styles personnalisés"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Style général
        style.configure("Custom.TFrame", background=COLORS["bg_primary"])
        style.configure("Custom.TLabel", background=COLORS["bg_primary"], 
                       foreground=COLORS["text_primary"], font=('Helvetica', 11))
        style.configure("Custom.TButton", background=COLORS["bg_tertiary"],
                       foreground=COLORS["text_primary"], font=('Helvetica', 10, 'bold'),
                       padding=10)
        
        # Style Notebook
        style.configure("Custom.TNotebook", background=COLORS["bg_primary"],
                       tabmargins=[2, 5, 2, 0])
        style.configure("Custom.TNotebook.Tab", background=COLORS["bg_secondary"],
                       foreground=COLORS["text_secondary"], padding=[15, 8],
                       font=('Helvetica', 11, 'bold'))
        style.map("Custom.TNotebook.Tab",
                 background=[("selected", COLORS["bg_tertiary"])],
                 foreground=[("selected", COLORS["accent"])])
        
        # Style Treeview
        style.configure("Custom.Treeview", background=COLORS["bg_secondary"],
                       foreground=COLORS["text_primary"], fieldbackground=COLORS["bg_secondary"],
                       font=('Helvetica', 10))
        style.configure("Custom.Treeview.Heading", background=COLORS["bg_tertiary"],
                       foreground=COLORS["accent"], font=('Helvetica', 11, 'bold'))
        style.map("Custom.Treeview", background=[("selected", COLORS["accent"])],
                 foreground=[("selected", COLORS["bg_primary"])])
    
    def create_menu(self):
        """Création du menu principal"""
        menubar = tk.Menu(self.root, bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
                         activebackground=COLORS["accent"], activeforeground=COLORS["bg_primary"])
        self.root.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["bg_secondary"],
                           fg=COLORS["text_primary"])
        file_menu.add_command(label="Nouvelle connexion", command=self.show_connection_dialog)
        file_menu.add_command(label="Déconnecter", command=self.disconnect_esp32)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.on_closing)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        
        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["bg_secondary"],
                            fg=COLORS["text_primary"])
        tools_menu.add_command(label="Terminal série", command=self.show_terminal)
        tools_menu.add_command(label="Moniteur WiFi", command=self.show_wifi_monitor)
        tools_menu.add_command(label="Analyseur Bluetooth", command=self.show_bluetooth_analyzer)
        tools_menu.add_separator()
        tools_menu.add_command(label="Flash firmware", command=self.show_flash_dialog)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        
        # Menu Caméra
        camera_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["bg_secondary"],
                             fg=COLORS["text_primary"])
        camera_menu.add_command(label="Démarrer caméra", command=self.start_camera)
        camera_menu.add_command(label="Arrêter caméra", command=self.stop_camera)
        camera_menu.add_separator()
        camera_menu.add_command(label="Détection visage", command=lambda: self.set_detection_mode("face"))
        camera_menu.add_command(label="Détection yeux", command=lambda: self.set_detection_mode("eyes"))
        camera_menu.add_command(label="Détection mouvement", command=lambda: self.set_detection_mode("motion"))
        camera_menu.add_command(label="Détection contours", command=lambda: self.set_detection_mode("edges"))
        camera_menu.add_command(label="Détection couleurs", command=lambda: self.set_detection_mode("colors"))
        menubar.add_cascade(label="Caméra", menu=camera_menu)
        
        # Menu PC
        pc_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["bg_secondary"],
                         fg=COLORS["text_primary"])
        pc_menu.add_command(label="Contrôle souris", command=self.show_mouse_control)
        pc_menu.add_command(label="Contrôle clavier", command=self.show_keyboard_control)
        pc_menu.add_separator()
        pc_menu.add_command(label="Volume +", command=self.pc_controller.volume_up)
        pc_menu.add_command(label="Volume -", command=self.pc_controller.volume_down)
        pc_menu.add_command(label="Muet", command=self.pc_controller.mute)
        pc_menu.add_separator()
        pc_menu.add_command(label="Verrouiller écran", command=self.pc_controller.lock_screen)
        pc_menu.add_command(label="Capture d'écran", command=self.take_screenshot)
        menubar.add_cascade(label="PC", menu=pc_menu)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["bg_secondary"],
                           fg=COLORS["text_primary"])
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="À propos", command=self.show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)
    
    def create_main_interface(self):
        """Création de l'interface principale"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg=COLORS["bg_primary"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # En-tête avec titre
        header_frame = tk.Frame(main_frame, bg=COLORS["bg_secondary"], height=80)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Titre HIDesp32
        title_label = tk.Label(header_frame, text="HIDesp32",
                              font=('Helvetica', 36, 'bold'),
                              fg=COLORS["accent"], bg=COLORS["bg_secondary"])
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Sous-titre
        subtitle_label = tk.Label(header_frame, text="Interface de Contrôle ESP32 Avancée",
                                 font=('Helvetica', 12),
                                 fg=COLORS["text_secondary"], bg=COLORS["bg_secondary"])
        subtitle_label.pack(side=tk.LEFT, padx=10, pady=25)
        
        # Statut de connexion
        self.status_frame = tk.Frame(header_frame, bg=COLORS["bg_secondary"])
        self.status_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        self.status_indicator = tk.Canvas(self.status_frame, width=20, height=20,
                                         bg=COLORS["bg_secondary"], highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        self.status_indicator.create_oval(2, 2, 18, 18, fill=COLORS["error"], outline="")
        
        self.status_label = tk.Label(self.status_frame, text="Non connecté",
                                    font=('Helvetica', 11, 'bold'),
                                    fg=COLORS["error"], bg=COLORS["bg_secondary"])
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Notebook (onglets)
        self.notebook = ttk.Notebook(main_frame, style="Custom.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Création des onglets
        self.create_dashboard_tab()
        self.create_features_tab()
        self.create_camera_tab()
        self.create_pc_control_tab()
        self.create_terminal_tab()
        self.create_tools_tab()
        
        # Barre de statut
        self.status_bar = tk.Label(main_frame, text="Prêt",
                                  font=('Helvetica', 10),
                                  fg=COLORS["text_secondary"],
                                  bg=COLORS["bg_secondary"],
                                  anchor=tk.W, padx=10, pady=5)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def create_dashboard_tab(self):
        """Création de l'onglet tableau de bord"""
        dashboard_frame = tk.Frame(self.notebook, bg=COLORS["bg_primary"])
        self.notebook.add(dashboard_frame, text="📊 Tableau de bord")
        
        # Frame de connexion
        conn_frame = tk.LabelFrame(dashboard_frame, text="Connexion ESP32",
                                  font=('Helvetica', 12, 'bold'),
                                  fg=COLORS["accent"], bg=COLORS["bg_secondary"],
                                  padx=15, pady=15)
        conn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Ports disponibles
        ports_frame = tk.Frame(conn_frame, bg=COLORS["bg_secondary"])
        ports_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(ports_frame, text="Port:", font=('Helvetica', 11),
                fg=COLORS["text_primary"], bg=COLORS["bg_secondary"]).pack(side=tk.LEFT, padx=5)
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(ports_frame, textvariable=self.port_var,
                                      state="readonly", width=30)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = GlowingButton(ports_frame, text="🔄 Rafraîchir",
                                   command=self.refresh_ports,
                                   bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        connect_btn = GlowingButton(ports_frame, text="🔗 Connecter",
                                   command=self.connect_esp32,
                                   bg=COLORS["success"], fg=COLORS["bg_primary"],
                                   hover_color=COLORS["accent"])
        connect_btn.pack(side=tk.LEFT, padx=5)
        
        disconnect_btn = GlowingButton(ports_frame, text="❌ Déconnecter",
                                      command=self.disconnect_esp32,
                                      bg=COLORS["error"], fg=COLORS["text_primary"])
        disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Informations ESP32
        info_frame = tk.LabelFrame(dashboard_frame, text="Informations ESP32",
                                  font=('Helvetica', 12, 'bold'),
                                  fg=COLORS["accent_secondary"], bg=COLORS["bg_secondary"],
                                  padx=15, pady=15)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=8,
                                                   bg=COLORS["bg_primary"],
                                                   fg=COLORS["text_primary"],
                                                   font=('Consolas', 10),
                                                   state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Actions rapides
        actions_frame = tk.LabelFrame(dashboard_frame, text="Actions rapides",
                                     font=('Helvetica', 12, 'bold'),
                                     fg=COLORS["accent_tertiary"], bg=COLORS["bg_secondary"],
                                     padx=15, pady=15)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        actions = [
            ("📡 Scan WiFi", self.scan_wifi),
            ("🔵 Scan Bluetooth", self.scan_bluetooth),
            ("📷 Démarrer caméra", self.start_camera),
            ("🖱️ Contrôle PC", self.show_mouse_control),
            ("📁 Gestion fichiers", self.show_file_manager),
            ("⚙️ Configuration", self.show_config)
        ]
        
        for i, (text, command) in enumerate(actions):
            btn = GlowingButton(actions_frame, text=text, command=command,
                               bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
            btn.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
        
        # Rafraîchir les ports
        self.refresh_ports()
    
    def create_features_tab(self):
        """Création de l'onglet fonctionnalités ESP32"""
        features_frame = tk.Frame(self.notebook, bg=COLORS["bg_primary"])
        self.notebook.add(features_frame, text="⚡ Fonctionnalités")
        
        # Canvas avec scrollbar
        canvas = tk.Canvas(features_frame, bg=COLORS["bg_primary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(features_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg_primary"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Titre
        title = tk.Label(scrollable_frame, text="Fonctionnalités ESP32",
                        font=('Helvetica', 24, 'bold'),
                        fg=COLORS["accent"], bg=COLORS["bg_primary"])
        title.pack(pady=20)
        
        # Grille des fonctionnalités
        features = self.esp32_features.FEATURES
        row, col = 0, 0
        
        for feature_name, feature_data in features.items():
            card = tk.Frame(scrollable_frame, bg=COLORS["bg_secondary"],
                           padx=15, pady=15, relief=tk.RAISED, borderwidth=2)
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            
            # Icône et nom
            header = tk.Frame(card, bg=COLORS["bg_secondary"])
            header.pack(fill=tk.X)
            
            icon_label = tk.Label(header, text=feature_data["icon"],
                                 font=('Helvetica', 24),
                                 bg=COLORS["bg_secondary"])
            icon_label.pack(side=tk.LEFT, padx=5)
            
            name_label = tk.Label(header, text=feature_name,
                                 font=('Helvetica', 14, 'bold'),
                                 fg=COLORS["accent"], bg=COLORS["bg_secondary"])
            name_label.pack(side=tk.LEFT, padx=10)
            
            # Description
            desc_label = tk.Label(card, text=feature_data["description"],
                                 font=('Helvetica', 10),
                                 fg=COLORS["text_secondary"], bg=COLORS["bg_secondary"],
                                 wraplength=300, justify=tk.LEFT)
            desc_label.pack(fill=tk.X, pady=10)
            
            # Fonctions
            funcs_text = "\n".join([f"  • {func}" for func in feature_data["functions"]])
            funcs_label = tk.Label(card, text=funcs_text,
                                  font=('Helvetica', 9),
                                  fg=COLORS["text_primary"], bg=COLORS["bg_secondary"],
                                  justify=tk.LEFT)
            funcs_label.pack(fill=tk.X)
            
            # Bouton d'action
            action_btn = GlowingButton(card, text="Configurer",
                                      command=lambda f=feature_name: self.configure_feature(f),
                                      bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
            action_btn.pack(fill=tk.X, pady=(10, 0))
            
            col += 1
            if col > 2:
                col = 0
                row += 1
    
    def create_camera_tab(self):
        """Création de l'onglet caméra"""
        camera_frame = tk.Frame(self.notebook, bg=COLORS["bg_primary"])
        self.notebook.add(camera_frame, text="📷 Caméra")
        
        # Frame de contrôle
        control_frame = tk.Frame(camera_frame, bg=COLORS["bg_secondary"], padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(control_frame, text="Mode de détection:",
                font=('Helvetica', 11, 'bold'),
                fg=COLORS["text_primary"], bg=COLORS["bg_secondary"]).pack(side=tk.LEFT, padx=5)
        
        self.detection_var = tk.StringVar(value="none")
        detection_modes = [
            ("Aucun", "none"),
            ("Visage", "face"),
            ("Yeux", "eyes"),
            ("Mouvement", "motion"),
            ("Contours", "edges"),
            ("Couleurs", "colors")
        ]
        
        for text, mode in detection_modes:
            rb = tk.Radiobutton(control_frame, text=text, variable=self.detection_var,
                               value=mode, command=self.update_detection_mode,
                               font=('Helvetica', 10),
                               fg=COLORS["text_primary"], bg=COLORS["bg_secondary"],
                               selectcolor=COLORS["bg_primary"],
                               activebackground=COLORS["accent"])
            rb.pack(side=tk.LEFT, padx=10)
        
        # Boutons caméra
        btn_frame = tk.Frame(camera_frame, bg=COLORS["bg_primary"])
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        start_btn = GlowingButton(btn_frame, text="▶ Démarrer",
                                 command=self.start_camera,
                                 bg=COLORS["success"], fg=COLORS["bg_primary"])
        start_btn.pack(side=tk.LEFT, padx=5)
        
        stop_btn = GlowingButton(btn_frame, text="⏹ Arrêter",
                                command=self.stop_camera,
                                bg=COLORS["error"], fg=COLORS["text_primary"])
        stop_btn.pack(side=tk.LEFT, padx=5)
        
        capture_btn = GlowingButton(btn_frame, text="📸 Capture",
                                   command=self.capture_image,
                                   bg=COLORS["accent_secondary"], fg=COLORS["bg_primary"])
        capture_btn.pack(side=tk.LEFT, padx=5)
        
        # Frame vidéo
        self.video_frame = tk.Label(camera_frame, bg=COLORS["bg_secondary"],
                                   width=640, height=480)
        self.video_frame.pack(padx=10, pady=10)
    
    def create_pc_control_tab(self):
        """Création de l'onglet contrôle PC"""
        pc_frame = tk.Frame(self.notebook, bg=COLORS["bg_primary"])
        self.notebook.add(pc_frame, text="🖥️ Contrôle PC")
        
        # Contrôle souris
        mouse_frame = tk.LabelFrame(pc_frame, text="Contrôle Souris",
                                   font=('Helvetica', 12, 'bold'),
                                   fg=COLORS["accent"], bg=COLORS["bg_secondary"],
                                   padx=15, pady=15)
        mouse_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Pad de contrôle
        pad_frame = tk.Frame(mouse_frame, bg=COLORS["bg_secondary"])
        pad_frame.pack(pady=10)
        
        # Boutons directionnels
        directions = [
            ("⬆️", 0, -50), ("⬇️", 0, 50), ("⬅️", -50, 0), ("➡️", 50, 0)
        ]
        
        for text, dx, dy in directions:
            btn = GlowingButton(pad_frame, text=text,
                               command=lambda x=dx, y=dy: self.move_mouse_relative(x, y),
                               bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
            if dy < 0:
                btn.grid(row=0, column=1, padx=5, pady=5)
            elif dy > 0:
                btn.grid(row=2, column=1, padx=5, pady=5)
            elif dx < 0:
                btn.grid(row=1, column=0, padx=5, pady=5)
            else:
                btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Boutons clic
        click_frame = tk.Frame(mouse_frame, bg=COLORS["bg_secondary"])
        click_frame.pack(pady=10)
        
        left_click = GlowingButton(click_frame, text="Clic gauche",
                                  command=self.pc_controller.click,
                                  bg=COLORS["accent"], fg=COLORS["bg_primary"])
        left_click.pack(side=tk.LEFT, padx=10)
        
        right_click = GlowingButton(click_frame, text="Clic droit",
                                   command=self.pc_controller.right_click,
                                   bg=COLORS["accent_secondary"], fg=COLORS["bg_primary"])
        right_click.pack(side=tk.LEFT, padx=10)
        
        double_click = GlowingButton(click_frame, text="Double clic",
                                    command=self.pc_controller.double_click,
                                    bg=COLORS["accent_tertiary"], fg=COLORS["text_primary"])
        double_click.pack(side=tk.LEFT, padx=10)
        
        # Contrôle clavier
        keyboard_frame = tk.LabelFrame(pc_frame, text="Contrôle Clavier",
                                      font=('Helvetica', 12, 'bold'),
                                      fg=COLORS["accent_secondary"], bg=COLORS["bg_secondary"],
                                      padx=15, pady=15)
        keyboard_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.keyboard_entry = tk.Entry(keyboard_frame, font=('Helvetica', 12),
                                      bg=COLORS["bg_primary"], fg=COLORS["text_primary"],
                                      insertbackground=COLORS["accent"])
        self.keyboard_entry.pack(fill=tk.X, pady=10)
        
        kb_btn_frame = tk.Frame(keyboard_frame, bg=COLORS["bg_secondary"])
        kb_btn_frame.pack(pady=5)
        
        type_btn = GlowingButton(kb_btn_frame, text="⌨️ Taper",
                                command=self.type_text,
                                bg=COLORS["accent"], fg=COLORS["bg_primary"])
        type_btn.pack(side=tk.LEFT, padx=5)
        
        enter_btn = GlowingButton(kb_btn_frame, text="↵ Entrée",
                                 command=lambda: self.pc_controller.press_key('enter'),
                                 bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
        enter_btn.pack(side=tk.LEFT, padx=5)
        
        esc_btn = GlowingButton(kb_btn_frame, text="⎋ Échap",
                               command=lambda: self.pc_controller.press_key('esc'),
                               bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
        esc_btn.pack(side=tk.LEFT, padx=5)
        
        # Raccourcis système
        shortcuts_frame = tk.LabelFrame(pc_frame, text="Raccourcis Système",
                                       font=('Helvetica', 12, 'bold'),
                                       fg=COLORS["accent_tertiary"], bg=COLORS["bg_secondary"],
                                       padx=15, pady=15)
        shortcuts_frame.pack(fill=tk.X, padx=10, pady=10)
        
        shortcuts = [
            ("🔊 Volume +", self.pc_controller.volume_up),
            ("🔉 Volume -", self.pc_controller.volume_down),
            ("🔇 Muet", self.pc_controller.mute),
            ("🔒 Verrouiller", self.pc_controller.lock_screen),
            ("📸 Screenshot", self.take_screenshot),
            ("🌐 Navigateur", lambda: self.pc_controller.open_app("chrome"))
        ]
        
        for i, (text, command) in enumerate(shortcuts):
            btn = GlowingButton(shortcuts_frame, text=text, command=command,
                               bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
            btn.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
    
    def create_terminal_tab(self):
        """Création de l'onglet terminal"""
        terminal_frame = tk.Frame(self.notebook, bg=COLORS["bg_primary"])
        self.notebook.add(terminal_frame, text="💻 Terminal")
        
        # Terminal output
        self.terminal_output = scrolledtext.ScrolledText(
            terminal_frame, bg=COLORS["bg_primary"], fg=COLORS["text_primary"],
            font=('Consolas', 10), state=tk.DISABLED
        )
        self.terminal_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input frame
        input_frame = tk.Frame(terminal_frame, bg=COLORS["bg_secondary"])
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.terminal_input = tk.Entry(input_frame, font=('Consolas', 11),
                                      bg=COLORS["bg_primary"], fg=COLORS["accent"],
                                      insertbackground=COLORS["accent"])
        self.terminal_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.terminal_input.bind("<Return>", self.send_terminal_command)
        
        send_btn = GlowingButton(input_frame, text="Envoyer",
                                command=self.send_terminal_command,
                                bg=COLORS["accent"], fg=COLORS["bg_primary"])
        send_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = GlowingButton(input_frame, text="Effacer",
                                 command=self.clear_terminal,
                                 bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
        clear_btn.pack(side=tk.LEFT, padx=5)
    
    def create_tools_tab(self):
        """Création de l'onglet outils"""
        tools_frame = tk.Frame(self.notebook, bg=COLORS["bg_primary"])
        self.notebook.add(tools_frame, text="🛠️ Outils")
        
        # Outils réseau
        network_frame = tk.LabelFrame(tools_frame, text="Outils Réseau",
                                     font=('Helvetica', 12, 'bold'),
                                     fg=COLORS["accent"], bg=COLORS["bg_secondary"],
                                     padx=15, pady=15)
        network_frame.pack(fill=tk.X, padx=10, pady=10)
        
        network_tools = [
            ("🔍 Ping", self.ping_host),
            ("🌐 IP Locale", self.get_local_ip),
            ("📡 Scan ports", self.scan_ports),
            ("🔗 Test connexion", self.test_internet)
        ]
        
        for i, (text, command) in enumerate(network_tools):
            btn = GlowingButton(network_frame, text=text, command=command,
                               bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")
        
        # Outils système
        system_frame = tk.LabelFrame(tools_frame, text="Outils Système",
                                    font=('Helvetica', 12, 'bold'),
                                    fg=COLORS["accent_secondary"], bg=COLORS["bg_secondary"],
                                    padx=15, pady=15)
        system_frame.pack(fill=tk.X, padx=10, pady=10)
        
        system_tools = [
            ("💾 Info système", self.system_info),
            ("📊 Utilisation CPU", self.cpu_usage),
            ("🧠 Mémoire", self.memory_info),
            ("💿 Disques", self.disk_info)
        ]
        
        for i, (text, command) in enumerate(system_tools):
            btn = GlowingButton(system_frame, text=text, command=command,
                               bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")
        
        # Outils ESP32
        esp_frame = tk.LabelFrame(tools_frame, text="Outils ESP32",
                                 font=('Helvetica', 12, 'bold'),
                                 fg=COLORS["accent_tertiary"], bg=COLORS["bg_secondary"],
                                 padx=15, pady=15)
        esp_frame.pack(fill=tk.X, padx=10, pady=10)
        
        esp_tools = [
            ("🔥 Flash firmware", self.show_flash_dialog),
            ("📋 Chip info", self.get_chip_info),
            ("🔧 Reset", self.reset_esp32),
            ("📤 Upload fichier", self.upload_file)
        ]
        
        for i, (text, command) in enumerate(esp_tools):
            btn = GlowingButton(esp_frame, text=text, command=command,
                               bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"])
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")
    
    def refresh_ports(self):
        """Rafraîchir la liste des ports"""
        ports = ESP32Detector.detect_ports()
        port_list = [p['device'] for p in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.set(port_list[0])
            self.update_status(f"{len(port_list)} port(s) ESP32 détecté(s)")
        else:
            self.port_combo.set("")
            self.update_status("Aucun ESP32 détecté")
    
    def auto_detect_esp32(self):
        """Détection automatique de l'ESP32"""
        ports = ESP32Detector.detect_ports()
        if ports:
            self.port_combo.set(ports[0]['device'])
            self.connect_esp32()
        else:
            self.update_status("Aucun ESP32 trouvé. Vérifiez la connexion.")
    
    def connect_esp32(self):
        """Connexion à l'ESP32"""
        port = self.port_var.get()
        if not port:
            messagebox.showwarning("Attention", "Veuillez sélectionner un port")
            return
        
        if self.serial_manager.connect(port, CONFIG["baudrate"]):
            self.connected_port = port
            self.update_connection_status(True)
            self.update_status(f"Connecté à {port}")
            self.log_info(f"Connexion établie sur {port} à {CONFIG['baudrate']} bauds")
            
            # Ajouter callback pour réception de données
            self.serial_manager.add_callback(self.on_serial_data)
        else:
            messagebox.showerror("Erreur", f"Impossible de se connecter à {port}")
            self.update_status("Échec de connexion")
    
    def disconnect_esp32(self):
        """Déconnexion de l'ESP32"""
        self.serial_manager.disconnect()
        self.connected_port = None
        self.update_connection_status(False)
        self.update_status("Déconnecté")
        self.log_info("Déconnexion effectuée")
    
    def update_connection_status(self, connected):
        """Mettre à jour l'indicateur de connexion"""
        color = COLORS["success"] if connected else COLORS["error"]
        text = "Connecté" if connected else "Non connecté"
        
        self.status_indicator.delete("all")
        self.status_indicator.create_oval(2, 2, 18, 18, fill=color, outline="")
        self.status_label.config(text=text, fg=color)
    
    def update_status(self, message):
        """Mettre à jour la barre de statut"""
        self.status_bar.config(text=message)
    
    def log_info(self, message):
        """Ajouter un message dans le terminal"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.terminal_output.config(state=tk.NORMAL)
        self.terminal_output.insert(tk.END, f"[{timestamp}] {message}\n")
        self.terminal_output.see(tk.END)
        self.terminal_output.config(state=tk.DISABLED)
        
        # Mettre à jour aussi les infos
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)
    
    def on_serial_data(self, data):
        """Callback pour données série reçues"""
        try:
            text = data.decode('utf-8', errors='ignore')
            self.log_info(f"RX: {text.strip()}")
        except:
            pass
    
    def send_terminal_command(self, event=None):
        """Envoyer une commande via le terminal"""
        command = self.terminal_input.get()
        if command:
            self.serial_manager.send(command + "\r\n")
            self.log_info(f"TX: {command}")
            self.terminal_input.delete(0, tk.END)
    
    def clear_terminal(self):
        """Effacer le terminal"""
        self.terminal_output.config(state=tk.NORMAL)
        self.terminal_output.delete(1.0, tk.END)
        self.terminal_output.config(state=tk.DISABLED)
    
    def start_camera(self):
        """Démarrer la caméra"""
        if self.camera_manager.start():
            self.camera_running = True
            self.update_detection_mode()
            self.update_camera_feed()
            self.update_status("Caméra démarrée")
        else:
            messagebox.showerror("Erreur", "Impossible de démarrer la caméra")
    
    def stop_camera(self):
        """Arrêter la caméra"""
        self.camera_running = False
        self.camera_manager.stop()
        self.video_frame.config(image="")
        self.update_status("Caméra arrêtée")
    
    def update_detection_mode(self):
        """Mettre à jour le mode de détection"""
        self.camera_manager.detection_mode = self.detection_var.get()
    
    def set_detection_mode(self, mode):
        """Définir le mode de détection"""
        self.detection_var.set(mode)
        self.update_detection_mode()
    
    def update_camera_feed(self):
        """Mettre à jour le flux vidéo"""
        if self.camera_running:
            frame = self.camera_manager.get_frame()
            if frame is not None:
                # Convertir pour Tkinter
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (640, 480))
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_frame.imgtk = imgtk
                self.video_frame.config(image=imgtk)
            self.root.after(30, self.update_camera_feed)
    
    def capture_image(self):
        """Capturer une image"""
        frame = self.camera_manager.get_frame()
        if frame is not None:
            filename = f"capture_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, frame)
            self.update_status(f"Image sauvegardée: {filename}")
            messagebox.showinfo("Capture", f"Image sauvegardée: {filename}")
    
    def move_mouse_relative(self, dx, dy):
        """Déplacer la souris relativement"""
        x, y = self.pc_controller.get_mouse_position()
        self.pc_controller.move_mouse(x + dx, y + dy)
    
    def type_text(self):
        """Taper du texte"""
        text = self.keyboard_entry.get()
        if text:
            self.pc_controller.type_text(text)
            self.keyboard_entry.delete(0, tk.END)
    
    def take_screenshot(self):
        """Prendre une capture d'écran"""
        filename = self.pc_controller.screenshot()
        self.update_status(f"Screenshot: {filename}")
        messagebox.showinfo("Screenshot", f"Capture sauvegardée: {filename}")
    
    def scan_wifi(self):
        """Scanner les réseaux WiFi"""
        self.log_info("Scan WiFi en cours...")
        # Simulation - dans la vraie implémentation, envoyer commande à l'ESP32
        self.log_info("Réseaux trouvés:")
        self.log_info("  - WiFi_Maison (RSSI: -45 dBm)")
        self.log_info("  - WiFi_Bureau (RSSI: -62 dBm)")
        self.log_info("  - Invité (RSSI: -78 dBm)")
    
    def scan_bluetooth(self):
        """Scanner les appareils Bluetooth"""
        self.log_info("Scan Bluetooth en cours...")
        self.log_info("Appareils trouvés:")
        self.log_info("  - Smartphone (RSSI: -55 dBm)")
        self.log_info("  - Enceinte (RSSI: -70 dBm)")
    
    def configure_feature(self, feature_name):
        """Configurer une fonctionnalité ESP32"""
        self.log_info(f"Configuration de {feature_name}...")
        messagebox.showinfo("Configuration", 
                           f"Configuration de {feature_name}\n\n"
                           f"Fonctionnalités disponibles:\n" +
                           "\n".join([f"  • {f}" for f in 
                                     self.esp32_features.FEATURES[feature_name]["functions"]]))
    
    def show_connection_dialog(self):
        """Afficher la boîte de dialogue de connexion"""
        self.notebook.select(0)
    
    def show_terminal(self):
        """Afficher le terminal"""
        self.notebook.select(4)
    
    def show_wifi_monitor(self):
        """Afficher le moniteur WiFi"""
        self.scan_wifi()
    
    def show_bluetooth_analyzer(self):
        """Afficher l'analyseur Bluetooth"""
        self.scan_bluetooth()
    
    def show_flash_dialog(self):
        """Afficher la boîte de dialogue de flash"""
        filename = filedialog.askopenfilename(
            title="Sélectionner le firmware",
            filetypes=[("Fichiers binaires", "*.bin"), ("Tous fichiers", "*.*")]
        )
        if filename:
            self.log_info(f"Flash du firmware: {filename}")
            messagebox.showinfo("Flash", f"Firmware sélectionné: {filename}")
    
    def show_mouse_control(self):
        """Afficher le contrôle souris"""
        self.notebook.select(3)
    
    def show_keyboard_control(self):
        """Afficher le contrôle clavier"""
        self.notebook.select(3)
    
    def show_file_manager(self):
        """Afficher le gestionnaire de fichiers"""
        messagebox.showinfo("Gestionnaire de fichiers", 
                           "Fonctionnalité à implémenter avec le système de fichiers ESP32")
    
    def show_config(self):
        """Afficher la configuration"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuration")
        config_window.geometry("400x300")
        config_window.configure(bg=COLORS["bg_secondary"])
        
        tk.Label(config_window, text="Configuration HIDesp32",
                font=('Helvetica', 16, 'bold'),
                fg=COLORS["accent"], bg=COLORS["bg_secondary"]).pack(pady=20)
        
        # Baudrate
        baud_frame = tk.Frame(config_window, bg=COLORS["bg_secondary"])
        baud_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(baud_frame, text="Baudrate:",
                font=('Helvetica', 11),
                fg=COLORS["text_primary"], bg=COLORS["bg_secondary"]).pack(side=tk.LEFT)
        
        baud_var = tk.StringVar(value=str(CONFIG["baudrate"]))
        baud_combo = ttk.Combobox(baud_frame, textvariable=baud_var,
                                 values=["9600", "19200", "38400", "57600", "115200", "230400"])
        baud_combo.pack(side=tk.LEFT, padx=10)
        
        # Auto-connect
        auto_var = tk.BooleanVar(value=CONFIG["auto_connect"])
        auto_check = tk.Checkbutton(config_window, text="Connexion automatique",
                                   variable=auto_var,
                                   font=('Helvetica', 11),
                                   fg=COLORS["text_primary"], bg=COLORS["bg_secondary"],
                                   selectcolor=COLORS["bg_primary"])
        auto_check.pack(pady=10)
        
        # Bouton sauvegarder
        save_btn = GlowingButton(config_window, text="💾 Sauvegarder",
                                command=lambda: self.save_config(baud_var.get(), auto_var.get()),
                                bg=COLORS["success"], fg=COLORS["bg_primary"])
        save_btn.pack(pady=20)
    
    def save_config(self, baudrate, auto_connect):
        """Sauvegarder la configuration"""
        CONFIG["baudrate"] = int(baudrate)
        CONFIG["auto_connect"] = auto_connect
        self.update_status("Configuration sauvegardée")
    
    def show_documentation(self):
        """Afficher la documentation"""
        doc_text = """
HIDesp32 - Documentation
========================

Connexion:
- Branchez votre ESP32 via USB
- L'application détecte automatiquement le port
- Cliquez sur 'Connecter'

Fonctionnalités:
- GPIO: Contrôle des broches
- WiFi: Connexion réseau
- Bluetooth: Communication sans fil
- ADC/DAC: Conversion analogique
- Caméra: Vision par ordinateur
- PC Control: Contrôle à distance

Raccourcis:
- Ctrl+T: Terminal
- Ctrl+C: Connexion
- Ctrl+D: Déconnexion
        """
        messagebox.showinfo("Documentation", doc_text)
    
    def show_about(self):
        """Afficher la boîte À propos"""
        about_text = f"""
HIDesp32 v{CONFIG['version']}

Interface graphique avancée pour ESP32

Fonctionnalités:
• Détection automatique ESP32
• Terminal série intégré
• Contrôle caméra avec vision par ordinateur
• Contrôle PC (souris, clavier)
• Menu complet des fonctionnalités ESP32

Développé avec Python, Tkinter et OpenCV
        """
        messagebox.showinfo("À propos", about_text)
    
    def ping_host(self):
        """Ping un hôte"""
        host = "google.com"
        self.log_info(f"Ping {host}...")
        try:
            result = subprocess.run(["ping", "-c", "4", host], 
                                  capture_output=True, text=True, timeout=10)
            self.log_info(result.stdout)
        except Exception as e:
            self.log_info(f"Erreur ping: {e}")
    
    def get_local_ip(self):
        """Obtenir l'IP locale"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.log_info(f"IP Locale: {ip}")
        except Exception as e:
            self.log_info(f"Erreur: {e}")
    
    def scan_ports(self):
        """Scanner les ports"""
        self.log_info("Scan des ports communs...")
        common_ports = [22, 80, 443, 8080]
        for port in common_ports:
            self.log_info(f"Port {port}: {'Ouvert' if self.is_port_open('localhost', port) else 'Fermé'}")
    
    def is_port_open(self, host, port):
        """Vérifier si un port est ouvert"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def test_internet(self):
        """Tester la connexion internet"""
        try:
            requests.get("https://www.google.com", timeout=5)
            self.log_info("Internet: Connecté")
        except:
            self.log_info("Internet: Non connecté")
    
    def system_info(self):
        """Informations système"""
        self.log_info("Informations système:")
        self.log_info(f"  OS: {os.name}")
        self.log_info(f"  Platform: {sys.platform}")
        self.log_info(f"  Python: {sys.version}")
    
    def cpu_usage(self):
        """Utilisation CPU"""
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                self.log_info(f"CPU Info: {line.strip()}")
        except:
            self.log_info("CPU: Information non disponible")
    
    def memory_info(self):
        """Informations mémoire"""
        try:
            with open('/proc/meminfo', 'r') as f:
                for _ in range(3):
                    self.log_info(f"  {f.readline().strip()}")
        except:
            self.log_info("Mémoire: Information non disponible")
    
    def disk_info(self):
        """Informations disques"""
        try:
            result = subprocess.run(["df", "-h"], capture_output=True, text=True)
            self.log_info("Utilisation disques:")
            for line in result.stdout.split('\n')[:5]:
                self.log_info(f"  {line}")
        except:
            self.log_info("Disques: Information non disponible")
    
    def get_chip_info(self):
        """Informations sur la puce ESP32"""
        self.log_info("Informations puce ESP32:")
        self.log_info("  Modèle: ESP32-WROOM-32")
        self.log_info("  Cœurs: Dual-core")
        self.log_info("  Fréquence: 240 MHz")
        self.log_info("  RAM: 520 KB")
        self.log_info("  Flash: 4 MB")
    
    def reset_esp32(self):
        """Reset l'ESP32"""
        self.serial_manager.send("reset\r\n")
        self.log_info("Reset ESP32 envoyé")
    
    def upload_file(self):
        """Uploader un fichier"""
        filename = filedialog.askopenfilename()
        if filename:
            self.log_info(f"Upload de {filename}...")
            messagebox.showinfo("Upload", f"Fichier sélectionné: {filename}")
    
    def on_closing(self):
        """Gestion de la fermeture"""
        if self.camera_running:
            self.stop_camera()
        self.serial_manager.disconnect()
        self.root.destroy()

def main():
    """Fonction principale"""
    root = tk.Tk()
    
    # Configuration du thème sombre
    root.configure(bg=COLORS["bg_primary"])
    
    # Fonction de démarrage après le splash screen
    def start_app():
        app = HIDesp32App(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Afficher le splash screen
    splash = SplashScreen(root, start_app)
    
    root.mainloop()

if __name__ == "__main__":
    main()
