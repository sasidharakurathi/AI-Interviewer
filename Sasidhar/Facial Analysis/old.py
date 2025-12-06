import cv2
import mediapipe as mp
import numpy as np
import time
import math

class AIInterviewer:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.H_RATIO_LEFT = 0.60
        self.H_RATIO_RIGHT = 0.35
        self.V_RATIO_UP = 0.30
        self.V_RATIO_DOWN = 0.70

        self.HEAD_YAW_LEFT = 0.6
        self.HEAD_YAW_RIGHT = 1.8

        self.HEAD_PITCH_UP = 0.9
        self.HEAD_PITCH_DOWN = 1.8

        self.EAR_THRESH = 0.22
        self.blink_count = 0
        self.blink_start = time.time()
        self.is_blinking = False

    def get_ratio(self, point, start, end):
        """
        Calculates how far 'point' is along the line from 'start' to 'end'.
        Returns 0.0 if at start, 1.0 if at end, 0.5 if middle.
        Uses vector projection for accuracy.
        """
        p = np.array([point.x, point.y])
        a = np.array([start.x, start.y])
        b = np.array([end.x, end.y])

        vec_line = b - a
        vec_point = p - a

        line_len_sq = np.dot(vec_line, vec_line)
        if line_len_sq == 0: return 0.5
        
        t = np.dot(vec_point, vec_line) / line_len_sq
        return t

    def get_gaze_label(self, landmarks):
        """
        Detects gaze direction using relative projection.
        Uses RIGHT EYE (Subject's Right) for calculation as it's often more stable.
        """
        inner = landmarks[362]
        outer = landmarks[263]
        top = landmarks[386]
        bottom = landmarks[374]
        iris = landmarks[473]

        h_ratio = self.get_ratio(iris, inner, outer)
        
        v_ratio = self.get_ratio(iris, top, bottom)

        label = "Center"
        if h_ratio > self.H_RATIO_LEFT: label = "Looking RIGHT"
        elif h_ratio < self.H_RATIO_RIGHT: label = "Looking LEFT"
        
        if v_ratio < self.V_RATIO_UP: label = "Looking UP"
        elif v_ratio > self.V_RATIO_DOWN: label = "Looking DOWN"

        return label, h_ratio, v_ratio

    def get_head_label(self, landmarks):
        nose = landmarks[1]
        left_ear = landmarks[234]
        right_ear = landmarks[454]
        forehead = landmarks[10]
        chin = landmarks[152]

        dist_left = abs(nose.x - left_ear.x)
        dist_right = abs(nose.x - right_ear.x)
        yaw_ratio = dist_left / (dist_right + 1e-6)

        dist_top = abs(nose.y - forehead.y)
        dist_bottom = abs(nose.y - chin.y)
        pitch_ratio = dist_top / (dist_bottom + 1e-6)

        label = "Forward"
        if yaw_ratio < self.HEAD_YAW_LEFT: label = "Head LEFT"
        elif yaw_ratio > self.HEAD_YAW_RIGHT: label = "Head RIGHT"
        elif pitch_ratio < self.HEAD_PITCH_UP: label = "Head UP"
        elif pitch_ratio > self.HEAD_PITCH_DOWN: label = "Head DOWN"

        return label, yaw_ratio, pitch_ratio

    def get_blink_rate(self, landmarks):
        l_top = landmarks[159]; l_bot = landmarks[145]
        l_in = landmarks[33]; l_out = landmarks[133]
        l_dist_v = math.hypot(l_top.x - l_bot.x, l_top.y - l_bot.y)
        l_dist_h = math.hypot(l_in.x - l_out.x, l_in.y - l_out.y)
        
        r_top = landmarks[386]; r_bot = landmarks[374]
        r_in = landmarks[362]; r_out = landmarks[263]
        r_dist_v = math.hypot(r_top.x - r_bot.x, r_top.y - r_bot.y)
        r_dist_h = math.hypot(r_in.x - r_out.x, r_in.y - r_out.y)

        ear = ((l_dist_v / (l_dist_h+1e-6)) + (r_dist_v / (r_dist_h+1e-6))) / 2.0

        if ear < self.EAR_THRESH:
            if not self.is_blinking:
                self.blink_count += 1
                self.is_blinking = True
        else:
            self.is_blinking = False

        elapsed = time.time() - self.blink_start
        bpm = int((self.blink_count / elapsed) * 60) if elapsed > 1 else 0
        if elapsed > 60:
            self.blink_start = time.time()
            self.blink_count = 0
        
        return bpm, ear

    def run(self):
        cap = cv2.VideoCapture(0)
        print("--- DEBUG MODE STARTED ---")
        print("Look at these numbers to calibrate:")
        print("GAZE: < 0.35 (Right), > 0.75 (Left) | < 0.30 (Up), > 0.70 (Down)")
        print("HEAD: < 0.60 (Left), > 1.80 (Right) | < 1.10 (Up), > 2.00 (Down)")

        while True:
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb)
            h, w, _ = frame.shape

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    lm = face_landmarks.landmark

                    gaze, h_ratio, v_ratio = self.get_gaze_label(lm)
                    head, yaw, pitch = self.get_head_label(lm)
                    bpm, ear = self.get_blink_rate(lm)

                    cv2.rectangle(frame, (10, 10), (300, 200), (40, 40, 40), -1)
                    cv2.rectangle(frame, (10, 10), (300, 200), (255, 255, 255), 2)

                    font = cv2.FONT_HERSHEY_SIMPLEX
                    
                    c_gaze = (0, 0, 255) if "Looking" in gaze else (0, 255, 0)
                    c_head = (0, 0, 255) if "Head" in head else (0, 255, 0)

                    cv2.putText(frame, f"GAZE: {gaze}", (20, 40), font, 0.7, c_gaze, 2)
                    cv2.putText(frame, f"HEAD: {head}", (20, 80), font, 0.7, c_head, 2)
                    cv2.putText(frame, f"Blink Rate: {bpm} BPM", (20, 120), font, 0.7, (200, 200, 200), 2)

                    cv2.putText(frame, f"H:{h_ratio:.2f} V:{v_ratio:.2f}", (20, 160), font, 0.5, (0, 255, 255), 1)
                    cv2.putText(frame, f"Y:{yaw:.2f} P:{pitch:.2f}", (150, 160), font, 0.5, (0, 255, 255), 1)

                    iris_x = int(lm[473].x * w)
                    iris_y = int(lm[473].y * h)
                    cv2.circle(frame, (iris_x, iris_y), 4, (0, 255, 255), -1)

            cv2.imshow('Calibrated AI Interviewer', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = AIInterviewer()
    app.run()