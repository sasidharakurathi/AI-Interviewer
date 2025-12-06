import cv2
import mediapipe as mp
import math
import numpy as np
import time

class EmotionAndConfidenceDetection:
    def __init__(self):
        # mediapipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # setup drawing utils
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # thresholds (configurations)
        
        # GAZE (Horizontal Ratio): 0.0 = Left, 1.0 = Right
        self.THRESH_LOOK_LEFT = 0.45   # < 0.45 is Left
        self.THRESH_LOOK_RIGHT = 0.66  # > 0.66 is Right
        
        # HEAD PITCH (Vertical Ratio: Forehead / Chin)
        self.THRESH_HEAD_DOWN = 1.35   # > 1.35 is Head Down
        self.THRESH_HEAD_UP = 0.83     # < 0.83 is Head Up

        # HEAD YAW (Horizontal Ratio: Left Cheek / Right Cheek)
        self.THRESH_HEAD_LEFT = 0.60   # < 0.60 is Head Left
        self.THRESH_HEAD_RIGHT = 1.80  # > 1.80 is Head Right

    # calculate euclidean distance between two points
    def calculate_distance(self, p1, p2):
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def get_ratio(self, point, start, end):
        p = np.array([point.x, point.y])
        a = np.array([start.x, start.y])
        b = np.array([end.x, end.y])
        
        vec_line = b - a
        vec_point = p - a
        line_len_sq = np.dot(vec_line, vec_line)
        
        if line_len_sq == 0: 
            return 0.5
        
        t = np.dot(vec_point, vec_line) / line_len_sq
        
        return t
    
    def get_eye_aspect_ratio(self, landmarks, eye_indices):
        # indices: [Top, Bottom, Left, Right]
        
        vertical_dist = self.calculate_distance(landmarks[eye_indices[0]], landmarks[eye_indices[1]])
        horizontal_dist = self.calculate_distance(landmarks[eye_indices[2]], landmarks[eye_indices[3]])
        
        if horizontal_dist == 0: 
            return 0.0
        
        return vertical_dist / horizontal_dist

    def get_gaze_label(self, landmarks):
        """Detects Horizontal Gaze Direction."""
        
        inner = landmarks[362]
        outer = landmarks[263]
        iris = landmarks[473]
        h_ratio = self.get_ratio(iris, inner, outer)
        
        gaze_h = "Center"
        if h_ratio < self.THRESH_LOOK_LEFT: 
            gaze_h = "Looking LEFT"
        
        elif h_ratio > self.THRESH_LOOK_RIGHT: 
            gaze_h = "Looking RIGHT"
            
        return gaze_h, h_ratio

    def get_head_pose(self, landmarks):
        """Detects Head Orientation."""
        
        nose = landmarks[1]
        forehead = landmarks[10]
        chin = landmarks[152]
        left_ear = landmarks[234] 
        right_ear = landmarks[454]

        # Pitch
        forehead_dist = nose.y - forehead.y
        chin_dist = chin.y - nose.y
        pitch_ratio = forehead_dist / (chin_dist + 1e-6)

        # Yaw
        left_dist = abs(nose.x - left_ear.x)
        right_dist = abs(nose.x - right_ear.x)
        yaw_ratio = left_dist / (right_dist + 1e-6)

        # Logic
        pose = "Forward"
        if pitch_ratio > self.THRESH_HEAD_DOWN: 
            pose = "Head DOWN"
        
        elif pitch_ratio < self.THRESH_HEAD_UP: 
            pose = "Head UP"
            
        elif yaw_ratio < self.THRESH_HEAD_LEFT: 
            pose = "Head LEFT"
            
        elif yaw_ratio > self.THRESH_HEAD_RIGHT: 
            pose = "Head RIGHT"

        return pose, pitch_ratio, yaw_ratio

    def analyze_emotion(self, landmarks):
        """
        Detects Smile, Surprise, or Neutral based on geometry.
        """
        
        # MOUTH ASPECT RATIO (MAR)
        # Vertical: 13 (Upper), 14 (Lower) and Horizontal: 61 (Left), 291 (Right)
        mouth_vertical = self.calculate_distance(landmarks[13], landmarks[14])
        mouth_horizontal = self.calculate_distance(landmarks[61], landmarks[291])
        
        mar = 0.0
        if mouth_horizontal > 0:
            mar = mouth_vertical / mouth_horizontal

        # EYE ASPECT RATIO (EAR)
        # Left Eye: 159 (Top), 145 (Bottom), 33 (Inner), 133 (Outer)
        left_ear = self.get_eye_aspect_ratio(landmarks, [159, 145, 33, 133])
        
        # Right Eye: 386 (Top), 374 (Bottom), 362 (Inner), 263 (Outer)
        right_ear = self.get_eye_aspect_ratio(landmarks, [386, 374, 362, 263])
        
        avg_ear = (left_ear + right_ear) / 2.0

        # SMILE RATIO
        # Normalized by jaw width to be scale-invariant
        jaw_width = self.calculate_distance(landmarks[234], landmarks[454])
        normalized_mouth_width = 0.0
        
        if jaw_width > 0:
            normalized_mouth_width = mouth_horizontal / jaw_width

        # LOGIC & THRESHOLDS
        # SURPRISE: Eyes wide open (High EAR) AND Mouth open (High MAR)
        if avg_ear > 0.37 and mar > 0.45: 
            return "Surprise"
        
        # HAPPY: Wide mouth (Smile)
        if normalized_mouth_width > 0.38: 
            return "Happy"

        # NEUTRAL: Everything else
        return "Neutral"

    def run(self):
        cap = cv2.VideoCapture(0)
        print("--------------------------- TEST STARTED ---------------------------")

        while True:
            ret, frame = cap.read()
            if not ret: break

            # Flipping webcam (to accuratly calculate the left and right directions)
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb)

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    lm = face_landmarks.landmark

                    # Draw Mesh
                    self.mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                    )
                    self.mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                    )

                    # Calculate Analytics
                    gaze_label, h_ratio = self.get_gaze_label(lm)
                    head_label, pitch, yaw = self.get_head_pose(lm)
                    emotion_label = self.analyze_emotion(lm)

                    # Display Results
                    cv2.rectangle(frame, (10, 10), (350, 150), (30, 30, 30), -1)
                    cv2.rectangle(frame, (10, 10), (350, 150), (255, 255, 255), 2)

                    font = cv2.FONT_HERSHEY_SIMPLEX
                    c_gaze = (0, 0, 255) if "Looking" in gaze_label else (0, 255, 0)
                    c_head = (0, 0, 255) if "Head" in head_label else (0, 255, 0)
                    
                    # Emotion Color
                    c_emo = (0, 255, 0)
                    
                    if emotion_label == "Happy": 
                        c_emo = (0, 255, 255)
                        
                    elif emotion_label == "Surprise": 
                        c_emo = (255, 0, 255)

                    cv2.putText(frame, f"Look: {gaze_label}", (20, 50), font, 0.8, c_gaze, 2)
                    cv2.putText(frame, f"Head: {head_label}", (20, 90), font, 0.8, c_head, 2)
                    cv2.putText(frame, f"Mood: {emotion_label}", (20, 130), font, 0.8, c_emo, 2)

                    # Debugging Gaze, Pitch, Yaw Values
                    cv2.putText(frame, f"Gaze: {h_ratio:.2f} | Pitch: {pitch:.2f} | Yaw: {yaw:.2f}", (20, 175), font, 0.5, (255, 2, 2), 1)

            cv2.imshow('Testing Emotion and Confidence Detection', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = EmotionAndConfidenceDetection()
    app.run()