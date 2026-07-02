import cv2
import numpy as np
import threading
import time
from PIL import Image, ImageTk
import tkinter as tk

class FaceDetectionModule:
    def __init__(self, parent_frame, status_callback=None):
        self.parent = parent_frame
        self.status_callback = status_callback
        self.camera = None
        self.running = False
        self.thread = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
        self.current_frame = None
        self.detection_mode = "faces"
        self.face_count = 0
        self.eye_count = 0
        self.smile_count = 0
        self.setup_ui()

    def setup_ui(self):
        # Zone vidéo
        self.video_label = tk.Label(self.parent, bg="black")
        self.video_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Contrôles
        controls = tk.Frame(self.parent, bg="#1a1a2e")
        controls.pack(fill=tk.X, padx=10, pady=5)

        self.btn_start = tk.Button(controls, text="▶ Démarrer Caméra", command=self.start_camera,
                                   bg="#00ff88", fg="black", font=("Consolas", 10, "bold"))
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(controls, text="⏹ Arrêter", command=self.stop_camera,
                                  bg="#ff4444", fg="white", font=("Consolas", 10, "bold"), state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        # Mode de détection
        mode_frame = tk.Frame(controls, bg="#1a1a2e")
        mode_frame.pack(side=tk.LEFT, padx=20)

        tk.Label(mode_frame, text="Mode:", bg="#1a1a2e", fg="white", font=("Consolas", 10)).pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="faces")
        modes = [("Visages", "faces"), ("Yeux", "eyes"), ("Sourires", "smiles"), ("Tout", "all")]
        for text, mode in modes:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=mode,
                          bg="#1a1a2e", fg="white", selectcolor="#16213e",
                          activebackground="#1a1a2e", activeforeground="#00ff88",
                          font=("Consolas", 9), command=self.change_mode).pack(side=tk.LEFT, padx=5)

        # Statistiques
        stats_frame = tk.Frame(self.parent, bg="#16213e")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        self.lbl_faces = tk.Label(stats_frame, text="👤 Visages: 0", bg="#16213e", fg="#00ff88", font=("Consolas", 11, "bold"))
        self.lbl_faces.pack(side=tk.LEFT, padx=10)

        self.lbl_eyes = tk.Label(stats_frame, text="👁 Yeux: 0", bg="#16213e", fg="#00aaff", font=("Consolas", 11, "bold"))
        self.lbl_eyes.pack(side=tk.LEFT, padx=10)

        self.lbl_smiles = tk.Label(stats_frame, text="😊 Sourires: 0", bg="#16213e", fg="#ffaa00", font=("Consolas", 11, "bold"))
        self.lbl_smiles.pack(side=tk.LEFT, padx=10)

        self.lbl_fps = tk.Label(stats_frame, text="FPS: 0", bg="#16213e", fg="#ff00ff", font=("Consolas", 11, "bold"))
        self.lbl_fps.pack(side=tk.RIGHT, padx=10)

        # Options avancées
        adv_frame = tk.LabelFrame(self.parent, text="Options Avancées", bg="#1a1a2e", fg="#00ff88",
                                  font=("Consolas", 10, "bold"))
        adv_frame.pack(fill=tk.X, padx=10, pady=5)

        self.blur_faces = tk.BooleanVar(value=False)
        tk.Checkbutton(adv_frame, text="Flouter les visages", variable=self.blur_faces,
                      bg="#1a1a2e", fg="white", selectcolor="#16213e",
                      activebackground="#1a1a2e", activeforeground="#00ff88",
                      font=("Consolas", 9)).pack(side=tk.LEFT, padx=10)

        self.detect_gender = tk.BooleanVar(value=False)
        tk.Checkbutton(adv_frame, text="Estimer âge/genre", variable=self.detect_gender,
                      bg="#1a1a2e", fg="white", selectcolor="#16213e",
                      activebackground="#1a1a2e", activeforeground="#00ff88",
                      font=("Consolas", 9)).pack(side=tk.LEFT, padx=10)

        self.save_frames = tk.BooleanVar(value=False)
        tk.Checkbutton(adv_frame, text="Sauvegarder captures", variable=self.save_frames,
                      bg="#1a1a2e", fg="white", selectcolor="#16213e",
                      activebackground="#1a1a2e", activeforeground="#00ff88",
                      font=("Consolas", 9)).pack(side=tk.LEFT, padx=10)

        self.btn_capture = tk.Button(adv_frame, text="📸 Capture", command=self.capture_frame,
                                    bg="#0088ff", fg="white", font=("Consolas", 10, "bold"))
        self.btn_capture.pack(side=tk.RIGHT, padx=10)

    def change_mode(self):
        self.detection_mode = self.mode_var.get()

    def start_camera(self):
        if self.running:
            return
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            if self.status_callback:
                self.status_callback("❌ Erreur: Impossible d'ouvrir la caméra")
            return
        self.running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        if self.status_callback:
            self.status_callback("📷 Caméra démarrée")
        self.thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.thread.start()

    def stop_camera(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.camera:
            self.camera.release()
            self.camera = None
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.video_label.config(image="")
        if self.status_callback:
            self.status_callback("📷 Caméra arrêtée")

    def camera_loop(self):
        frame_count = 0
        start_time = time.time()
        while self.running and self.camera:
            ret, frame = self.camera.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.face_count = 0
            self.eye_count = 0
            self.smile_count = 0
            # Détection des visages
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            self.face_count = len(faces)
            for (x, y, w, h) in faces:
                if self.blur_faces.get():
                    face_roi = frame[y:y+h, x:x+w]
                    face_roi = cv2.GaussianBlur(face_roi, (99, 99), 30)
                    frame[y:y+h, x:x+w] = face_roi
                else:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"Face {self.face_count}", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = frame[y:y+h, x:x+w]
                # Détection des yeux
                if self.detection_mode in ("eyes", "all"):
                    eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 5)
                    self.eye_count += len(eyes)
                    for (ex, ey, ew, eh) in eyes:
                        cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (255, 0, 0), 2)
                # Détection des sourires
                if self.detection_mode in ("smiles", "all"):
                    smiles = self.smile_cascade.detectMultiScale(roi_gray, 1.8, 20)
                    self.smile_count += len(smiles)
                    for (sx, sy, sw, sh) in smiles:
                        cv2.rectangle(roi_color, (sx, sy), (sx+sw, sy+sh), (0, 165, 255), 2)
            # Calcul FPS
            frame_count += 1
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            # Mise à jour UI
            self.current_frame = frame.copy()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            self.lbl_faces.config(text=f"👤 Visages: {self.face_count}")
            self.lbl_eyes.config(text=f"👁 Yeux: {self.eye_count}")
            self.lbl_smiles.config(text=f"😊 Sourires: {self.smile_count}")
            self.lbl_fps.config(text=f"FPS: {fps:.1f}")
            if self.save_frames.get() and frame_count % 30 == 0:
                cv2.imwrite(f"capture_{frame_count}.jpg", frame)

    def capture_frame(self):
        if self.current_frame is not None:
            filename = f"capture_manual_{int(time.time())}.jpg"
            cv2.imwrite(filename, self.current_frame)
            if self.status_callback:
                self.status_callback(f"📸 Image sauvegardée: {filename}")

    def cleanup(self):
        self.stop_camera()
