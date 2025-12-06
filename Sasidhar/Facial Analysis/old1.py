import cv2
import mediapipe as mp
import math
import numpy as np

class FastEmotionDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def calculate_distance(self, p1, p2):
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def get_eye_aspect_ratio(self, landmarks, eye_indices):
        vertical_dist = self.calculate_distance(landmarks[eye_indices[0]], landmarks[eye_indices[1]])
        horizontal_dist = self.calculate_distance(landmarks[eye_indices[2]], landmarks[eye_indices[3]])

        if horizontal_dist == 0: return 0.0
        return vertical_dist / horizontal_dist

    def analyze_geometry(self, landmarks):
        mouth_vertical = self.calculate_distance(landmarks[13], landmarks[14])
        mouth_horizontal = self.calculate_distance(landmarks[61], landmarks[291])
        
        mar = 0.0
        if mouth_horizontal > 0:
            mar = mouth_vertical / mouth_horizontal

        left_ear = self.get_eye_aspect_ratio(landmarks, [159, 145, 33, 133])
        right_ear = self.get_eye_aspect_ratio(landmarks, [386, 374, 362, 263])
        
        avg_ear = (left_ear + right_ear) / 2.0

        jaw_width = self.calculate_distance(landmarks[234], landmarks[454])
        normalized_mouth_width = 0.0
        if jaw_width > 0:
            normalized_mouth_width = mouth_horizontal / jaw_width

        print(f"EAR: {avg_ear:.3f} (Wide > 0.4) | MAR: {mar:.3f} (Open > 0.4) | Smile: {normalized_mouth_width:.3f}")

        if avg_ear > 0.37 and mar > 0.45: 
            return "Surprise"
        
        if normalized_mouth_width > 0.38: 
            return "Happy"

        return "Neutral"

    def run(self):
        cap = cv2.VideoCapture(0)
        print("Starting Scale-Invariant Emotion Detector...")
        print("Look at the terminal for 'EAR', 'MAR', and 'Smile' values to debug.")

        while True:
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            height, width, _ = frame.shape

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    mp.solutions.drawing_utils.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_tesselation_style()
                    )

                    emotion = self.analyze_geometry(face_landmarks.landmark)
                    
                    x = int(face_landmarks.landmark[10].x * width)
                    y = int(face_landmarks.landmark[10].y * height)

                    color = (0, 255, 0)
                    if emotion == "Happy": color = (0, 255, 255)
                    if emotion == "Surprise": color = (255, 0, 255)

                    cv2.putText(frame, emotion, (x - 50, y - 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            cv2.imshow('Pure MediaPipe Detector', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = FastEmotionDetector()
    app.run()